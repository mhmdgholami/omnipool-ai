import asyncio

import pytest

from backend.ai.base import AIProvider
from backend.ai.config import AISettings
from backend.ai.exceptions import (
    AllProvidersUnavailable,
    ProviderRateLimited,
    ProviderTransientError,
    ProviderUnavailable,
)
from backend.ai.router import AIRouter
from backend.ai.schemas import (
    GenerationRequest,
    GenerationResult,
    ProviderHealth,
)


class FakeProvider(AIProvider):
    def __init__(
        self,
        name: str,
        *,
        text: str = "ok",
        error: Exception | None = None,
        delay: float = 0.0,
    ) -> None:
        self.name = name
        self.text = text
        self.error = error
        self.delay = delay
        self.calls = 0

    def configured(self) -> bool:
        return True

    async def health_check(self) -> ProviderHealth:
        return ProviderHealth(
            provider=self.name,
            available=True,
            detail="ready",
        )

    async def generate(
        self,
        request: GenerationRequest,
    ) -> GenerationResult:
        self.calls += 1
        if self.delay:
            await asyncio.sleep(self.delay)
        if self.error:
            raise self.error
        return GenerationResult(
            text=self.text,
            provider=self.name,
            model="fake",
            latency_ms=1.0,
            input_tokens_estimate=1,
            output_tokens_estimate=1,
        )


def settings(**overrides) -> AISettings:
    values = {
        "primary_provider": "first",
        "max_retries": 0,
        "timeout_seconds": 0.05,
        "queue_timeout_seconds": 0.1,
        "max_concurrency": 1,
    }
    values.update(overrides)
    return AISettings(**values)


def test_rate_limit_falls_back_to_next_provider():
    first = FakeProvider(
        "first",
        error=ProviderRateLimited("limited"),
    )
    second = FakeProvider("second", text="fallback worked")
    router = AIRouter(settings(), [first, second])

    result = asyncio.run(
        router.generate(GenerationRequest(prompt="hello"))
    )

    assert result.provider == "second"
    assert result.text == "fallback worked"
    assert result.fallback_index == 1


def test_timeout_falls_back_to_next_provider():
    first = FakeProvider("first", delay=0.05)
    second = FakeProvider("second", text="fast")
    router = AIRouter(
        settings(timeout_seconds=0.005),
        [first, second],
    )

    result = asyncio.run(
        router.generate(GenerationRequest(prompt="hello"))
    )

    assert result.provider == "second"


def test_two_provider_failures_are_stable():
    providers = [
        FakeProvider("first", error=ProviderUnavailable("offline")),
        FakeProvider("second", error=ProviderRateLimited("limited")),
    ]
    router = AIRouter(settings(), providers)

    with pytest.raises(
        AllProvidersUnavailable,
        match="no_free_ai_provider_available",
    ):
        asyncio.run(
            router.generate(GenerationRequest(prompt="hello"))
        )


def test_no_configured_provider_returns_controlled_error():
    class DisabledProvider(FakeProvider):
        def configured(self) -> bool:
            return False

    router = AIRouter(
        settings(),
        [DisabledProvider("first")],
    )

    with pytest.raises(AllProvidersUnavailable):
        asyncio.run(
            router.generate(GenerationRequest(prompt="hello"))
        )


def test_server_error_falls_back_to_next_provider():
    first = FakeProvider(
        "first",
        error=ProviderTransientError("server_error"),
    )
    second = FakeProvider("second", text="recovered")
    router = AIRouter(settings(), [first, second])

    result = asyncio.run(
        router.generate(GenerationRequest(prompt="hello"))
    )

    assert result.provider == "second"
    assert result.text == "recovered"
