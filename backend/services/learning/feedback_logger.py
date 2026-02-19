"""Feedback Logger Service.

Records merchant interactions with recommendations.
Data used for training preference models.
"""
from uuid import UUID
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from backend.models.models import RecommendationFeedback

async def log_feedback(
    db: AsyncSession,
    merchant_id: UUID,
    recommendation_id: UUID,
    accepted: bool,
    supplier_selected: Optional[UUID] = None,
    time_to_decision: Optional[float] = None,
    price_difference: Optional[float] = None,
):
    """Log feedback entry."""
    entry = RecommendationFeedback(
        merchant_id=merchant_id,
        recommendation_id=recommendation_id,
        accepted=accepted,
        supplier_selected=supplier_selected,
        time_to_decision=time_to_decision,
        price_difference=price_difference
    )
    db.add(entry)
    await db.commit()
