"""OpenTelemetry + Prometheus observability middleware and instrumentation."""
import time
import logging
from typing import Callable

from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger("kosh.observability")

# ── In-memory metrics store (exported to Prometheus) ───────

_metrics = {
    "http_requests_total": {},          # {method_path_status: count}
    "http_request_duration_seconds": {},  # {method_path: [sum, count]}
    "ocr_tasks_total": {"completed": 0, "failed": 0, "retried": 0},
    "ocr_processing_seconds": [],
    "active_celery_tasks": 0,
    "invoice_uploads_total": 0,
    "recommendations_generated_total": 0,
    "dlq_messages_total": 0,
}


def inc_counter(name: str, labels: str = "", value: int = 1):
    key = f"{name}:{labels}"
    if key not in _metrics["http_requests_total"]:
        _metrics["http_requests_total"][key] = 0
    _metrics["http_requests_total"][key] += value


def observe_histogram(name: str, value: float):
    if name not in _metrics:
        _metrics[name] = []
    _metrics[name].append(value)


def inc_ocr_metric(status: str):
    _metrics["ocr_tasks_total"][status] = _metrics["ocr_tasks_total"].get(status, 0) + 1


def inc_simple(name: str, value: int = 1):
    _metrics[name] = _metrics.get(name, 0) + value


# ── Prometheus metrics endpoint ────────────────────────────

def generate_prometheus_metrics() -> str:
    """Generate Prometheus-compatible text exposition format."""
    lines = []

    # HTTP request counters
    lines.append("# HELP kosh_http_requests_total Total HTTP requests")
    lines.append("# TYPE kosh_http_requests_total counter")
    for key, count in _metrics["http_requests_total"].items():
        parts = key.split(":")
        if len(parts) == 2:
            lines.append(f'kosh_http_requests_total{{endpoint="{parts[1]}"}} {count}')

    # OCR task counters
    lines.append("# HELP kosh_ocr_tasks_total Total OCR processing tasks")
    lines.append("# TYPE kosh_ocr_tasks_total counter")
    for status, count in _metrics["ocr_tasks_total"].items():
        lines.append(f'kosh_ocr_tasks_total{{status="{status}"}} {count}')

    # Simple counters
    lines.append("# HELP kosh_invoice_uploads_total Total invoice uploads")
    lines.append("# TYPE kosh_invoice_uploads_total counter")
    lines.append(f'kosh_invoice_uploads_total {_metrics.get("invoice_uploads_total", 0)}')

    lines.append("# HELP kosh_recommendations_generated_total Total recommendations generated")
    lines.append("# TYPE kosh_recommendations_generated_total counter")
    lines.append(f'kosh_recommendations_generated_total {_metrics.get("recommendations_generated_total", 0)}')

    lines.append("# HELP kosh_dlq_messages_total Total dead letter queue messages")
    lines.append("# TYPE kosh_dlq_messages_total counter")
    lines.append(f'kosh_dlq_messages_total {_metrics.get("dlq_messages_total", 0)}')

    # OCR duration histogram approximation
    durations = _metrics.get("ocr_processing_seconds", [])
    if durations:
        lines.append("# HELP kosh_ocr_duration_seconds OCR processing duration")
        lines.append("# TYPE kosh_ocr_duration_seconds summary")
        lines.append(f'kosh_ocr_duration_seconds_sum {sum(durations):.3f}')
        lines.append(f'kosh_ocr_duration_seconds_count {len(durations)}')

    return "\n".join(lines) + "\n"


# ── Request tracing middleware ─────────────────────────────

class ObservabilityMiddleware(BaseHTTPMiddleware):
    """Records request metrics, adds trace context headers."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start = time.perf_counter()
        method = request.method
        path = request.url.path

        # Generate trace ID
        import uuid
        trace_id = request.headers.get("X-Trace-ID", uuid.uuid4().hex[:16])

        try:
            response = await call_next(request)
            duration = time.perf_counter() - start

            # Record metrics
            label = f"{method} {path} {response.status_code}"
            inc_counter("http_requests_total", label)

            # Add trace headers to response
            response.headers["X-Trace-ID"] = trace_id
            response.headers["X-Response-Time"] = f"{duration:.4f}s"

            # Log slow requests
            if duration > 2.0:
                logger.warning(f"Slow request: {method} {path} took {duration:.2f}s "
                              f"[trace={trace_id}]")

            return response
        except Exception as exc:
            duration = time.perf_counter() - start
            label = f"{method} {path} 500"
            inc_counter("http_requests_total", label)
            logger.error(f"Request failed: {method} {path} after {duration:.2f}s "
                        f"[trace={trace_id}] error={exc}")
            raise


# ── Health check with dependency status ────────────────────

async def detailed_health_check(request: Request) -> dict:
    """Returns health status with dependency checks."""
    import redis.asyncio as aioredis
    from backend.config import get_settings
    from sqlalchemy import text
    from backend.database import async_session_factory

    settings = get_settings()
    health = {
        "status": "healthy",
        "service": "kosh-ai",
        "version": "1.0.0",
        "dependencies": {}
    }

    # Check PostgreSQL
    try:
        async with async_session_factory() as session:
            await session.execute(text("SELECT 1"))
        health["dependencies"]["postgres"] = {"status": "up"}
    except Exception as e:
        health["dependencies"]["postgres"] = {"status": "down", "error": str(e)}
        health["status"] = "degraded"

    # Check Redis
    try:
        r = aioredis.from_url(settings.REDIS_URL)
        await r.ping()
        await r.close()
        health["dependencies"]["redis"] = {"status": "up"}
    except Exception as e:
        health["dependencies"]["redis"] = {"status": "down", "error": str(e)}
        health["status"] = "degraded"

    return health
