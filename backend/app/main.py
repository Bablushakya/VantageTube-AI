"""
VantageTube AI - Main FastAPI Application
Phase 5: Security hardening + request logging + Retry-After header
"""

import time
import logging
import uuid
from pathlib import Path

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.api import auth, users, youtube, seo, content, trending

# ── Logging setup ─────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("vantagetube")

# ── Application ───────────────────────────────────────────────────────────────
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI-powered YouTube Creator Optimisation Platform",
    debug=settings.DEBUG,
    # Hide /docs and /redoc in production
    docs_url="/docs" if settings.ENVIRONMENT != "production" else None,
    redoc_url="/redoc" if settings.ENVIRONMENT != "production" else None,
)


# ─────────────────────────────────────────────────────────────────────────────
# 5.1  CORS — use settings.cors_origins instead of wildcard
# ─────────────────────────────────────────────────────────────────────────────
# In development (.env: ENVIRONMENT=development) cors_origins defaults to
# ["http://localhost:3000", "http://localhost:5500", "http://127.0.0.1:5500"]
# which covers Live Server and common dev ports.
#
# In production set ALLOWED_ORIGINS in .env to your real domain(s):
#   ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
# ─────────────────────────────────────────────────────────────────────────────
_cors_origins = (
    ["*"] if settings.ENVIRONMENT == "development"
    else settings.cors_origins
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept"],
    expose_headers=["Retry-After", "X-Request-ID"],
)


# ─────────────────────────────────────────────────────────────────────────────
# 5.3  REQUEST LOGGING MIDDLEWARE
# Logs: method, path, status code, duration, user-agent, request-id
# ─────────────────────────────────────────────────────────────────────────────
@app.middleware("http")
async def request_logging_middleware(request: Request, call_next):
    request_id = str(uuid.uuid4())[:8]
    start = time.perf_counter()

    # Attach request-id so downstream handlers can reference it
    request.state.request_id = request_id

    response: Response = await call_next(request)

    duration_ms = (time.perf_counter() - start) * 1000
    user_agent  = request.headers.get("user-agent", "-")[:80]

    log_fn = logger.warning if response.status_code >= 400 else logger.info
    log_fn(
        f"[{request_id}] {request.method} {request.url.path} "
        f"→ {response.status_code}  {duration_ms:.1f}ms  ua={user_agent!r}"
    )

    # Attach request-id to every response for client-side debugging
    response.headers["X-Request-ID"] = request_id
    return response


# ─────────────────────────────────────────────────────────────────────────────
# 5.4  GLOBAL 429 HANDLER — adds Retry-After header
# ─────────────────────────────────────────────────────────────────────────────
# The Retry-After value tells the client exactly how many seconds to wait.
# For per-minute limits: 60 s.  For daily limits: seconds until midnight UTC.
# ─────────────────────────────────────────────────────────────────────────────
from fastapi.exceptions import RequestValidationError
from fastapi import status as http_status
from starlette.exceptions import HTTPException as StarletteHTTPException
import math
from datetime import datetime, timezone


def _retry_after_seconds(detail: str) -> int:
    """
    Infer a sensible Retry-After value from the quota error message.
    - "per minute"  → 60 s
    - "per hour"    → 3600 s
    - "per day" / "midnight" → seconds until next UTC midnight
    - fallback      → 60 s
    """
    msg = detail.lower()
    if "per day" in msg or "daily" in msg or "midnight" in msg:
        now = datetime.now(timezone.utc)
        midnight = (now + __import__("datetime").timedelta(days=1)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        return max(1, math.ceil((midnight - now).total_seconds()))
    if "per hour" in msg:
        return 3600
    if "per minute" in msg or "rate limit" in msg:
        return 60
    return 60


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    headers = {}

    if exc.status_code == 429:
        detail = str(exc.detail) if exc.detail else "Too many requests"
        retry_after = _retry_after_seconds(detail)
        headers["Retry-After"] = str(retry_after)
        logger.warning(
            f"429 for {request.url.path} — Retry-After: {retry_after}s  detail: {detail}"
        )
        return JSONResponse(
            status_code=429,
            content={
                "detail": detail,
                "retry_after_seconds": retry_after,
                "message": f"Please wait {retry_after} seconds before retrying.",
            },
            headers=headers,
        )

    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": str(exc.detail)},
        headers=headers,
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Return clean 422 validation errors."""
    errors = [
        {"field": " → ".join(str(l) for l in e["loc"]), "message": e["msg"]}
        for e in exc.errors()
    ]
    return JSONResponse(
        status_code=422,
        content={"detail": "Validation error", "errors": errors},
    )


# ─────────────────────────────────────────────────────────────────────────────
# ROUTERS
# ─────────────────────────────────────────────────────────────────────────────
app.include_router(auth.router,     prefix="/api")
app.include_router(users.router,    prefix="/api")
app.include_router(youtube.router,  prefix="/api")
app.include_router(seo.router,      prefix="/api")
app.include_router(content.router,  prefix="/api")
app.include_router(trending.router, prefix="/api")


# ─────────────────────────────────────────────────────────────────────────────
# 5.2  STATIC FILES — only in development
# In production the frontend is served by a CDN / separate web server.
# ─────────────────────────────────────────────────────────────────────────────
if settings.ENVIRONMENT != "production":
    frontend_path = Path(__file__).parent.parent.parent / "frontend"
    if frontend_path.exists():
        app.mount(
            "/",
            StaticFiles(directory=str(frontend_path), html=True),
            name="static",
        )
        logger.info(f"Serving frontend from {frontend_path}")
    else:
        logger.warning(f"Frontend path not found: {frontend_path}")


# ─────────────────────────────────────────────────────────────────────────────
# HEALTH ENDPOINTS
# ─────────────────────────────────────────────────────────────────────────────
@app.get("/health", tags=["Health"])
async def health_check():
    """Lightweight health check — used by load balancers / uptime monitors."""
    return {
        "status":      "healthy",
        "app":         settings.APP_NAME,
        "version":     settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
    }


# ─────────────────────────────────────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
    )
