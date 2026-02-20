"""Autonomy API Endpoints."""
from uuid import UUID
from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel

from backend.database import get_db
from backend.utils.auth import get_current_user
from backend.models.models import SystemMetric, ModelRegistry, Experiment, OptimizationLog, Merchant

router = APIRouter(prefix="/system", tags=["Autonomous Optimization"])

# ── Schemas ─────────────────────────────────────────────────

class MetricOut(BaseModel):
    metric_name: str
    value: float
    window_end: datetime

class ModelOut(BaseModel):
    model_name: str
    version: str
    status: str
    is_baseline: bool
    performance_score: Optional[float]

    model_config = {"protected_namespaces": ()}


class ExperimentOut(BaseModel):
    name: str
    status: str
    traffic_split: float

class LogOut(BaseModel):
    action_type: str
    status: str
    created_at: datetime
    details: dict

# ── Endpoints ──────────────────────────────────────────────

@router.get("/metrics", response_model=List[MetricOut])
async def get_system_metrics(
    db: AsyncSession = Depends(get_db),
    current_user: Merchant = Depends(get_current_user),
):
    """Get latest system KPIs."""
    result = await db.execute(
        select(SystemMetric).order_by(SystemMetric.created_at.desc()).limit(20)
    )
    return result.scalars().all()

@router.get("/models", response_model=List[ModelOut])
async def get_model_registry(
    db: AsyncSession = Depends(get_db),
    current_user: Merchant = Depends(get_current_user),
):
    """Get deployed models."""
    result = await db.execute(select(ModelRegistry).order_by(ModelRegistry.created_at.desc()))
    return result.scalars().all()

@router.get("/experiments", response_model=List[ExperimentOut])
async def get_active_experiments(
    db: AsyncSession = Depends(get_db),
    current_user: Merchant = Depends(get_current_user),
):
    """Get running experiments."""
    result = await db.execute(select(Experiment).where(Experiment.status == "RUNNING"))
    return result.scalars().all()

@router.get("/status", response_model=List[LogOut])
async def get_optimization_status(
    db: AsyncSession = Depends(get_db),
    current_user: Merchant = Depends(get_current_user),
):
    """Get recent optimization actions."""
    result = await db.execute(select(OptimizationLog).order_by(OptimizationLog.created_at.desc()).limit(10))
    return result.scalars().all()
