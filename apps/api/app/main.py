from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes import router
from app.core.config import get_settings
from app.core.middleware import CSRFSafeOriginMiddleware, REQUEST_METRICS, RateLimitMiddleware, RequestContextMiddleware, SecurityHeadersMiddleware
from app.core.readiness import assert_startup_readiness, production_readiness_report
from app.services.seed import seed_demo_data

settings = get_settings()
assert_startup_readiness(settings)
if settings.seed_demo_on_startup and settings.app_env.lower() != "production":
    seed_demo_data()

app = FastAPI(title=settings.app_name, version=settings.api_version)
allowed_origins = [origin.strip() for origin in settings.allowed_origins.split(",") if origin.strip()]

app.add_middleware(RequestContextMiddleware)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RateLimitMiddleware, limit_per_minute=settings.rate_limit_per_minute)
app.add_middleware(CSRFSafeOriginMiddleware, allowed_origins=allowed_origins)
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api/v1")


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "request_id": getattr(request.state, "request_id", None)},
    )


@app.get("/health")
def root_health() -> dict[str, str]:
    return {"status": "ok", "service": settings.app_name}


@app.get("/version")
def root_version() -> dict[str, str]:
    return {"version": settings.api_version, "phase": settings.release_phase, "release": settings.release_name}


@app.get("/readiness")
def root_readiness() -> dict[str, object]:
    return production_readiness_report(settings)


@app.get("/metrics")
def root_metrics() -> dict[str, object]:
    return {
        "service": settings.app_name,
        "phase": settings.release_phase,
        "release": settings.release_name,
        "requests_total": REQUEST_METRICS["requests_total"],
        "errors_total": REQUEST_METRICS["errors_total"],
        "last_response_time_ms": REQUEST_METRICS["last_response_time_ms"],
    }
