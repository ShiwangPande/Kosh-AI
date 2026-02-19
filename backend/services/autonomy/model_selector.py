"""Model Selector & Experiment Engine.

Manages Model Registry and A/B Tests.
"""
import random
from uuid import UUID
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.models.models import ModelRegistry, Experiment

class ModelSelector:
    
    @staticmethod
    async def get_active_model(db: AsyncSession) -> ModelRegistry:
        """Return currently active model."""
        res = await db.execute(
            select(ModelRegistry).where(ModelRegistry.status == "ACTIVE").limit(1)
        )
        return res.scalar()

class ExperimentEngine:
    
    @staticmethod
    async def get_model_for_merchant(db: AsyncSession, merchant_id: UUID) -> ModelRegistry:
        """
        Determine if merchant should see Experimental Model or Control.
        Check active experiments.
        """
        # 1. Check Running Experiment
        exp_res = await db.execute(
            select(Experiment).where(Experiment.status == "RUNNING").limit(1)
        )
        exp = exp_res.scalar()
        
        if not exp:
            return await ModelSelector.get_active_model(db)
            
        # 2. Traffic Split Hashing
        # Deterministic based on merchant ID hash
        # Simple integer based logic for demo
        h_val = int(merchant_id.int) % 100
        cutoff = exp.traffic_split * 100
        
        model_id = exp.candidate_model_id if h_val < cutoff else exp.control_model_id
        
        res = await db.execute(
            select(ModelRegistry).where(ModelRegistry.id == model_id)
        )
        return res.scalar()

    @staticmethod
    async def start_experiment(db: AsyncSession, candidate_id: UUID, split: float = 0.1):
        """Start new A/B test."""
        if split > 0.3:
            raise ValueError("Max exposure is 30%")
            
        # Get active as control
        control = await ModelSelector.get_active_model(db)
        if not control:
             raise ValueError("No active baseline")
             
        exp = Experiment(
            name=f"Exp vs {control.version}",
            status="RUNNING",
            control_model_id=control.id,
            candidate_model_id=candidate_id,
            traffic_split=split,
            start_time=datetime.utcnow()
        )
        db.add(exp)
        await db.commit()
