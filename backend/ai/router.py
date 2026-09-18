from __future__ import annotations

import asyncio
import json
import logging

from backend.ai.base import AIProvider
from backend.ai.config import AISettings, ai_settings
from backend.ai.exceptions import (
    AIConcurrencyLimit,
    AIInputTooLarge,
    AllProvidersUnavailable,
    ProviderError,
)
from backend.ai.providers import (
    GroqProvider,
    OllamaProvider,
    OpenRouterProvider,
)
from backend.ai.schemas import (
    EmbeddingResult,
    GenerationRequest,
    GenerationResult,
    ProviderHealth,
)
from backend.ai.utils.retry import retry_async

logger = logging.getLogger("omnipool.ai")


class AIRouter:
    def __init__(
        self,
        settings: AISettings = ai_settings,
        providers: list[AIProvider] | None = None,
    ) -> None:
        self.settings = settings
        self._providers = providers or [
            OllamaProvider(settings),
            GroqProvider(settings),
            OpenRouterProvider(settings),
        ]
        self._semaphore = asyncio.Semaphore(
            settings.max_concurrency
        )

    def _ordered_providers(self) -> list[AIProvider]:
        enabled = [
            provider
            for provider in self._providers
            if provider.configured()
        ]
        priority = {"ollama": 0, "groq": 1, "openrouter": 2}
        enabled.sort(
            key=lambda provider: (
                provider.name != self.settings.primary_provider,
                priority.get(provider.name, 99),
            )
        )
        return enabled

    def _validate_request(
        self, request: GenerationRequest
    ) -> GenerationRequest:
        total_chars = len(request.prompt) + len(request.system)
        if total_chars > self.settings.max_input_chars:
            raise AIInputTooLarge(
                f"input_exceeds_{self.settings.max_input_chars}_characters"
            )
        if request.max_tokens > self.settings.max_output_tokens:
            return request.model_copy(
                update={
                    "max_tokens": self.settings.max_output_tokens
                }
            )
        return request

    async def health(self) -> list[ProviderHealth]:
        return [
            await provider.health_check()
            for provider in self._providers
            if provider.configured() or provider.name == "ollama"
        ]

    async def generate(
        self, request: GenerationRequest
    ) -> GenerationResult:
        request = self._validate_request(request)

        try:
            await asyncio.wait_for(
                self._semaphore.acquire(),
                timeout=self.settings.queue_timeout_seconds,
            )
        except TimeoutError as exc:
            raise AIConcurrencyLimit("ai_queue_timeout") from exc

        failures: list[str] = []
        try:
            for fallback_index, provider in enumerate(
                self._ordered_providers()
            ):
                health = await provider.health_check()
                if not health.available:
                    failures.append(
                        f"{provider.name}:{health.detail}"
                    )
                    continue

                async def call(
                    active_provider: AIProvider = provider,
                ) -> GenerationResult:
                    return await asyncio.wait_for(
                        active_provider.generate(request),
                        timeout=self.settings.timeout_seconds,
                    )

                try:
                    result = await retry_async(
                        call,
                        retries=self.settings.max_retries,
                    )
                except TimeoutError:
                    failures.append(f"{provider.name}:timeout")
                    continue
                except ProviderError as exc:
                    failures.append(
                        f"{provider.name}:{exc.__class__.__name__}"
                    )
                    continue

                result.fallback_index = fallback_index
                logger.info(
                    json.dumps(
                        {
                            "event": "ai_generation",
                            "provider": result.provider,
                            "model": result.model,
                            "latency_ms": result.latency_ms,
                            "fallback_index": fallback_index,
                            "input_tokens_estimate": (
                                result.input_tokens_estimate
                            ),
                            "output_tokens_estimate": (
                                result.output_tokens_estimate
                            ),
                        },
                        separators=(",", ":"),
                    )
                )
                return result
        finally:
            self._semaphore.release()

        logger.warning(
            json.dumps(
                {
                    "event": "ai_generation_failed",
                    "failures": failures[:8],
                },
                separators=(",", ":"),
            )
        )
        raise AllProvidersUnavailable(
            "no_free_ai_provider_available"
        )

    async def embed(
        self, texts: list[str]
    ) -> EmbeddingResult:
        if sum(len(text) for text in texts) > self.settings.max_input_chars:
            raise AIInputTooLarge("embedding_input_too_large")

        for provider in self._ordered_providers():
            try:
                return await provider.embed(texts)
            except ProviderError:
                continue

        raise AllProvidersUnavailable(
            "no_local_embedding_provider_available"
        )


ai_router = AIRouter()
