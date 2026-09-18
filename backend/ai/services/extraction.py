from __future__ import annotations

from typing import TypeVar

from pydantic import BaseModel

from backend.ai.router import AIRouter, ai_router
from backend.ai.schemas import TaskKind
from backend.ai.services.generation import generate_structured

T = TypeVar("T", bound=BaseModel)


async def extract(
    text: str,
    schema: type[T],
    *,
    instructions: str = "",
    router: AIRouter = ai_router,
) -> T:
    prompt = (
        "Extract only information supported by the supplied text. "
        "Return JSON only."
    )
    if instructions:
        prompt += "\nInstructions: " + instructions
    prompt += "\n\nText:\n" + text

    return await generate_structured(
        prompt,
        schema,
        task=TaskKind.EXTRACTION,
        router=router,
    )
