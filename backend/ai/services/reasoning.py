from __future__ import annotations

from backend.ai.router import AIRouter, ai_router
from backend.ai.schemas import GenerationResult, TaskKind
from backend.ai.services.generation import generate_text


async def reason(
    prompt: str,
    *,
    system: str = "",
    router: AIRouter = ai_router,
) -> GenerationResult:
    return await generate_text(
        prompt,
        system=system,
        task=TaskKind.REASONING,
        max_tokens=900,
        temperature=0.3,
        router=router,
    )
