"""Learning System API Endpoints."""
from uuid import UUID
from typing import Dict, Any, List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from backend.database import get_db
from backend.utils.auth import get_current_user
from backend.models.models import Merchant
from backend.services.learning.feedback_logger import log_feedback
from backend.services.learning.merchant_preference_model import get_merchant_weights

router = APIRouter(prefix="/learning", tags=["Learning"])

# ── Schemas ─────────────────────────────────────────────────

class FeedbackCreate(BaseModel):
    recommendation_id: UUID
    accepted: bool
    supplier_selected: UUID = None
    time_to_decision: float = None
    price_difference: float = None

class PreferenceOut(BaseModel):
    merchant_id: UUID
    weights: Dict[str, float]

class ModelStatsOut(BaseModel):
    training_runs: int
    last_run: str = None

# ── Endpoints ──────────────────────────────────────────────

@router.post("/feedback")
async def submit_feedback(
    feedback: FeedbackCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Merchant = Depends(get_current_user),
):
    """Submit feedback on a recommendation."""
    await log_feedback(
        db=db,
        merchant_id=current_user.id,
        recommendation_id=feedback.recommendation_id,
        accepted=feedback.accepted,
        supplier_selected=feedback.supplier_selected,
        time_to_decision=feedback.time_to_decision,
        price_difference=feedback.price_difference
    )
    return {"status": "recorded"}


@router.get("/merchant/preferences", response_model=PreferenceOut)
async def get_my_preferences(
    db: AsyncSession = Depends(get_db),
    current_user: Merchant = Depends(get_current_user),
):
    """Get current learned preference weights."""
    weights = await get_merchant_weights(db, current_user.id)
    return PreferenceOut(merchant_id=current_user.id, weights=weights)


@router.get("/system/model-stats", response_model=ModelStatsOut)
async def get_model_stats(
    db: AsyncSession = Depends(get_db),
    current_user: Merchant = Depends(get_current_user),
):
    """Get global model stats (Admin only placeholder)."""
    # Placeholder logic
    return {"training_runs": 0, "last_run": "Never"}
