from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator

from backend.ai.exceptions import ProviderCapabilityError
from backend.ai.schemas import (
    EmbeddingResult,
    GenerationRequest,
    GenerationResult,
    ProviderHealth,
)


class AIProvider(ABC):
    name: str

    @abstractmethod
    def configured(self) -> bool:
        raise NotImplementedError

    @abstractmethod
    async def generate(
        self, request: GenerationRequest
    ) -> GenerationResult:
        raise NotImplementedError

    async def stream(
        self, request: GenerationRequest
    ) -> AsyncIterator[str]:
        result = await self.generate(request)
        yield result.text

    @abstractmethod
    async def health_check(self) -> ProviderHealth:
        raise NotImplementedError

    async def embed(self, texts: list[str]) -> EmbeddingResult:
        raise ProviderCapabilityError(
            f"{self.name}_embeddings_not_supported"
        )
