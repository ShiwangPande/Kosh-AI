"""Autonomy Worker."""
import asyncio
from backend.workers.celery_app import celery_app
from backend.services.autonomy.auto_optimizer import run_optimization_cycle

@celery_app.task(bind=True, name="backend.workers.autonomy_worker.run_optimization_cycle")
def task_run_optimization_cycle(self):
    """
    Periodic task: Monitor -> Optimize.
    """
    try:
        asyncio.run(run_optimization_cycle())
    except Exception as e:
        raise self.retry(exc=e)
    
@celery_app.task(bind=True, name="backend.workers.autonomy_worker.evaluate_experiments")
def task_evaluate_experiments(self):
    """
    Periodic task: Check experiment results.
    """
    # Validation placeholder
    pass
