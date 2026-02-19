"""Network Intelligence Worker."""
import asyncio
from backend.workers.celery_app import celery_app
from backend.database import async_session_factory
from backend.services.network_intelligence.market_price_engine import update_market_prices
from backend.services.network_intelligence.supplier_benchmark_engine import update_supplier_benchmarks
from backend.services.network_intelligence.trend_detector import detect_market_trends
from backend.services.network_intelligence.risk_alert_engine import scan_for_risks
from celery.utils.log import get_task_logger

logger = get_task_logger(__name__)

async def run_market_prices():
    async with async_session_factory() as db:
        await update_market_prices(db)
        await db.commit()

async def run_supplier_benchmarks():
    async with async_session_factory() as db:
        await update_supplier_benchmarks(db)
        await db.commit()

async def run_trend_detection():
    async with async_session_factory() as db:
        await detect_market_trends(db)
        await db.commit()

async def run_risk_scan():
    async with async_session_factory() as db:
        await scan_for_risks(db)
        await db.commit()

@celery_app.task(bind=True, name="backend.workers.network_worker.update_prices")
def task_update_prices(self):
    try:
        asyncio.run(run_market_prices())
    except Exception as e:
        logger.error(f"Update Prices failed: {e}")
        raise self.retry(exc=e)

@celery_app.task(bind=True, name="backend.workers.network_worker.update_benchmarks")
def task_update_benchmarks(self):
    try:
        asyncio.run(run_supplier_benchmarks())
    except Exception as e:
        logger.error(f"Update Benchmarks failed: {e}")
        raise self.retry(exc=e)

@celery_app.task(bind=True, name="backend.workers.network_worker.detect_trends")
def task_detect_trends(self):
    try:
        asyncio.run(run_trend_detection())
    except Exception as e:
        logger.error(f"Detect Trends failed: {e}")
        raise self.retry(exc=e)

@celery_app.task(bind=True, name="backend.workers.network_worker.scan_risks")
def task_scan_risks(self):
    try:
        asyncio.run(run_risk_scan())
    except Exception as e:
        logger.error(f"Scan Risks failed: {e}")
        raise self.retry(exc=e)
