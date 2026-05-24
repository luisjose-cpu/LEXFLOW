from fastapi import HTTPException
import pytest

from app.core.config import Settings
from app.services.login_throttle import LoginThrottle


class FakeRedis:
    def __init__(self) -> None:
        self.values: dict[str, int] = {}
        self.expirations: dict[str, int] = {}

    def get(self, key: str) -> int | None:
        return self.values.get(key)

    def incr(self, key: str) -> int:
        self.values[key] = self.values.get(key, 0) + 1
        return self.values[key]

    def expire(self, key: str, seconds: int) -> None:
        self.expirations[key] = seconds

    def delete(self, key: str) -> None:
        self.values.pop(key, None)


def test_login_throttle_blocks_after_configured_failures() -> None:
    throttle = LoginThrottle(settings_provider=lambda: Settings(failed_login_limit=2, failed_login_window_minutes=15))
    key = throttle.normalize_key(email="Admin@Lexflow.Demo", tenant_slug="Piloto")

    throttle.record_failure(scope="tenant", key=key)
    throttle.record_failure(scope="tenant", key=key)

    with pytest.raises(HTTPException) as exc:
        throttle.assert_allowed(scope="tenant", key=key)

    assert exc.value.status_code == 429


def test_login_throttle_scopes_tenant_and_owner_independently() -> None:
    throttle = LoginThrottle(settings_provider=lambda: Settings(failed_login_limit=1, failed_login_window_minutes=15))
    key = throttle.normalize_key(email="owner@lexflow.com")

    throttle.record_failure(scope="owner", key=key)

    with pytest.raises(HTTPException):
        throttle.assert_allowed(scope="owner", key=key)
    throttle.assert_allowed(scope="tenant", key=key)


def test_login_throttle_uses_redis_backend_with_hashed_keys() -> None:
    redis = FakeRedis()
    throttle = LoginThrottle(settings_provider=lambda: Settings(failed_login_backend="redis", failed_login_limit=2, failed_login_window_minutes=15))
    throttle._redis_client = redis
    key = throttle.normalize_key(email="admin@lexflow.demo", tenant_slug="piloto")

    throttle.record_failure(scope="tenant", key=key)
    throttle.record_failure(scope="tenant", key=key)

    assert all("admin@lexflow.demo" not in item for item in redis.values)
    assert list(redis.expirations.values()) == [900]
    with pytest.raises(HTTPException) as exc:
        throttle.assert_allowed(scope="tenant", key=key)
    assert exc.value.status_code == 429

    throttle.clear(scope="tenant", key=key)
    throttle.assert_allowed(scope="tenant", key=key)


def test_login_throttle_clear_all_resets_failures() -> None:
    throttle = LoginThrottle(settings_provider=lambda: Settings(failed_login_limit=1, failed_login_window_minutes=15))
    key = throttle.normalize_key(email="admin@lexflow.demo", tenant_slug="piloto")
    throttle.record_failure(scope="tenant", key=key)

    throttle.clear_all()

    throttle.assert_allowed(scope="tenant", key=key)
