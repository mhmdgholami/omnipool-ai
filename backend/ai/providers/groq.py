from __future__ import annotations

from backend.ai.base import AIProvider
from backend.ai.config import AISettings, ai_settings
from backend.ai.exceptions import ProviderUnavailable
from backend.ai.providers._compat import chat_completion
from backend.ai.schemas import (
    GenerationRequest,
    GenerationResult,
    ProviderHealth,
)
from backend.ai.utils.health import HealthCache
from backend.services.http import external_http


class GroqProvider(AIProvider):
    name = "groq"

    def __init__(self, settings: AISettings = ai_settings) -> None:
        self.settings = settings
        self._health = HealthCache(settings.health_ttl_seconds)

    def configured(self) -> bool:
        return bool(
            self.settings.enable_groq
            and self.settings.groq_api_key
        )

    async def health_check(self) -> ProviderHealth:
        cached = self._health.get(self.name)
        if cached is not None:
            return cached
        if not self.configured():
            return self._health.set(
                self.name,
                ProviderHealth(
                    provider=self.name,
                    available=False,
                    detail="not configured",
                ),
            )

        try:
            payload = await external_http.request_json(
                "GET",
                f"{self.settings.groq_base_url}/models",
                headers={
                    "Authorization": (
                        f"Bearer {self.settings.groq_api_key}"
                    )
                },
                timeout_seconds=self.settings.health_timeout_seconds,
            )
            models = [
                str(item.get("id"))
                for item in payload.get("data", [])
                if isinstance(item, dict) and item.get("id")
            ][:64]
        except Exception:
            return self._health.set(
                self.name,
                ProviderHealth(
                    provider=self.name,
                    available=False,
                    detail="unreachable or rate limited",
                ),
            )

        return self._health.set(
            self.name,
            ProviderHealth(
                provider=self.name,
                available=True,
                detail="ready",
                models=models,
            ),
        )

    async def generate(
        self, request: GenerationRequest
    ) -> GenerationResult:
        if not self.configured():
            raise ProviderUnavailable("groq_not_configured")

        return await chat_completion(
            provider=self.name,
            base_url=self.settings.groq_base_url,
            api_key=self.settings.groq_api_key,
            model=request.model or self.settings.groq_model,
            request=request,
        )
