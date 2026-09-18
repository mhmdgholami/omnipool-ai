from __future__ import annotations

import time
from dataclasses import dataclass

from backend.ai.schemas import ProviderHealth


@dataclass(slots=True)
class _HealthEntry:
    value: ProviderHealth
    expires_at: float


class HealthCache:
    def __init__(self, ttl_seconds: float, max_entries: int = 16) -> None:
        self._ttl_seconds = max(1.0, ttl_seconds)
        self._max_entries = max(1, max_entries)
        self._values: dict[str, _HealthEntry] = {}

    def get(self, key: str) -> ProviderHealth | None:
        entry = self._values.get(key)
        if entry is None:
            return None
        if entry.expires_at <= time.monotonic():
            self._values.pop(key, None)
            return None
        return entry.value

    def set(
        self, key: str, value: ProviderHealth
    ) -> ProviderHealth:
        if len(self._values) >= self._max_entries and key not in self._values:
            oldest = next(iter(self._values))
            self._values.pop(oldest, None)
        self._values[key] = _HealthEntry(
            value=value,
            expires_at=time.monotonic() + self._ttl_seconds,
        )
        return value

    def clear(self) -> None:
        self._values.clear()
