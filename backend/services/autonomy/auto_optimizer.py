"""Auto Optimizer Orchestrator.

Central engine for autonomous optimization.
Runs monitoring, tuning, and safety checks.
"""
import logging
from backend.services.autonomy.performance_monitor import PerformanceMonitor
from backend.services.autonomy.weight_tuner import WeightTuner
from backend.services.autonomy.rollback_manager import RollbackManager
from backend.services.learning.merchant_preference_model import get_merchant_weights, update_merchant_weights
from backend.models.models import OptimizationLog
from sqlalchemy.ext.asyncio import AsyncSession
from backend.database import SessionLocal

logger = logging.getLogger(__name__)

async def run_optimization_cycle():
    """
    Main Loop: Monitor -> Evaluate -> Optimize/Rollback.
    """
    async with SessionLocal() as db:
        # 1. Monitor
        metrics = await PerformanceMonitor.capture_metrics(db)
        
        # 2. Check for Drops
        # Acceptance Rate
        drop, baseline, dev = await PerformanceMonitor.check_performance_drop(db, "acceptance_rate", metrics["acceptance_rate"])
        
        if drop:
            logger.warning(f"Performance Drop Detected! {dev*100}% below baseline.")
            
            # Safety Check: If drop is severe (>20%), Rollback
            if dev < -0.20:
                await RollbackManager.rollback_weights(db)
                return

            # Otherwise, Attempt Tuning
            # Get global or specific merchant weights (simplified to global for demo)
            # We would iterate metrics per merchant in real system
            # Here we tune a hypothetical "global" preference
            
            # Mock getting some weights to tune
            # current_weights = await get_merchant_weights(db, some_id) 
            # new_weights = WeightTuner.adjust_weights(current_weights, "acceptance_rate")
            # await update_merchant_weights(db, some_id, new_weights)
            
            db.add(OptimizationLog(
                action_type="WEIGHT_TUNE_TRIGGERED",
                status="COMPLETED", 
                details={"reason": "Acceptance Rate Drop", "deviation": dev}
            ))
            await db.commit()
            
        else:
            logger.info("System stable. No optimization needed.")
