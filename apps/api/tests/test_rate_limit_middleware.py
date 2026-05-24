from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Route
from starlette.testclient import TestClient

from app.core.middleware import RateLimitMiddleware, SecurityHeadersMiddleware


def test_rate_limit_prunes_stale_buckets() -> None:
    middleware = RateLimitMiddleware(Starlette(), limit_per_minute=100)
    middleware._buckets = {
        ("old", 1): 20,
        ("previous", 9): 3,
        ("current", 10): 1,
    }

    middleware._prune_old_buckets(10)

    assert ("old", 1) not in middleware._buckets
    assert middleware._buckets[("previous", 9)] == 3
    assert middleware._buckets[("current", 10)] == 1


def test_rate_limit_prune_runs_once_per_bucket() -> None:
    middleware = RateLimitMiddleware(Starlette(), limit_per_minute=100)
    middleware._buckets = {("old", 1): 20}

    middleware._prune_old_buckets(10)
    middleware._buckets[("late-old", 1)] = 5
    middleware._prune_old_buckets(10)

    assert ("late-old", 1) in middleware._buckets


def test_rate_limit_response_has_security_headers_and_request_id() -> None:
    async def limited(_request):
        return JSONResponse({"ok": True})

    app = Starlette(routes=[Route("/limited", limited)])
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(RateLimitMiddleware, limit_per_minute=1)
    client = TestClient(app)

    assert client.get("/limited").status_code == 200
    blocked = client.get("/limited", headers={"X-Request-Id": "req-rate-limit"})

    assert blocked.status_code == 429
    assert blocked.json()["request_id"] == "req-rate-limit"
    assert blocked.headers["X-Request-Id"] == "req-rate-limit"
    assert blocked.headers["X-Content-Type-Options"] == "nosniff"
    assert blocked.headers["X-Frame-Options"] == "DENY"
    assert blocked.headers["Content-Security-Policy"] == "default-src 'none'; frame-ancestors 'none'; base-uri 'none'"
    assert blocked.headers["Cross-Origin-Opener-Policy"] == "same-origin"
    assert blocked.headers["Cross-Origin-Resource-Policy"] == "same-origin"
