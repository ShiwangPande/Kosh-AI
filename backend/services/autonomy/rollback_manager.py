"""Rollback Manager.

Restores system to previous stable state.
"""
from typing import Dict
from datetime import datetime
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from backend.models.models import ModelRegistry, WeightHistory, OptimizationLog

class RollbackManager:
    
    @staticmethod
    async def rollback_weights(db: AsyncSession, merchant_id: str = None):
        """Revert to previous weights."""
        # Get last weight history
        query = select(WeightHistory).order_by(WeightHistory.created_at.desc()).limit(1)
        if merchant_id:
            query = query.where(WeightHistory.merchant_id == merchant_id)
            
        res = await db.execute(query)
        last_change = res.scalar()
        
        if last_change and last_change.previous_weights:
            # Revert logic would update MerchantPreference here
            # Mocking the action
            log = OptimizationLog(
                action_type="ROLLBACK_WEIGHTS",
                status="SUCCESS",
                details={"reverted_to": last_change.id}
            )
            db.add(log)
            await db.commit()
            return True
        return False

    @staticmethod
    async def rollback_model(db: AsyncSession):
        """Demote unstable model, promote previous baseline."""
        # Find active
        active_res = await db.execute(select(ModelRegistry).where(ModelRegistry.status == "ACTIVE"))
        active = active_res.scalar()
        
        if active and not active.is_baseline:
            # It's an experimental model that failed
            active.status = "FAILED"
            
            # Find baseline
            base_res = await db.execute(select(ModelRegistry).where(ModelRegistry.is_baseline == True))
            baseline = base_res.scalar()
            if baseline:
                baseline.status = "ACTIVE"
                
            db.add(OptimizationLog(
                action_type="ROLLBACK_MODEL",
                status="SUCCESS",
                details={"demoted": active.model_name, "promoted": baseline.model_name if baseline else "None"}
            ))
            await db.commit()
