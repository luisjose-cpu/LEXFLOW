from starlette.applications import Starlette

from app.core.middleware import RateLimitMiddleware


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
