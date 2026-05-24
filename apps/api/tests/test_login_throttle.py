from fastapi import HTTPException
import pytest

from app.core.config import Settings
from app.services.login_throttle import LoginThrottle


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


def test_login_throttle_clear_all_resets_failures() -> None:
    throttle = LoginThrottle(settings_provider=lambda: Settings(failed_login_limit=1, failed_login_window_minutes=15))
    key = throttle.normalize_key(email="admin@lexflow.demo", tenant_slug="piloto")
    throttle.record_failure(scope="tenant", key=key)

    throttle.clear_all()

    throttle.assert_allowed(scope="tenant", key=key)
