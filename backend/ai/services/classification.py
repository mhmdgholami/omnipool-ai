from __future__ import annotations

from pydantic import BaseModel

from backend.ai.router import AIRouter, ai_router
from backend.ai.schemas import TaskKind
from backend.ai.services.generation import generate_structured


class _Classification(BaseModel):
    label: str


async def classify(
    text: str,
    labels: list[str],
    *,
    router: AIRouter = ai_router,
) -> str:
    if not labels:
        raise ValueError("classification_labels_required")

    prompt = (
        "Choose exactly one label from this list: "
        + ", ".join(labels)
        + ". Return an object with one field named label.\n\nText:\n"
        + text
    )
    result = await generate_structured(
        prompt,
        _Classification,
        task=TaskKind.CLASSIFICATION,
        max_tokens=80,
        temperature=0.0,
        router=router,
    )
    if result.label not in labels:
        raise ValueError("classification_returned_unknown_label")
    return result.label
