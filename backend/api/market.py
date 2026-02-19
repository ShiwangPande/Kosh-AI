"""Market Intelligence API."""
from uuid import UUID
from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel

from backend.database import get_db
from backend.utils.auth import get_current_user
from backend.models.models import AggregatedPrice, SupplierBenchmark, MarketTrend, RiskAlert, Merchant

router = APIRouter(prefix="/market", tags=["Market Intelligence"])

# ── Schemas ─────────────────────────────────────────────────

class MarketPriceOut(BaseModel):
    product_id: UUID
    city: str
    median_price: float
    p25_price: float
    p75_price: float
    volatility: float
    time_window: datetime

class SupplierRankingOut(BaseModel):
    supplier_id: UUID
    rank: int
    score: float # Computed composite
    price_competitiveness: float
    delivery_reliability: float

class TrendOut(BaseModel):
    trend_type: str
    direction: str
    magnitude: float
    city: str
    product_id: UUID

class AlertOut(BaseModel):
    alert_type: str
    severity: str
    description: str
    created_at: datetime

# ── Endpoints ──────────────────────────────────────────────

@router.get("/price/{product_id}", response_model=List[MarketPriceOut])
async def get_market_price(
    product_id: UUID,
    city: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: Merchant = Depends(get_current_user),
):
    """Get aggregated market price history for a product."""
    query = select(AggregatedPrice).where(AggregatedPrice.product_id == product_id)
    if city:
        query = query.where(AggregatedPrice.city == city)
    
    query = query.order_by(AggregatedPrice.time_window.desc()).limit(30)
    result = await db.execute(query)
    prices = result.scalars().all()
    return prices

@router.get("/suppliers/{city}", response_model=List[SupplierRankingOut])
async def get_supplier_rankings(
    city: str,
    db: AsyncSession = Depends(get_db),
    current_user: Merchant = Depends(get_current_user),
):
    """Get top suppliers in a city."""
    result = await db.execute(
        select(SupplierBenchmark)
        .where(SupplierBenchmark.city == city)
        .order_by(SupplierBenchmark.network_rank.asc())
    )
    benchmarks = result.scalars().all()
    
    return [
        SupplierRankingOut(
            supplier_id=b.supplier_id,
            rank=b.network_rank,
            score=(b.price_competitiveness + b.delivery_reliability + b.fulfillment_accuracy + b.merchant_retention)/4,
            price_competitiveness=b.price_competitiveness,
            delivery_reliability=b.delivery_reliability
        )
        for b in benchmarks
    ]

@router.get("/trends", response_model=List[TrendOut])
async def get_market_trends(
    city: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: Merchant = Depends(get_current_user),
):
    """Get recent market trends."""
    query = select(MarketTrend).order_by(MarketTrend.detected_at.desc()).limit(20)
    if city:
        query = query.where(MarketTrend.city == city)
        
    result = await db.execute(query)
    return result.scalars().all()

@router.get("/alerts", response_model=List[AlertOut])
async def get_risk_alerts(
    db: AsyncSession = Depends(get_db),
    current_user: Merchant = Depends(get_current_user),
):
    """Get active risk alerts."""
    result = await db.execute(
        select(RiskAlert).where(RiskAlert.is_active == True).order_by(RiskAlert.created_at.desc())
    )
    return result.scalars().all()
