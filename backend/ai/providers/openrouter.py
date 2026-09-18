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


def is_free_model(model: str) -> bool:
    return model == "openrouter/free" or model.endswith(":free")


class OpenRouterProvider(AIProvider):
    name = "openrouter"

    def __init__(self, settings: AISettings = ai_settings) -> None:
        self.settings = settings
        self._health = HealthCache(settings.health_ttl_seconds)

    def configured(self) -> bool:
        if not (
            self.settings.enable_openrouter
            and self.settings.openrouter_api_key
        ):
            return False
        return is_free_model(self.settings.openrouter_model)

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
                    detail=(
                        "not configured or model is not explicitly free"
                    ),
                ),
            )

        try:
            payload = await external_http.request_json(
                "GET",
                f"{self.settings.openrouter_base_url}/models",
                headers={
                    "Authorization": (
                        f"Bearer {self.settings.openrouter_api_key}"
                    )
                },
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
        model = request.model or self.settings.openrouter_model

        if not is_free_model(model):
            raise ProviderUnavailable(
                "openrouter_paid_model_blocked_by_policy"
            )
        if not self.configured():
            raise ProviderUnavailable("openrouter_not_configured")

        return await chat_completion(
            provider=self.name,
            base_url=self.settings.openrouter_base_url,
            api_key=self.settings.openrouter_api_key,
            model=model,
            request=request,
            extra_headers={"X-Title": "OMNIPOOL AI"},
        )
