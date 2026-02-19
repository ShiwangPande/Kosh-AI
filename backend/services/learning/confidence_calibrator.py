"""Confidence Calibrator.

Tracks accuracy of predictions (e.g. savings estimates).
"""
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from backend.models.models import ConfidenceMetric

async def record_confidence_metric(
    db: AsyncSession,
    merchant_id: UUID,
    predicted_savings: float,
    actual_savings: float
):
    """Log prediction accuracy."""
    error = abs(predicted_savings - actual_savings)
    
    metric = ConfidenceMetric(
        merchant_id=merchant_id,
        predicted_savings=predicted_savings,
        actual_savings=actual_savings,
        error_margin=error
    )
    db.add(metric)
    await db.commit()

async def get_calibration_score(db: AsyncSession, merchant_id: UUID) -> float:
    """
    Returns average error margin for recent predictions.
    Lower is better.
    """
    # Simplified: Get average error of last 100 entries
    from sqlalchemy import select, func
    
    result = await db.execute(
        select(func.avg(ConfidenceMetric.error_margin))
        .where(ConfidenceMetric.merchant_id == merchant_id)
        .order_by(ConfidenceMetric.created_at.desc())
        .limit(100)
    )
    avg_error = result.scalar() or 0.0
    return float(avg_error)
