from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from typing import TypeVar

from backend.ai.exceptions import ProviderError

T = TypeVar("T")


async def retry_async(
    operation: Callable[[], Awaitable[T]],
    *,
    retries: int,
    base_delay_seconds: float = 0.2,
) -> T:
    attempt = 0
    while True:
        try:
            return await operation()
        except ProviderError as exc:
            if not exc.retryable or attempt >= retries:
                raise
            delay = base_delay_seconds * (2**attempt)
            attempt += 1
            await asyncio.sleep(delay)
