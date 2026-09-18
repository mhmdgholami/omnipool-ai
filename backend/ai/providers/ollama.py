from __future__ import annotations

import time
from typing import Any

from backend.ai.base import AIProvider
from backend.ai.config import AISettings, ai_settings
from backend.ai.exceptions import (
    ProviderResponseError,
    ProviderUnavailable,
)
from backend.ai.providers._compat import translate_http_error
from backend.ai.schemas import (
    EmbeddingResult,
    GenerationRequest,
    GenerationResult,
    ProviderHealth,
)
from backend.ai.utils.health import HealthCache
from backend.ai.utils.tokens import estimate_tokens
from backend.services.http import external_http


class OllamaProvider(AIProvider):
    name = "ollama"

    def __init__(self, settings: AISettings = ai_settings) -> None:
        self.settings = settings
        self._health = HealthCache(settings.health_ttl_seconds)

    def configured(self) -> bool:
        return self.settings.enable_ollama

    async def _models(self) -> list[str]:
        payload = await external_http.request_json(
            "GET",
            f"{self.settings.ollama_base_url}/api/tags",
        )
        models = payload.get("models", [])
        return [
            str(item.get("name"))
            for item in models
            if isinstance(item, dict) and item.get("name")
        ][:64]

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
                    detail="disabled",
                ),
            )

        try:
            models = await self._models()
        except Exception:
            return self._health.set(
                self.name,
                ProviderHealth(
                    provider=self.name,
                    available=False,
                    detail=(
                        "Ollama is not reachable. Start Ollama and "
                        "install at least one local model."
                    ),
                ),
            )

        return self._health.set(
            self.name,
            ProviderHealth(
                provider=self.name,
                available=bool(models),
                detail=(
                    "ready"
                    if models
                    else "Ollama is running but no models are installed."
                ),
                models=models,
            ),
        )

    @staticmethod
    def _select_model(
        preferred: str,
        installed: list[str],
        *,
        allow_any: bool = True,
    ) -> str:
        if preferred in installed:
            return preferred

        preferred_base = preferred.split(":", 1)[0]
        for model in installed:
            if model.split(":", 1)[0] == preferred_base:
                return model

        if installed and allow_any:
            return installed[0]
        if installed:
            raise ProviderUnavailable(
                f"ollama_model_not_installed:{preferred}"
            )
        raise ProviderUnavailable("ollama_no_models_installed")

    async def generate(
        self, request: GenerationRequest
    ) -> GenerationResult:
        health = await self.health_check()
        if not health.available:
            raise ProviderUnavailable(health.detail)

        preferred = (
            request.model
            or self.settings.local_model_for_task(request.task.value)
        )
        model = self._select_model(preferred, health.models)

        messages: list[dict[str, str]] = []
        if request.system:
            messages.append({"role": "system", "content": request.system})
        messages.append({"role": "user", "content": request.prompt})

        body: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "stream": False,
            "keep_alive": "5m",
            "options": {
                "temperature": request.temperature,
                "num_predict": request.max_tokens,
            },
        }
        if request.json_mode:
            body["format"] = "json"

        started = time.perf_counter()
        try:
            payload = await external_http.request_json(
                "POST",
                f"{self.settings.ollama_base_url}/api/chat",
                json_body=body,
                timeout_seconds=self.settings.timeout_seconds,
            )
        except Exception as exc:
            translate_http_error(self.name, exc)

        text = (
            payload.get("message", {}).get("content")
            if isinstance(payload, dict)
            else None
        )
        if not isinstance(text, str) or not text.strip():
            raise ProviderResponseError("ollama_malformed_response")

        return GenerationResult(
            text=text.strip(),
            provider=self.name,
            model=model,
            latency_ms=round(
                (time.perf_counter() - started) * 1000,
                2,
            ),
            input_tokens_estimate=estimate_tokens(
                request.system + request.prompt
            ),
            output_tokens_estimate=estimate_tokens(text),
        )

    async def embed(self, texts: list[str]) -> EmbeddingResult:
        if not texts:
            return EmbeddingResult(
                embeddings=[],
                provider=self.name,
                model=self.settings.embedding_model,
            )

        health = await self.health_check()
        if not health.available:
            raise ProviderUnavailable(health.detail)

        model = self._select_model(
            self.settings.embedding_model,
            health.models,
            allow_any=False,
        )
        try:
            payload = await external_http.request_json(
                "POST",
                f"{self.settings.ollama_base_url}/api/embed",
                json_body={"model": model, "input": texts},
                timeout_seconds=self.settings.timeout_seconds,
            )
        except Exception as exc:
            translate_http_error(self.name, exc)

        embeddings = (
            payload.get("embeddings")
            if isinstance(payload, dict)
            else None
        )
        if not isinstance(embeddings, list):
            raise ProviderResponseError(
                "ollama_malformed_embedding_response"
            )

        return EmbeddingResult(
            embeddings=embeddings,
            provider=self.name,
            model=model,
        )
