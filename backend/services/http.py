from __future__ import annotations

import asyncio
import json
from typing import Any

import httpx

from backend.config import settings


class ExternalResponseTooLarge(RuntimeError):
    pass


class ExternalHttpClient:
    """Shared connection pool for bounded outbound JSON requests."""

    def __init__(self) -> None:
        self._client: httpx.AsyncClient | None = None
        self._lock = asyncio.Lock()

    async def start(self) -> None:
        if self._client is not None:
            return

        async with self._lock:
            if self._client is not None:
                return

            timeout = httpx.Timeout(
                settings.request_timeout_seconds,
                connect=min(
                    4.0,
                    settings.request_timeout_seconds,
                ),
            )
            limits = httpx.Limits(
                max_connections=8,
                max_keepalive_connections=4,
                keepalive_expiry=30.0,
            )
            self._client = httpx.AsyncClient(
                timeout=timeout,
                limits=limits,
                follow_redirects=True,
                headers={"User-Agent": "omnipool-ai/0.4"},
            )

    async def close(self) -> None:
        client, self._client = self._client, None
        if client is not None:
            await client.aclose()

    async def request_json(
        self,
        method: str,
        url: str,
        *,
        headers: dict[str, str] | None = None,
        json_body: dict[str, Any] | None = None,
        timeout_seconds: float | None = None,
        max_response_bytes: int | None = None,
    ) -> Any:
        await self.start()
        if self._client is None:
            raise RuntimeError("http_client_not_started")

        byte_limit = (
            max_response_bytes
            if max_response_bytes is not None
            else settings.max_external_response_bytes
        )
        if byte_limit <= 0:
            raise ValueError("max_response_bytes_must_be_positive")

        async with self._client.stream(
            method,
            url,
            headers=headers,
            json=json_body,
            timeout=(
                timeout_seconds
                or settings.request_timeout_seconds
            ),
        ) as response:
            response.raise_for_status()

            declared_length = response.headers.get(
                "content-length"
            )
            if declared_length:
                try:
                    declared_size = int(declared_length)
                except ValueError:
                    declared_size = 0
                if declared_size > byte_limit:
                    raise ExternalResponseTooLarge(
                        "external_response_too_large"
                    )

            payload = bytearray()
            async for chunk in response.aiter_bytes():
                if len(payload) + len(chunk) > byte_limit:
                    raise ExternalResponseTooLarge(
                        "external_response_too_large"
                    )
                payload.extend(chunk)

        try:
            return json.loads(payload)
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            raise ValueError(
                "external_response_invalid_json"
            ) from exc


external_http = ExternalHttpClient()
