"""Shared feed client primitives: rate limiting, caching, and HTTP handling."""

from __future__ import annotations

import time
from collections.abc import Callable
from threading import Lock
from typing import Any

import requests

from ..models import FeedClientError, IntelligenceConfig, RateLimitError


class TTLCache:
    """Small in-memory TTL cache for feed responses."""

    def __init__(self, ttl_seconds: int) -> None:
        self._ttl_seconds = ttl_seconds
        self._store: dict[str, tuple[float, Any]] = {}
        self._lock = Lock()

    def get(self, key: str) -> Any | None:
        now = time.monotonic()
        with self._lock:
            item = self._store.get(key)
            if item is None:
                return None
            expiry, value = item
            if now >= expiry:
                self._store.pop(key, None)
                return None
            return value

    def set(self, key: str, value: Any) -> None:
        with self._lock:
            self._store[key] = (time.monotonic() + self._ttl_seconds, value)


class SlidingWindowRateLimiter:
    """Simple process-local sliding window limiter."""

    def __init__(self, max_calls_per_minute: int) -> None:
        self.max_calls_per_minute = max(1, max_calls_per_minute)
        self._calls: list[float] = []
        self._lock = Lock()

    def acquire(self) -> None:
        now = time.monotonic()
        window_start = now - 60.0
        with self._lock:
            self._calls = [call_time for call_time in self._calls if call_time >= window_start]
            if len(self._calls) >= self.max_calls_per_minute:
                raise RateLimitError("Rate limit exceeded for feed client")
            self._calls.append(now)


class BaseFeedClient:
    """Base class with shared execution wrappers for feed clients."""

    source_name: str = "base"

    def __init__(self, config: IntelligenceConfig) -> None:
        self.config = config
        self.cache = TTLCache(config.cache_ttl_seconds)
        self.rate_limiter = SlidingWindowRateLimiter(config.rate_limit_per_minute)

    def _cached(self, key: str, fn: Callable[[], Any]) -> Any:
        cached = self.cache.get(key)
        if cached is not None:
            return cached
        self.rate_limiter.acquire()
        value = fn()
        self.cache.set(key, value)
        return value

    def _request_json(
        self,
        *,
        url: str,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        try:
            response = requests.get(
                url,
                params=params,
                headers=headers,
                timeout=self.config.request_timeout_seconds,
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as exc:
            raise FeedClientError(f"{self.source_name} request failed: {exc}") from exc
        except ValueError as exc:
            raise FeedClientError(f"{self.source_name} returned non-JSON response") from exc
