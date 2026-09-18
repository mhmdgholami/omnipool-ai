from __future__ import annotations

import time
from typing import Any

import httpx

from backend.ai.exceptions import (
    ProviderRateLimited,
    ProviderResponseError,
    ProviderTimeout,
    ProviderTransientError,
    ProviderUnavailable,
)
from backend.ai.schemas import GenerationRequest, GenerationResult
from backend.ai.utils.tokens import estimate_tokens
from backend.services.http import external_http


def translate_http_error(provider: str, exc: Exception) -> None:
    if isinstance(exc, httpx.TimeoutException):
        raise ProviderTimeout(f"{provider}_timeout") from exc
    if isinstance(exc, httpx.ConnectError):
        raise ProviderUnavailable(f"{provider}_unreachable") from exc
    if isinstance(exc, httpx.HTTPStatusError):
        status = exc.response.status_code
        if status == 429:
            raise ProviderRateLimited(f"{provider}_rate_limited") from exc
        if 500 <= status < 600:
            raise ProviderTransientError(
                f"{provider}_server_error_{status}"
            ) from exc
        raise ProviderResponseError(
            f"{provider}_http_error_{status}"
        ) from exc
    raise ProviderUnavailable(f"{provider}_request_failed") from exc


async def chat_completion(
    *,
    provider: str,
    base_url: str,
    api_key: str,
    model: str,
    request: GenerationRequest,
    extra_headers: dict[str, str] | None = None,
) -> GenerationResult:
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    if extra_headers:
        headers.update(extra_headers)

    messages: list[dict[str, str]] = []
    if request.system:
        messages.append({"role": "system", "content": request.system})
    messages.append({"role": "user", "content": request.prompt})

    body: dict[str, Any] = {
        "model": model,
        "messages": messages,
        "temperature": request.temperature,
        "max_tokens": request.max_tokens,
        "stream": False,
    }
    if request.json_mode:
        body["response_format"] = {"type": "json_object"}

    started = time.perf_counter()
    try:
        payload = await external_http.request_json(
            "POST",
            f"{base_url}/chat/completions",
            headers=headers,
            json_body=body,
        )
    except Exception as exc:
        translate_http_error(provider, exc)
        raise AssertionError("unreachable")

    try:
        text = payload["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise ProviderResponseError(
            f"{provider}_malformed_response"
        ) from exc

    if not isinstance(text, str) or not text.strip():
        raise ProviderResponseError(f"{provider}_empty_response")

    return GenerationResult(
        text=text.strip(),
        provider=provider,
        model=model,
        latency_ms=round((time.perf_counter() - started) * 1000, 2),
        input_tokens_estimate=estimate_tokens(
            request.system + request.prompt
        ),
        output_tokens_estimate=estimate_tokens(text),
    )
