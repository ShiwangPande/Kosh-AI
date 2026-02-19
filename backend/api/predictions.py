"""Prediction API Endpoints."""
from uuid import UUID
from typing import List, Optional
from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel

from backend.database import get_db
from backend.utils.auth import get_current_user
from backend.models.models import PricePrediction, DemandPrediction, RestockPrediction, SupplierRiskPrediction, Merchant

router = APIRouter(prefix="/predict", tags=["Predictive Intelligence"])

# ── Schemas ─────────────────────────────────────────────────

class Explanation(BaseModel):
    factors: List[dict]
    primary_driver: str

class PricePredOut(BaseModel):
    product_id: UUID
    predicted_price: float
    confidence_score: float
    trend_direction: str
    target_date: date
    explanation: dict

class RestockOut(BaseModel):
    product_id: UUID
    recommended_date: date
    recommended_quantity: float
    urgency_score: float
    explanation: dict

# ── Endpoints ──────────────────────────────────────────────

@router.get("/price/{product_id}", response_model=List[PricePredOut])
async def get_price_prediction(
    product_id: UUID,
    city: str,
    db: AsyncSession = Depends(get_db),
    current_user: Merchant = Depends(get_current_user),
):
    """Get price forecast for a product."""
    result = await db.execute(
        select(PricePrediction)
        .where(PricePrediction.product_id == product_id, PricePrediction.city == city)
        .order_by(PricePrediction.created_at.desc())
        .limit(1)
    )
    return result.scalars().all()

@router.get("/restock/{merchant_id}", response_model=List[RestockOut])
async def get_restock_recommendations(
    merchant_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Merchant = Depends(get_current_user),
):
    """Get active restock recommendations."""
    result = await db.execute(
        select(RestockPrediction)
        .where(RestockPrediction.merchant_id == merchant_id)
        .order_by(RestockPrediction.urgency_score.desc())
    )
    return result.scalars().all()
