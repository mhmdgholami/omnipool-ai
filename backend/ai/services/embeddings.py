from __future__ import annotations

from backend.ai.router import AIRouter, ai_router
from backend.ai.schemas import EmbeddingResult


async def embed_texts(
    texts: list[str],
    *,
    router: AIRouter = ai_router,
) -> EmbeddingResult:
    return await router.embed(texts)
