"""Celery application configuration."""
from celery import Celery
from backend.config import get_settings

settings = get_settings()

celery_app = Celery(
    "kosh_ai",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "backend.workers.ocr_worker",
        "backend.workers.learning_worker",
        "backend.workers.network_worker",
        "backend.workers.prediction_worker",
        "backend.workers.autonomy_worker",
    ],
)

from celery.schedules import crontab

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_routes={
        "backend.workers.ocr_worker.*": {"queue": "ocr"},
        "backend.workers.learning_worker.*": {"queue": "learning"},
        "backend.workers.network_worker.*": {"queue": "analytics"},
        "backend.workers.prediction_worker.*": {"queue": "predictions"},
        "backend.workers.autonomy_worker.*": {"queue": "optimization"},
    },
    beat_schedule={
        "train-merchant-models-every-6-hours": {
            "task": "backend.workers.learning_worker.train_models",
            "schedule": crontab(minute=0, hour="*/6"),
        },
        "update-market-prices-30m": {
            "task": "backend.workers.network_worker.update_prices",
            "schedule": crontab(minute="*/30"),
        },
        "update-supplier-benchmarks-hourly": {
            "task": "backend.workers.network_worker.update_benchmarks",
            "schedule": crontab(minute=0, hour="*"),
        },
        "detect-market-trends-hourly": {
            "task": "backend.workers.network_worker.detect_trends",
            "schedule": crontab(minute=0, hour="*"),
        },
        "scan-risk-alerts-hourly": {
            "task": "backend.workers.network_worker.scan_risks",
            "schedule": crontab(minute=0, hour="*"),
        },
        "predict-prices-6h": {
            "task": "backend.workers.prediction_worker.run_price_forecasts",
            "schedule": crontab(minute=0, hour="*/6"),
        },
        "predict-demand-daily": {
            "task": "backend.workers.prediction_worker.run_demand_forecasts",
            "schedule": crontab(minute=0, hour=0),
        },
        "predict-restock-hourly": {
            "task": "backend.workers.prediction_worker.run_restock_check",
            "schedule": crontab(minute=0, hour="*"),
        },
        "run-optimization-cycle-10m": {
            "task": "backend.workers.autonomy_worker.run_optimization_cycle",
            "schedule": crontab(minute="*/10"),
        },
        "evaluate-experiments-hourly": {
            "task": "backend.workers.autonomy_worker.evaluate_experiments",
            "schedule": crontab(minute=30, hour="*"),
        },
    },
)

celery_app.autodiscover_tasks(["backend.workers"])
