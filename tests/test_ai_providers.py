import asyncio

import httpx
import pytest

from backend.ai.config import AISettings
from backend.ai.exceptions import ProviderUnavailable
from backend.ai.providers.groq import GroqProvider
from backend.ai.providers.ollama import OllamaProvider
from backend.ai.providers.openrouter import OpenRouterProvider
from backend.ai.schemas import GenerationRequest
from backend.services.http import external_http


def test_missing_hosted_keys_disable_providers():
    config = AISettings(
        groq_api_key="",
        openrouter_api_key="",
    )
    assert GroqProvider(config).configured() is False
    assert OpenRouterProvider(config).configured() is False


def test_openrouter_paid_model_is_blocked_even_if_flag_is_set():
    config = AISettings(
        openrouter_api_key="key",
        openrouter_model="vendor/paid-model",
        allow_paid_providers=True,
    )
    provider = OpenRouterProvider(config)
    assert provider.configured() is False


def test_ollama_unavailable_is_reported_without_crashing(monkeypatch):
    async def fail(*args, **kwargs):
        raise httpx.ConnectError("offline")

    monkeypatch.setattr(external_http, "request_json", fail)
    provider = OllamaProvider(
        AISettings(
            enable_ollama=True,
            ollama_base_url="http://ollama",
        )
    )

    health = asyncio.run(provider.health_check())

    assert health.available is False
    assert "not reachable" in health.detail


def test_ollama_discovers_installed_model(monkeypatch):
    async def fake_request(method, url, **kwargs):
        if url.endswith("/api/tags"):
            return {
                "models": [
                    {"name": "qwen3:1.7b"},
                    {"name": "nomic-embed-text"},
                ]
            }
        if url.endswith("/api/chat"):
            return {"message": {"content": "local response"}}
        raise AssertionError(url)

    monkeypatch.setattr(
        external_http,
        "request_json",
        fake_request,
    )
    provider = OllamaProvider(
        AISettings(
            enable_ollama=True,
            fast_model="qwen3:1.7b",
        )
    )

    result = asyncio.run(
        provider.generate(
            GenerationRequest(
                prompt="hello",
                task="classification",
            )
        )
    )

    assert result.provider == "ollama"
    assert result.model == "qwen3:1.7b"
    assert result.text == "local response"


def test_embedding_never_falls_back_to_non_embedding_model(monkeypatch):
    async def fake_request(method, url, **kwargs):
        if url.endswith("/api/tags"):
            return {"models": [{"name": "qwen3:1.7b"}]}
        raise AssertionError(url)

    monkeypatch.setattr(
        external_http,
        "request_json",
        fake_request,
    )
    provider = OllamaProvider(
        AISettings(
            enable_ollama=True,
            embedding_model="nomic-embed-text",
        )
    )

    with pytest.raises(
        ProviderUnavailable,
        match="ollama_model_not_installed",
    ):
        asyncio.run(provider.embed(["hello"]))


def test_groq_unavailable_is_non_fatal(monkeypatch):
    async def fail(*args, **kwargs):
        raise httpx.ConnectError("offline")

    monkeypatch.setattr(external_http, "request_json", fail)
    provider = GroqProvider(
        AISettings(
            enable_groq=True,
            groq_api_key="test-key",
        )
    )

    health = asyncio.run(provider.health_check())

    assert health.available is False


def test_openrouter_unavailable_is_non_fatal(monkeypatch):
    async def fail(*args, **kwargs):
        raise httpx.ConnectError("offline")

    monkeypatch.setattr(external_http, "request_json", fail)
    provider = OpenRouterProvider(
        AISettings(
            enable_openrouter=True,
            openrouter_api_key="test-key",
            openrouter_model="openrouter/free",
        )
    )

    health = asyncio.run(provider.health_check())

    assert health.available is False


def test_ollama_health_is_ttl_cached(monkeypatch):
    calls = 0

    async def fake_request(method, url, **kwargs):
        nonlocal calls
        calls += 1
        return {"models": [{"name": "qwen3:1.7b"}]}

    monkeypatch.setattr(
        external_http,
        "request_json",
        fake_request,
    )
    provider = OllamaProvider(
        AISettings(
            enable_ollama=True,
            health_ttl_seconds=30,
        )
    )

    first = asyncio.run(provider.health_check())
    second = asyncio.run(provider.health_check())

    assert first.available is True
    assert second.available is True
    assert calls == 1


def test_ollama_generation_falls_back_when_configured_model_is_gone(
    monkeypatch,
):
    async def fake_request(method, url, **kwargs):
        if url.endswith("/api/tags"):
            return {
                "models": [
                    {"name": "available-model:3b"},
                ]
            }
        if url.endswith("/api/chat"):
            assert kwargs["json_body"]["model"] == "available-model:3b"
            return {"message": {"content": "fallback model response"}}
        raise AssertionError(url)

    monkeypatch.setattr(
        external_http,
        "request_json",
        fake_request,
    )
    provider = OllamaProvider(
        AISettings(
            enable_ollama=True,
            general_model="removed-model:4b",
        )
    )

    result = asyncio.run(
        provider.generate(
            GenerationRequest(
                prompt="hello",
                task="generation",
            )
        )
    )

    assert result.model == "available-model:3b"
    assert result.text == "fallback model response"
