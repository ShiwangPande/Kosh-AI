"""Merchant Preference Model Manager.

Handles loading/saving of learned weights for each merchant.
"""
from uuid import UUID
from typing import Dict, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.models.models import MerchantPreference

DEFAULT_WEIGHTS = {
    "credit_weight": 0.30,
    "price_weight": 0.25,
    "reliability_weight": 0.20,
    "switching_weight": 0.15,
    "speed_weight": 0.10,
}

async def get_merchant_weights(db: AsyncSession, merchant_id: UUID) -> Dict[str, float]:
    """Get learned weights or defaults."""
    result = await db.execute(
        select(MerchantPreference).where(MerchantPreference.merchant_id == merchant_id)
    )
    pref = result.scalar_one_or_none()
    
    if not pref:
        return DEFAULT_WEIGHTS
        
    return {
        "credit_weight": pref.credit_weight,
        "price_weight": pref.price_weight,
        "reliability_weight": pref.reliability_weight,
        "switching_weight": pref.switching_weight,
        "speed_weight": pref.speed_weight,
    }

async def update_merchant_weights(
    db: AsyncSession, 
    merchant_id: UUID, 
    new_weights: Dict[str, float]
):
    """Update weights for a merchant."""
    result = await db.execute(
        select(MerchantPreference).where(MerchantPreference.merchant_id == merchant_id)
    )
    pref = result.scalar_one_or_none()
    
    if not pref:
        pref = MerchantPreference(merchant_id=merchant_id)
        db.add(pref)
    
    pref.credit_weight = new_weights.get("credit_weight", pref.credit_weight)
    pref.price_weight = new_weights.get("price_weight", pref.price_weight)
    pref.reliability_weight = new_weights.get("reliability_weight", pref.reliability_weight)
    pref.switching_weight = new_weights.get("switching_weight", pref.switching_weight)
    pref.speed_weight = new_weights.get("speed_weight", pref.speed_weight)
    
    pref.version += 1
    # pref.last_trained_at update handled by TimestampMixin or explicit set? 
    # TimestampMixin handles updated_at. We need explicit last_trained_at.
    # We will let the caller or db handle it, but TimestampMixin doesn't have last_trained_at.
    # We should import func or datetime.
    from sqlalchemy.sql import func
    pref.last_trained_at = func.now()
    
    await db.commit()
