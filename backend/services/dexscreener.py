from __future__ import annotations

import asyncio
import time

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from backend.config import settings
from backend.services.http import external_http


class _DexItem(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
        extra="ignore",
    )

    chain_id: str = Field(alias="chainId", max_length=32)
    token_address: str = Field(
        default="",
        alias="tokenAddress",
        max_length=128,
    )
    url: str = Field(default="", max_length=512)
    description: str | None = Field(
        default=None,
        max_length=2000,
    )


class DexScreenerAdapter:
    def __init__(self) -> None:
        self._cache: list[dict] = []
        self._cached_at = 0.0
        self._lock = asyncio.Lock()

    async def scan(self) -> list[dict]:
        now = time.monotonic()
        if (
            self._cache
            and now - self._cached_at
            < settings.cache_ttl_seconds
        ):
            return list(self._cache)

        async with self._lock:
            now = time.monotonic()
            if (
                self._cache
                and now - self._cached_at
                < settings.cache_ttl_seconds
            ):
                return list(self._cache)

            endpoints = (
                (
                    "boost",
                    (
                        f"{settings.dexscreener_base_url}"
                        "/token-boosts/top/v1"
                    ),
                ),
                (
                    "profile",
                    (
                        f"{settings.dexscreener_base_url}"
                        "/token-profiles/latest/v1"
                    ),
                ),
            )
            results = await asyncio.gather(
                *(
                    external_http.request_json("GET", url)
                    for _, url in endpoints
                ),
                return_exceptions=True,
            )

            signals: list[dict] = []
            for (kind, _), result in zip(
                endpoints,
                results,
                strict=True,
            ):
                if (
                    isinstance(result, Exception)
                    or not isinstance(result, list)
                ):
                    continue

                for raw_item in result[:30]:
                    try:
                        item = _DexItem.model_validate(raw_item)
                    except ValidationError:
                        continue

                    if item.chain_id != "solana":
                        continue

                    description = (
                        item.description or "Solana token signal"
                    ).strip()
                    external_id = (
                        item.token_address
                        or item.url
                        or description
                    )
                    signals.append(
                        {
                            "external_id": external_id[:512],
                            "title": description[:96],
                            "summary": description[:320],
                            "kind": kind,
                            "address": item.token_address,
                            "url": item.url,
                        }
                    )

            self._cache = signals[
                : settings.market_cache_size
            ]
            self._cached_at = time.monotonic()
            return list(self._cache)


dex_adapter = DexScreenerAdapter()
