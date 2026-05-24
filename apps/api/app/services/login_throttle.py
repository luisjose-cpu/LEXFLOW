from __future__ import annotations

from datetime import datetime, timedelta

from fastapi import HTTPException, status

from app.core.config import Settings, get_settings
from app.db.models import now_utc


class LoginThrottle:
    def __init__(self, *, settings_provider=get_settings) -> None:
        self._settings_provider = settings_provider
        self._memory_failures: dict[str, list[datetime]] = {}

    def assert_allowed(self, *, scope: str, key: str) -> None:
        settings = self._settings()
        if settings.failed_login_limit <= 0:
            return
        if len(self._recent_failures(self._scoped_key(scope=scope, key=key), settings=settings)) >= settings.failed_login_limit:
            raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Too many failed login attempts")

    def record_failure(self, *, scope: str, key: str) -> None:
        settings = self._settings()
        if settings.failed_login_limit <= 0:
            return
        scoped_key = self._scoped_key(scope=scope, key=key)
        self._memory_failures[scoped_key] = [*self._recent_failures(scoped_key, settings=settings), now_utc()]

    def clear(self, *, scope: str, key: str) -> None:
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
        return f"{scope}:{key.strip().lower()}"

    def _recent_failures(self, scoped_key: str, *, settings: Settings) -> list[datetime]:
        cutoff = now_utc() - timedelta(minutes=settings.failed_login_window_minutes)
        recent = [item for item in self._memory_failures.get(scoped_key, []) if item > cutoff]
        self._memory_failures[scoped_key] = recent
        return recent


login_throttle = LoginThrottle()
