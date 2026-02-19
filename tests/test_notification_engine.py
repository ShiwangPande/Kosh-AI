"""
Notification Engine Tests.
"""
import pytest
import uuid
from datetime import datetime, time, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from backend.services.notification_engine import NotificationEngine
from backend.models.models import Merchant, TriggerEvent, NotificationLog

@pytest.mark.asyncio
async def test_quiet_hours_skip(db_session: AsyncSession):
    """Test that non-critical triggers are skipped during quiet hours."""
    merchant_id = uuid.uuid4()
    
    # 1. Setup Merchant with Quiet Hours (covering "now")
    # Hack: Make quiet hours 00:00 to 23:59
    merchant = Merchant(
        id=merchant_id,
        email=f"quiet_{uuid.uuid4()}@test.com",
        business_name="Quiet Shop",
        phone="1234567890",
        password_hash="pw",
        quiet_hours_start=time(0, 0),
        quiet_hours_end=time(23, 59)
    )
    db_session.add(merchant)
    await db_session.flush()
    
    # 2. Create Low Priority Trigger
    trigger = TriggerEvent(
        id=uuid.uuid4(),
        merchant_id=merchant_id,
        event_type="PROMO",
        priority=3, # Low
        payload={},
        status="PENDING"
    )
    db_session.add(trigger)
    await db_session.flush()
    
    # 3. Attempt Delivery
    await NotificationEngine.deliver_trigger(db_session, trigger.id)
    
    # 4. Verify NOT Sent
    await db_session.refresh(trigger)
    assert trigger.status == "PENDING" 

@pytest.mark.asyncio
async def test_rate_limit(db_session: AsyncSession):
    """Test max 3 notifications per hour."""
    merchant_id = uuid.uuid4()
    merchant = Merchant(
        id=merchant_id,
        email=f"spam_{uuid.uuid4()}@test.com",
        business_name="Spam Shop",
        password_hash="pw",
        phone="123"
    )
    db_session.add(merchant)
    await db_session.flush()
    
    # 1. Create 3 prior logs
    for i in range(3):
        db_session.add(NotificationLog(
            merchant_id=merchant_id,
            status="SENT",
            sent_at=datetime.utcnow() 
        ))
    await db_session.flush()
    
    # 2. Create new trigger
    trigger = TriggerEvent(
        id=uuid.uuid4(),
        merchant_id=merchant_id,
        event_type="PROMO",
        priority=3,
        payload={},
        status="PENDING"
    )
    db_session.add(trigger)
    
    # 3. Attempt Delivery -> Should Rate Limit
    await NotificationEngine.deliver_trigger(db_session, trigger.id)
    
    await db_session.refresh(trigger)
    assert trigger.status == "PENDING"
