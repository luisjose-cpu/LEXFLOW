from time import perf_counter
from uuid import uuid4

from fastapi import Request
from starlette.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware


REQUEST_METRICS = {
    "requests_total": 0,
    "errors_total": 0,
    "last_response_time_ms": 0.0,
}


def apply_security_headers(response):
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Referrer-Policy", "no-referrer")
    response.headers.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
    response.headers.setdefault("Strict-Transport-Security", "max-age=63072000; includeSubDomains; preload")
    response.headers.setdefault("Cache-Control", "no-store")
    return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        return apply_security_headers(response)


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, *, limit_per_minute: int) -> None:
        super().__init__(app)
        self.limit_per_minute = limit_per_minute
        self._buckets: dict[tuple[str, int], int] = {}
        self._last_pruned_bucket = 0

    def _prune_old_buckets(self, current_bucket: int) -> None:
        if current_bucket <= self._last_pruned_bucket:
            return
        stale_buckets = [key for key in self._buckets if key[1] < current_bucket - 1]
        for key in stale_buckets:
            self._buckets.pop(key, None)
        self._last_pruned_bucket = current_bucket

    async def dispatch(self, request: Request, call_next):
        if self.limit_per_minute > 0:
            client_host = request.client.host if request.client else "unknown"
            bucket = int(perf_counter() // 60)
            self._prune_old_buckets(bucket)
            key = (client_host, bucket)
            self._buckets[key] = self._buckets.get(key, 0) + 1
            if self._buckets[key] > self.limit_per_minute:
                request_id = request.headers.get("X-Request-Id", str(uuid4()))
                response = JSONResponse(status_code=429, content={"detail": "Rate limit exceeded", "request_id": request_id})
                response.headers["X-Request-Id"] = request_id
                return apply_security_headers(response)
        return await call_next(request)


class CSRFSafeOriginMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, *, allowed_origins: list[str]) -> None:
        super().__init__(app)
        self.allowed_origins = set(allowed_origins)

    async def dispatch(self, request: Request, call_next):
        if request.method in {"POST", "PUT", "PATCH", "DELETE"}:
            origin = request.headers.get("origin")
            if origin and origin not in self.allowed_origins:
                request_id = request.headers.get("X-Request-Id", str(uuid4()))
                response = JSONResponse(status_code=403, content={"detail": "Origin not allowed", "request_id": request_id})
                response.headers["X-Request-Id"] = request_id
                return apply_security_headers(response)
        return await call_next(request)


class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-Id", str(uuid4()))
        request.state.request_id = request_id
        request.state.tenant_id = request.headers.get("X-Tenant-Id")
        request.state.audit_context = {"request_id": request_id}

        started_at = perf_counter()
        response = await call_next(request)
        elapsed_ms = round((perf_counter() - started_at) * 1000, 2)
        REQUEST_METRICS["requests_total"] += 1
        REQUEST_METRICS["last_response_time_ms"] = elapsed_ms
        if response.status_code >= 500:
            REQUEST_METRICS["errors_total"] += 1
        response.headers["X-Request-Id"] = request_id
        response.headers["X-Response-Time-Ms"] = str(elapsed_ms)
        return response
