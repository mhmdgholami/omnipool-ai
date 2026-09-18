from __future__ import annotations

import asyncio
import hashlib
import json
import math
import time

from backend.config import settings
from backend.db import db
from backend.models import TrendFeatures, TrendObservation
from backend.quant.clustering import cluster_observations
from backend.quant.risk import risk_flags, risk_score, trend_confidence
from backend.quant.scoring import (
    clamp,
    compute_trend_score,
    freshness_score,
    opportunity_score,
)
from backend.quant.text import memeability_heuristic
from backend.services.dexscreener import dex_adapter

_SEEDS = (
    (
        "Robot Boxing",
        "Humanoid fighting clips moving from robotics circles into meme culture.",
        18.0,
    ),
    (
        "Tiny Mic Interviews",
        "Tiny microphone interviews mutating into a reusable reaction format.",
        14.0,
    ),
    (
        "AI Pigeon",
        "An AI-agent pigeon joke spreading through profile pictures and replies.",
        16.0,
    ),
)


def _trend_id(tokens: frozenset[str]) -> str:
    fingerprint = "|".join(sorted(tokens))
    return hashlib.blake2s(fingerprint.encode(), digest_size=10).hexdigest()


def _seed_observations(timestamp: float) -> list[TrendObservation]:
    if not settings.enable_demo_seeds:
        return []

    return [
        TrendObservation(
            source="curated_demo",
            external_id=f"seed:{index}",
            title=title,
            text=summary,
            url="",
            author="",
            created_at=timestamp - index * 180,
            engagement=engagement,
        )
        for index, (title, summary, engagement) in enumerate(_SEEDS)
    ]


async def _collect_observations() -> list[TrendObservation]:
    now = time.time()
    observations = _seed_observations(now)
    dex_signals = await dex_adapter.scan()

    for rank, signal in enumerate(dex_signals):
        observations.append(
            TrendObservation(
                source="dexscreener",
                external_id=signal["external_id"],
                title=signal["title"],
                text=signal["summary"],
                url=signal["url"],
                author="",
                created_at=now,
                engagement=max(1.0, 32.0 - rank),
            )
        )

    return observations[: settings.max_observations_per_scan]


def _cluster_to_trend(cluster, timestamp: float) -> dict:
    representative = max(
        cluster.observations,
        key=lambda observation: (
            observation.engagement,
            observation.created_at,
        ),
    )
    source_count = len(cluster.sources)
    evidence_count = len(cluster.observations)
    latest = max(
        observation.created_at
        for observation in cluster.observations
    )
    age_minutes = max(0.0, (timestamp - latest) / 60.0)

    velocity = clamp(
        36.0
        + min(42.0, math.log1p(cluster.engagement) * 8.0)
        + min(18.0, evidence_count * 2.5)
    )
    acceleration = clamp(42.0 + velocity * 0.45)
    cross_source = clamp(
        18.0
        + source_count * 28.0
        + min(22.0, max(0, evidence_count - 1) * 5.0)
    )
    novelty = clamp(93.0 - max(0, evidence_count - 1) * 4.0)
    dex_evidence = sum(
        observation.source == "dexscreener"
        for observation in cluster.observations
    )
    saturation = clamp(8.0 + dex_evidence * 10.0)
    memeability = sum(
        memeability_heuristic(
            observation.title,
            observation.text,
        )
        for observation in cluster.observations
    ) / evidence_count
    freshness = freshness_score(age_minutes)

    features = TrendFeatures(
        velocity=velocity,
        acceleration=acceleration,
        cross_source=cross_source,
        novelty=novelty,
        saturation=saturation,
        memeability=memeability,
        freshness=freshness,
    )
    base_score = compute_trend_score(features)
    confidence = trend_confidence(
        source_count=source_count,
        evidence_count=evidence_count,
        cross_source=cross_source,
        freshness=freshness,
    )
    flags = risk_flags(
        representative.title,
        representative.text,
        saturation=saturation,
        confidence=confidence,
        source_count=source_count,
    )
    launch_risk = risk_score(
        flags,
        saturation=saturation,
        confidence=confidence,
    )

    return {
        "id": _trend_id(cluster.token_set),
        "title": representative.title,
        "summary": representative.text,
        "source": ",".join(sorted(cluster.sources)),
        "score": opportunity_score(
            base_score,
            confidence,
            launch_risk,
        ),
        "confidence": confidence,
        "risk": launch_risk,
        "velocity": velocity,
        "acceleration": acceleration,
        "cross_source": cross_source,
        "novelty": novelty,
        "saturation": saturation,
        "memeability": memeability,
        "freshness": freshness,
        "evidence_count": evidence_count,
        "source_count": source_count,
        "risk_flags": flags,
        "created_at": min(
            observation.created_at
            for observation in cluster.observations
        ),
        "updated_at": timestamp,
    }


def _score_and_persist(
    observations: list[TrendObservation],
    timestamp: float,
) -> list[dict]:
    clusters = cluster_observations(
        observations,
        max_clusters=min(settings.max_trends, 60),
        max_observations=settings.max_observations_per_scan,
    )

    for cluster in clusters:
        db.upsert_trend(_cluster_to_trend(cluster, timestamp))

    return list_trends(30)


async def scan_trends() -> list[dict]:
    timestamp = time.time()
    observations = await _collect_observations()

    # SQLite and clustering are bounded, but both are synchronous. Running
    # them off-loop prevents disk latency or a full scan from stalling other
    # async HTTP requests.
    return await asyncio.to_thread(
        _score_and_persist,
        observations,
        timestamp,
    )


def list_trends(limit: int = 30) -> list[dict]:
    rows = db.rows(
        """
        SELECT *
        FROM trends
        ORDER BY score DESC, confidence DESC, updated_at DESC
        LIMIT ?
        """,
        (min(max(int(limit), 1), settings.max_trends),),
    )
    for row in rows:
        raw_flags = row.get("risk_flags", "[]")
        if isinstance(raw_flags, str):
            try:
                row["risk_flags"] = json.loads(raw_flags)
            except json.JSONDecodeError:
                row["risk_flags"] = []
    return rows
