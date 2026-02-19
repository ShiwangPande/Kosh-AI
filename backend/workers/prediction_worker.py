"""Prediction Worker."""
import asyncio
from backend.workers.celery_app import celery_app
from backend.database import async_session_factory
from backend.models.models import Merchant, Product, Supplier
from sqlalchemy import select

from backend.services.predictions.price_forecaster import forecast_price
from backend.services.predictions.demand_forecaster import forecast_demand
from backend.services.predictions.restock_predictor import predict_restock
from backend.services.predictions.supplier_risk_predictor import predict_supplier_risk
from celery.utils.log import get_task_logger

logger = get_task_logger(__name__)

async def run_price_predictions():
    """Predict prices for top products in major cities."""
    async with async_session_factory() as db:
        # Fetch active products & cities
        # Mock: Iterate top 10 products
        products = (await db.execute(select(Product).limit(10))).scalars().all()
        cities = ["Delhi", "Mumbai"] # Placeholder
        
        for p in products:
            for city in cities:
                pred = await forecast_price(db, p.id, city)
                if pred:
                    db.add(pred)
        await db.commit()

async def run_demand_predictions():
    """Predict demand for all merchants."""
    async with async_session_factory() as db:
        merchants = (await db.execute(select(Merchant).limit(5))).scalars().all()
        # For each merchant, predict demand for their top products
        # Mock logic
        pass
        await db.commit()

async def run_restock_predictions():
    """Check restock needs."""
    async with async_session_factory() as db:
        # Iterate active merchants
        pass
        await db.commit()

@celery_app.task(bind=True, name="backend.workers.prediction_worker.run_price_forecasts")
def task_run_price_forecasts(self):
    try:
        asyncio.run(run_price_predictions())
    except Exception as e:
        logger.error(f"Price Forecast failed: {e}")
        raise self.retry(exc=e)

@celery_app.task(bind=True, name="backend.workers.prediction_worker.run_demand_forecasts")
def task_run_demand_forecasts(self):
    try:
        asyncio.run(run_demand_predictions())
    except Exception as e:
        logger.error(f"Demand Forecast failed: {e}")
        raise self.retry(exc=e)

@celery_app.task(bind=True, name="backend.workers.prediction_worker.run_restock_check")
def task_run_restock_check(self):
    try:
        asyncio.run(run_restock_predictions())
    except Exception as e:
        logger.error(f"Restock Check failed: {e}")
        raise self.retry(exc=e)
