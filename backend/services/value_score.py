"""Value Score calculation engine.

score = w1*credit + w2*price + w3*reliability + w4*switching_friction + w5*delivery_speed

Weights are configurable via admin_settings table.
"""
from typing import Optional, Dict
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.models.models import Score, Supplier, AdminSetting


DEFAULT_WEIGHTS = {
    "credit_score": 0.30,
    "price_score": 0.25,
    "reliability_score": 0.20,
    "switching_friction": 0.15,
    "delivery_speed": 0.10,
}


async def get_weights(db: AsyncSession) -> Dict[str, float]:
    """Load weights from admin_settings; fall back to defaults."""
    result = await db.execute(
        select(AdminSetting).where(AdminSetting.key == "value_score_weights")
    )
    setting = result.scalar_one_or_none()
    if setting and isinstance(setting.value, dict):
        return setting.value
    return DEFAULT_WEIGHTS


def calculate_value_score(
    credit_score: float,
    price_score: float,
    reliability_score: float,
    switching_friction: float,
    delivery_speed: float,
    weights: Optional[Dict[str, float]] = None,
) -> float:
    """Compute weighted value score."""
    w = weights or DEFAULT_WEIGHTS
    return (
        w["credit_score"] * credit_score
        + w["price_score"] * price_score
        + w["reliability_score"] * reliability_score
        + w["switching_friction"] * switching_friction
        + w["delivery_speed"] * delivery_speed
    )


def compute_credit_score(supplier: Supplier) -> float:
    """Credit score based on credit terms (higher terms = better for merchant)."""
    terms = supplier.credit_terms or 0
    # Normalize: 0 days → 0.0, 90+ days → 1.0
    return min(terms / 90.0, 1.0)


def compute_price_score(unit_price: float, avg_market_price: float) -> float:
    """Price score — lower than avg means better (higher score)."""
    if avg_market_price <= 0:
        return 0.5
    ratio = unit_price / avg_market_price
    # ratio < 1 means cheaper → score > 0.5
    return max(0, min(1, 1.0 - (ratio - 1.0) * 0.5 + 0.5))


def compute_delivery_speed_score(supplier: Supplier) -> float:
    """Delivery speed — fewer days = higher score."""
    days = supplier.avg_delivery_days or 7
    # Normalize: 1 day → 1.0, 14+ days → 0.0
    return max(0, min(1, 1.0 - (days - 1) / 13.0))


def compute_switching_friction(
    current_supplier: bool,
    invoice_count: int = 0,
) -> float:
    """Switching friction — lower if staying with current supplier."""
    if current_supplier:
        return 0.8  # Low friction
    # More past invoices with this supplier → harder to switch
    return max(0.1, 0.5 - invoice_count * 0.05)


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
    """Compute all sub-scores and create/update a Score record."""
    weights = await get_weights(db)

    cs = compute_credit_score(supplier)
    ps = compute_price_score(unit_price, avg_market_price)
    rs = supplier.reliability_score or 0.5
    sf = compute_switching_friction(is_current_supplier, invoice_count)
    ds = compute_delivery_speed_score(supplier)

    total = calculate_value_score(cs, ps, rs, sf, ds, weights)

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
        score.credit_score = cs
        score.price_score = ps
        score.reliability_score = rs
        score.switching_friction = sf
        score.delivery_speed = ds
        score.total_score = total
        score.weights_snapshot = weights
    else:
        score = Score(
            merchant_id=merchant_id,
            supplier_id=supplier.id,
            product_id=product_id,
            credit_score=cs,
            price_score=ps,
            reliability_score=rs,
            switching_friction=sf,
            delivery_speed=ds,
            total_score=total,
            weights_snapshot=weights,
        )
        db.add(score)

    await db.flush()
    return score
