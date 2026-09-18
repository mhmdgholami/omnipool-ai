from __future__ import annotations

import asyncio
import json
import re
import time
from uuid import uuid4

from pydantic import BaseModel, Field

from backend.ai.exceptions import AIError
from backend.ai.schemas import TaskKind
from backend.ai.services.generation import generate_structured
from backend.db import db


class ConceptDraft(BaseModel):
    name: str = Field(min_length=2, max_length=48)
    ticker: str = Field(min_length=1, max_length=12)
    thesis: str = Field(min_length=12, max_length=500)
    visual_prompt: str = Field(default="", max_length=500)
    target_sol: float = Field(ge=5, le=250)
    novelty_score: float = Field(ge=0, le=100)
    momentum_score: float = Field(ge=0, le=100)
    saturation_score: float = Field(ge=0, le=100)
    risk_flags: list[str] = Field(default_factory=list, max_length=8)


class ConceptBatch(BaseModel):
    concepts: list[ConceptDraft] = Field(
        min_length=3,
        max_length=3,
    )


def _ticker(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9]", "", value).upper()
    return (cleaned or "IDEA")[:8]


def _trend_flags(trend: dict) -> list[str]:
    raw = trend.get("risk_flags", [])
    if isinstance(raw, list):
        return [str(flag)[:80] for flag in raw[:8]]
    if isinstance(raw, str):
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            return []
        if isinstance(parsed, list):
            return [str(flag)[:80] for flag in parsed[:8]]
    return []


def _fallback(
    trend: dict,
    *,
    degraded: bool = False,
) -> list[dict]:
    first_word = trend["title"].split()[0].title()
    names = (
        f"{first_word} Mode",
        f"Proof of {first_word}",
        f"{first_word} Signal",
    )
    inherited_flags = _trend_flags(trend)
    if degraded:
        inherited_flags = [
            *inherited_flags,
            "deterministic_fallback",
        ][:8]

    concepts: list[dict] = []
    for index, name in enumerate(names):
        concepts.append(
            {
                "id": str(uuid4()),
                "trend_id": trend["id"],
                "name": name,
                "ticker": _ticker(name),
                "thesis": (
                    f"A community launch around {trend['title'].lower()} "
                    "that proves demand before a tradable token exists."
                ),
                "visual_prompt": (
                    f"Minimal internet-native symbol for {name}; "
                    "dark background, high contrast, no text."
                ),
                "target_sol": (25, 40, 60)[index],
                "novelty_score": max(
                    50.0,
                    float(trend.get("novelty", 80.0)) - index * 4,
                ),
                "momentum_score": max(
                    50.0,
                    float(trend.get("score", 75.0)) - index * 3,
                ),
                "saturation_score": min(
                    100.0,
                    float(trend.get("saturation", 15.0)) + index * 4,
                ),
                "risk_flags": inherited_flags,
                "created_at": time.time(),
            }
        )
    return concepts


def _materialize(
    trend: dict,
    batch: ConceptBatch,
) -> list[dict]:
    inherited_flags = _trend_flags(trend)
    concepts: list[dict] = []

    for draft in batch.concepts:
        flags = list(
            dict.fromkeys(
                [*inherited_flags, *draft.risk_flags]
            )
        )[:8]
        concepts.append(
            {
                "id": str(uuid4()),
                "trend_id": trend["id"],
                "name": draft.name,
                "ticker": _ticker(draft.ticker or draft.name),
                "thesis": draft.thesis,
                "visual_prompt": draft.visual_prompt,
                "target_sol": float(draft.target_sol),
                "novelty_score": float(draft.novelty_score),
                "momentum_score": float(draft.momentum_score),
                "saturation_score": float(draft.saturation_score),
                "risk_flags": flags,
                "created_at": time.time(),
            }
        )
    return concepts


async def generate_concepts(trend: dict) -> list[dict]:
    flags = _trend_flags(trend)
    if (
        "sensitive_event" in flags
        or float(trend.get("risk", 0.0)) >= 80.0
    ):
        raise ValueError("trend_requires_manual_review")

    prompt = (
        "Create exactly three genuinely different launch concepts for "
        "the trend below. Return a JSON object with a concepts array. "
        "Each concept must contain name, ticker, thesis, visual_prompt, "
        "target_sol, novelty_score, momentum_score, saturation_score "
        "and risk_flags. Do not promise returns. Do not impersonate "
        "a real person, company or official organization. Keep ticker "
        "alphanumeric and at most 8 characters. target_sol must be 5-250.\n\n"
        f"Trend: {trend['title']}\n"
        f"Context: {trend['summary']}\n"
        f"Opportunity: {trend.get('score', 75)}\n"
        f"Confidence: {trend.get('confidence', 50)}\n"
        f"Launch risk: {trend.get('risk', 20)}\n"
        f"Saturation: {trend.get('saturation', 15)}"
    )

    try:
        batch = await generate_structured(
            prompt,
            ConceptBatch,
            task=TaskKind.GENERATION,
            max_tokens=850,
            temperature=0.5,
        )
        concepts = _materialize(trend, batch)
    except AIError:
        concepts = _fallback(trend, degraded=True)

    def persist() -> None:
        for concept in concepts:
            db.insert_concept(concept)

    await asyncio.to_thread(persist)
    return concepts
