from __future__ import annotations

import asyncio
import time

from backend.config import settings
from backend.services.http import external_http


class DexScreenerAdapter:
    def __init__(self) -> None:
        self._cache: list[dict] = []
        self._cached_at = 0.0
        self._lock = asyncio.Lock()

    async def scan(self) -> list[dict]:
        now = time.monotonic()
        if self._cache and now - self._cached_at < settings.cache_ttl_seconds:
            return list(self._cache)

        async with self._lock:
            now = time.monotonic()
            if self._cache and now - self._cached_at < settings.cache_ttl_seconds:
                return list(self._cache)

            endpoints = (
                ("boost", f"{settings.dexscreener_base_url}/token-boosts/top/v1"),
                ("profile", f"{settings.dexscreener_base_url}/token-profiles/latest/v1"),
            )
            results = await asyncio.gather(
                *(external_http.request_json("GET", url) for _, url in endpoints),
                return_exceptions=True,
            )

            signals: list[dict] = []
            for (kind, _), result in zip(endpoints, results):
                if isinstance(result, Exception) or not isinstance(result, list):
                    continue

                for item in result[:30]:
                    if item.get("chainId") != "solana":
                        continue

                    description = (
                        item.get("description") or "Solana token signal"
                    ).strip()
                    signals.append(
                        {
                            "external_id": (
                                item.get("tokenAddress")
                                or item.get("url")
                                or description
                            ),
                            "title": description[:96],
                            "summary": description[:320],
                            "kind": kind,
                            "address": item.get("tokenAddress", ""),
                            "url": item.get("url", ""),
                        }
                    )

            self._cache = signals[: settings.market_cache_size]
            self._cached_at = time.monotonic()
            return list(self._cache)


dex_adapter = DexScreenerAdapter()
