import asyncio
import json

import httpx
import pytest

from backend.services.http import (
    ExternalHttpClient,
    ExternalResponseTooLarge,
)


def run(coro):
    return asyncio.run(coro)


def test_outbound_json_response_is_size_bounded():
    def handler(request):
        body = json.dumps({"payload": "x" * 500}).encode()
        return httpx.Response(
            200,
            content=body,
            request=request,
        )

    client = ExternalHttpClient()
    client._client = httpx.AsyncClient(
        transport=httpx.MockTransport(handler)
    )

    with pytest.raises(
        ExternalResponseTooLarge,
        match="external_response_too_large",
    ):
        run(
            client.request_json(
                "GET",
                "https://example.test/data",
                max_response_bytes=64,
            )
        )

    run(client.close())


def test_outbound_json_parses_under_limit():
    def handler(request):
        return httpx.Response(
            200,
            json={"ok": True},
            request=request,
        )

    client = ExternalHttpClient()
    client._client = httpx.AsyncClient(
        transport=httpx.MockTransport(handler)
    )

    result = run(
        client.request_json(
            "GET",
            "https://example.test/data",
            max_response_bytes=1024,
        )
    )

    assert result == {"ok": True}
    run(client.close())


def test_invalid_external_json_fails_safely():
    def handler(request):
        return httpx.Response(
            200,
            content=b"not-json",
            request=request,
        )

    client = ExternalHttpClient()
    client._client = httpx.AsyncClient(
        transport=httpx.MockTransport(handler)
    )

    with pytest.raises(
        ValueError,
        match="external_response_invalid_json",
    ):
        run(
            client.request_json(
                "GET",
                "https://example.test/data",
            )
        )

    run(client.close())
