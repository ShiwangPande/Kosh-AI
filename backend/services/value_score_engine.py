"""Value Score Engine.

Calculates weighted composite score for (Supplier, Product) pair.
Weights are dynamic from DB (admin_settings).

Formula:
  score = w1*credit + w2*price + w3*reliability + w4*switching + w5*delivery

Returns:
    Score object with trace explanation.
"""
import logging
from typing import Dict, Any, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.models.models import AdminSetting, Supplier, Score

logger = logging.getLogger(__name__)

DEFAULT_WEIGHTS = {
    "credit_score": 0.30,
    "price_score": 0.25,
    "reliability_score": 0.20,
    "switching_friction": 0.15,
    "delivery_speed": 0.10,
}


async def get_dynamic_weights(db: AsyncSession) -> Dict[str, float]:
    """Fetch weights from DB, fallback to defaults."""
    try:
        result = await db.execute(
            select(AdminSetting).where(AdminSetting.key == "value_score_weights")
        )
        setting = result.scalar_one_or_none()
        if setting and isinstance(setting.value, dict):
            # Validate keys
            weights = {k: float(v) for k, v in setting.value.items() if k in DEFAULT_WEIGHTS}
            # Fill missing with defaults
            return {**DEFAULT_WEIGHTS, **weights}
    except Exception as e:
        logger.error(f"Failed to load weights: {e}")
    
    return DEFAULT_WEIGHTS


def calculate_subscores(
    supplier: Supplier,
    unit_price: float,
    avg_market_price: float,
    is_current_supplier: bool,
    invoice_count: int,
) -> Dict[str, float]:
    """Compute individual normalized sub-scores (0.0 - 1.0)."""
    
    # 1. Credit Score (0-90 days)
    credit = min((supplier.credit_terms or 0) / 90.0, 1.0)
    
    # 2. Price Score (Lower is better)
    # 1.0 = 50% cheaper, 0.5 = avg, 0.0 = 50% more expensive
    if avg_market_price <= 0:
        price = 0.5
    else:
        ratio = unit_price / avg_market_price
        price = max(0.0, min(1.0, 1.0 - (ratio - 1.0) * 0.5 + 0.5))

    # 3. Reliability (0.0 - 1.0)
    reliability = supplier.reliability_score or 0.5

    # 4. Switching Friction normalization
    # If is_current_supplier = True -> Friction is NOT a penalty, it's a bonus to stay?
    # Requirement: "switching_friction" score.
    # Usually: High friction = Bad for switching TO. Good for staying WITH.
    # Let's align: Higher score = Better option.
    # If option is Current Supplier: Score = 1.0 (No friction).
    # If option is New Supplier: Score = 0.5 (Friction exists).
    
    if is_current_supplier:
        friction = 1.0
    else:
        # Penalize new suppliers slightly
        friction = 0.7

    # 5. Delivery Speed (1 - 14 days)
    days = supplier.avg_delivery_days or 7
    delivery = max(0.0, min(1.0, 1.0 - (days - 1) / 13.0))

    return {
        "credit_score": credit,
        "price_score": price,
        "reliability_score": reliability,
        "switching_friction": friction,
        "delivery_speed": delivery,
    }


async def compute_full_score(
    db: AsyncSession,
    merchant_id: UUID,
    supplier: Supplier,
    product_id: Optional[UUID],
    unit_price: float,
    avg_market_price: float,
    is_current_supplier: bool,
    invoice_count: int = 0,
) -> Score:
    """Compute all sub-scores and create/update a Score record with trace."""
    
    weights = await get_dynamic_weights(db)
    subscores = calculate_subscores(
        supplier, unit_price, avg_market_price, is_current_supplier, invoice_count
    )

    final_score = sum(
        subscores[key] * weights.get(key, 0.0) 
        for key in subscores
    )

    # Upsert score
    existing = await db.execute(
        select(Score).where(
            Score.merchant_id == merchant_id,
            Score.supplier_id == supplier.id,
            Score.product_id == product_id,
        )
    )
    score = existing.scalar_one_or_none()

    if score:
        score.credit_score = subscores["credit_score"]
        score.price_score = subscores["price_score"]
        score.reliability_score = subscores["reliability_score"]
        score.switching_friction = subscores["switching_friction"]
        score.delivery_speed = subscores["delivery_speed"]
        score.total_score = final_score
        score.weights_snapshot = weights
    else:
        score = Score(
            merchant_id=merchant_id,
            supplier_id=supplier.id,
            product_id=product_id,
            credit_score=subscores["credit_score"],
            price_score=subscores["price_score"],
            reliability_score=subscores["reliability_score"],
            switching_friction=subscores["switching_friction"],
            delivery_speed=subscores["delivery_speed"],
            total_score=final_score,
            weights_snapshot=weights,
        )
        db.add(score)

    await db.flush()
    return score
