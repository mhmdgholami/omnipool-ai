from __future__ import annotations

import asyncio
from typing import Any

import httpx

from backend.config import settings


class ExternalHttpClient:
    """Shared connection pool for outbound APIs."""

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
                connect=min(4.0, settings.request_timeout_seconds),
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
    ) -> Any:
        await self.start()
        if self._client is None:
            raise RuntimeError("http_client_not_started")

        response = await self._client.request(
            method,
            url,
            headers=headers,
            json=json_body,
            timeout=timeout_seconds or settings.request_timeout_seconds,
        )
        response.raise_for_status()
        return response.json()


external_http = ExternalHttpClient()
