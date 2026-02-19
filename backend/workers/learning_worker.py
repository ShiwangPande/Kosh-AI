"""Learning System Worker."""
import asyncio
from backend.workers.celery_app import celery_app
from backend.services.learning.training_scheduler import run_training_cycle
from celery.utils.log import get_task_logger

logger = get_task_logger(__name__)

@celery_app.task(bind=True, name="backend.workers.learning_worker.train_models")
def train_models_task(self):
    """
    Periodic task to retrain merchant preference models.
    """
    logger.info("Starting model training task")
    try:
        # Run async function in sync celery worker using safe standard
        asyncio.run(run_training_cycle())
        logger.info("Model training task completed successfully")
    except Exception as e:
        logger.error(f"Model training failed: {e}")
        raise self.retry(exc=e, countdown=60, max_retries=3)
