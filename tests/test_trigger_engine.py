"""
Trigger Engine Tests.
"""
import pytest
import uuid
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from backend.services.trigger_engine import TriggerEngine, EVENT_PRICE_DROP, EVENT_RISK_ALERT

@pytest.mark.asyncio
async def test_trigger_deduplication(db_session: AsyncSession):
    """Test that duplicate triggers are suppressed."""
    merchant_id = uuid.uuid4()
    
    # 1. Emit first trigger
    t1 = await TriggerEngine.emit(
        db_session,
        merchant_id,
        EVENT_PRICE_DROP,
        {"sku": "SUGAR-1KG", "price": 40},
        target_id="SUGAR-1KG"
    )
    assert t1 is not None
    assert t1.priority == 2 # HIGH
    
    # 2. Emit duplicate immediately
    t2 = await TriggerEngine.emit(
        db_session,
        merchant_id,
        EVENT_PRICE_DROP,
        {"sku": "SUGAR-1KG", "price": 38},
        target_id="SUGAR-1KG" # Same target
    )
    assert t2 is None # Should be deduplicated

@pytest.mark.asyncio
async def test_trigger_prioritization(db_session: AsyncSession):
    """Test priority sorting."""
    merchant_id = uuid.uuid4()
    
    # Emit Medium Priority
    await TriggerEngine.emit(db_session, merchant_id, "OPPORTUNITY", {}, "OPP-1")
    
    # Emit Critical Priority
    await TriggerEngine.emit(db_session, merchant_id, EVENT_RISK_ALERT, {}, "RISK-1")
    
    triggers = await TriggerEngine.get_pending_triggers(db_session, merchant_id)
    
    assert len(triggers) == 2
    assert triggers[0].event_type == EVENT_RISK_ALERT # Critical first
    assert triggers[1].event_type == "OPPORTUNITY"

@pytest.mark.asyncio
async def test_trigger_expiration(db_session: AsyncSession):
    """Test that expired triggers are not returned."""
    merchant_id = uuid.uuid4()
    
    # Create expired trigger manually
    t_expired = await TriggerEngine.emit(db_session, merchant_id, "OPPORTUNITY", {}, "EXP-1")
    t_expired.expires_at = datetime.utcnow() - timedelta(hours=1)
    db_session.add(t_expired)
    await db_session.flush()
    
    triggers = await TriggerEngine.get_pending_triggers(db_session, merchant_id)
    assert len(triggers) == 0
