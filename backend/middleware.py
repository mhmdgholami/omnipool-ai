from __future__ import annotations

import time
from collections import OrderedDict
from dataclasses import dataclass


@dataclass(slots=True)
class _Bucket:
    tokens: float
    updated_at: float


class BoundedTokenBucket:
    """Process-local limiter with O(max_clients) bounded memory."""

    def __init__(self, requests_per_minute: int, max_clients: int) -> None:
        self._capacity = max(1, requests_per_minute)
        self._refill_per_second = self._capacity / 60.0
        self._max_clients = max(32, max_clients)
        self._buckets: OrderedDict[str, _Bucket] = OrderedDict()

    def allow(self, key: str, now: float | None = None) -> bool:
        timestamp = time.monotonic() if now is None else now
        bucket = self._buckets.get(key)

        if bucket is None:
            if len(self._buckets) >= self._max_clients:
                self._buckets.popitem(last=False)
            self._buckets[key] = _Bucket(self._capacity - 1.0, timestamp)
            return True

        elapsed = max(0.0, timestamp - bucket.updated_at)
        bucket.tokens = min(
            float(self._capacity),
            bucket.tokens + elapsed * self._refill_per_second,
        )
        bucket.updated_at = timestamp
        self._buckets.move_to_end(key)

        if bucket.tokens < 1.0:
            return False

        bucket.tokens -= 1.0
        return True
