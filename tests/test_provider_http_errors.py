import httpx
import pytest

from backend.ai.exceptions import (
    ProviderRateLimited,
    ProviderResponseError,
    ProviderTransientError,
)
from backend.ai.providers._compat import translate_http_error


def status_error(status: int) -> httpx.HTTPStatusError:
    request = httpx.Request(
        "POST",
        "https://provider.test/chat",
    )
    response = httpx.Response(
        status,
        request=request,
    )
    return httpx.HTTPStatusError(
        "provider error",
        request=request,
        response=response,
    )


def test_http_429_maps_to_rate_limit():
    with pytest.raises(ProviderRateLimited):
        translate_http_error(
            "provider",
            status_error(429),
        )


def test_http_500_maps_to_retryable_transient_error():
    with pytest.raises(ProviderTransientError):
        translate_http_error(
            "provider",
            status_error(500),
        )


def test_non_retryable_http_error_is_not_hidden():
    with pytest.raises(ProviderResponseError):
        translate_http_error(
            "provider",
            status_error(400),
        )
