"""Kosh-AI — FastAPI Application Entry Point."""
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse

from backend.config import get_settings
from backend.database import init_db
from backend.utils.rate_limiter import RateLimitMiddleware
from backend.utils.observability import (
    ObservabilityMiddleware,
    generate_prometheus_metrics,
    detailed_health_check,
)
from backend.api import auth, merchants, suppliers, invoices, recommendations, admin, whatsapp, learning, market, predictions, autonomy, orders, onboarding, docs

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup/shutdown lifecycle."""
    # Startup
    if settings.DEBUG:
        await init_db()
    yield
    # Shutdown — cleanup if needed


app = FastAPI(
    title="Kosh-AI",
    description="Procurement Intelligence Engine for Merchants",
    version="1.0.0",
    lifespan=lifespan,
    docs_url=settings.docs_url,
    redoc_url=settings.redoc_url,
)

# ── Routes ─────────────────────────────────────────────────

API_PREFIX = "/api/v1"

app.include_router(auth.router, prefix=API_PREFIX)
app.include_router(merchants.router, prefix=API_PREFIX)
app.include_router(suppliers.router, prefix=API_PREFIX)
app.include_router(invoices.router, prefix=API_PREFIX)
app.include_router(orders.router, prefix=API_PREFIX)
app.include_router(recommendations.router, prefix=API_PREFIX)
app.include_router(admin.router, prefix=API_PREFIX)
app.include_router(whatsapp.router, prefix=API_PREFIX)
app.include_router(learning.router, prefix=API_PREFIX)
app.include_router(market.router, prefix=API_PREFIX)
app.include_router(predictions.router, prefix=API_PREFIX)
app.include_router(autonomy.router, prefix=API_PREFIX)
app.include_router(onboarding.router, prefix=API_PREFIX)
app.include_router(docs.router, prefix="/api/v1/docs")


# ── Observability Endpoints ────────────────────────────────

@app.get("/health")
async def health_check(request: Request):
    """Detailed health check with dependency status."""
    return await detailed_health_check(request)


@app.get("/metrics", response_class=PlainTextResponse)
async def prometheus_metrics():
    """Prometheus-compatible metrics endpoint."""
    return generate_prometheus_metrics()


@app.get("/")
async def root():
    return {
        "service": "Kosh-AI",
        "description": "Procurement Intelligence Engine",
        "docs": "/docs",
        "health": "/health",
        "metrics": "/metrics",
    }


# ── Middleware (order matters: first added = outermost) ─────

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(ObservabilityMiddleware)
app.add_middleware(RateLimitMiddleware)
