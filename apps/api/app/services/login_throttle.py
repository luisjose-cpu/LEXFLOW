from __future__ import annotations

from datetime import datetime, timedelta
from hashlib import sha256
from typing import Any

from fastapi import HTTPException, status

from app.core.config import Settings, get_settings
from app.db.models import now_utc


class LoginThrottle:
    def __init__(self, *, settings_provider=get_settings) -> None:
        self._settings_provider = settings_provider
        self._memory_failures: dict[str, list[datetime]] = {}
        self._redis_client: Any | None = None

    def assert_allowed(self, *, scope: str, key: str) -> None:
        settings = self._settings()
        if settings.failed_login_limit <= 0:
            return
        if self._use_redis(settings):
            count = self._redis_count(scope=scope, key=key, settings=settings)
            if count is not None:
                if count >= settings.failed_login_limit:
                    self._raise_blocked()
                return
        if len(self._recent_failures(self._scoped_key(scope=scope, key=key), settings=settings)) >= settings.failed_login_limit:
            self._raise_blocked()

    def record_failure(self, *, scope: str, key: str) -> None:
        settings = self._settings()
        if settings.failed_login_limit <= 0:
            return
        if self._use_redis(settings):
            count = self._redis_increment(scope=scope, key=key, settings=settings)
            if count is not None:
                return
        scoped_key = self._scoped_key(scope=scope, key=key)
        self._memory_failures[scoped_key] = [*self._recent_failures(scoped_key, settings=settings), now_utc()]

    def clear(self, *, scope: str, key: str) -> None:
        settings = self._settings()
        if self._use_redis(settings):
            if self._redis_delete(scope=scope, key=key, settings=settings):
                return
        self._memory_failures.pop(self._scoped_key(scope=scope, key=key), None)

    def clear_all(self) -> None:
        self._memory_failures.clear()

    def _settings(self) -> Settings:
        return self._settings_provider()

    @staticmethod
    def normalize_key(*, email: str, tenant_slug: str | None = None) -> str:
        return f"{(tenant_slug or '').strip().lower()}:{email.strip().lower()}"

    @staticmethod
    def _scoped_key(*, scope: str, key: str) -> str:
        digest = sha256(key.strip().lower().encode("utf-8")).hexdigest()
        return f"lexflow:login-throttle:{scope}:{digest}"

    def _recent_failures(self, scoped_key: str, *, settings: Settings) -> list[datetime]:
        cutoff = now_utc() - timedelta(minutes=settings.failed_login_window_minutes)
        recent = [item for item in self._memory_failures.get(scoped_key, []) if item > cutoff]
        self._memory_failures[scoped_key] = recent
        return recent

    @staticmethod
    def _raise_blocked() -> None:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Too many failed login attempts")

    @staticmethod
    def _use_redis(settings: Settings) -> bool:
        return settings.failed_login_backend.lower() == "redis" and settings.redis_url.startswith("redis")

    def _redis(self, settings: Settings):
        if self._redis_client is not None:
            return self._redis_client
        try:
            from redis import Redis

            self._redis_client = Redis.from_url(settings.redis_url, decode_responses=True, socket_connect_timeout=0.2, socket_timeout=0.2)
            return self._redis_client
        except Exception:
            return None

    def _redis_count(self, *, scope: str, key: str, settings: Settings) -> int | None:
        client = self._redis(settings)
        if client is None:
            return None
        try:
            value = client.get(self._scoped_key(scope=scope, key=key))
            return int(value or 0)
        except Exception:
            return None

    def _redis_increment(self, *, scope: str, key: str, settings: Settings) -> int | None:
        client = self._redis(settings)
        if client is None:
            return None
        redis_key = self._scoped_key(scope=scope, key=key)
        try:
            count = int(client.incr(redis_key))
            if count == 1:
                client.expire(redis_key, max(1, settings.failed_login_window_minutes * 60))
            return count
        except Exception:
            return None

    def _redis_delete(self, *, scope: str, key: str, settings: Settings) -> bool:
        client = self._redis(settings)
        if client is None:
            return False
        try:
            client.delete(self._scoped_key(scope=scope, key=key))
            return True
        except Exception:
            return False


login_throttle = LoginThrottle()
