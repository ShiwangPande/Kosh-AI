"""
Notification Worker Tests.
"""
import pytest
import uuid
import asyncio
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from backend.workers.notification_worker import NotificationWorker
from backend.models.models import TriggerEvent, Merchant

@pytest.mark.asyncio
async def test_worker_priority_ordering(db_session: AsyncSession):
    """Test Critical priority processed before Low."""
    merchant_id = uuid.uuid4()
    
    # 1. Create Low Priority (Old)
    low = TriggerEvent(
        id=uuid.uuid4(),
        merchant_id=merchant_id,
        event_type="LOW",
        priority=4,
        payload={},
        status="PENDING",
        created_at=datetime.utcnow() - timedelta(hours=1)
    )
    
    # 2. Create Critical Priority (New)
    crit = TriggerEvent(
        id=uuid.uuid4(),
        merchant_id=merchant_id,
        event_type="CRIT",
        priority=1,
        payload={},
        status="PENDING",
        created_at=datetime.utcnow()
    )
    
    db_session.add_all([low, crit])
    await db_session.commit()
    
    # 3. Fetch Batch (Simulating Worker Query)
    # We can't easily mock the entire worker loop in unit test without mocking DB
    # So we test the QUERY logic directly
    
    from sqlalchemy import select, or_
    now = datetime.utcnow()
    stmt = select(TriggerEvent).where(
        TriggerEvent.status == "PENDING",
        TriggerEvent.expires_at > now,
        or_(
            TriggerEvent.next_retry_at.is_(None),
            TriggerEvent.next_retry_at <= now
        )
    ).order_by(
        TriggerEvent.priority.asc(),
        TriggerEvent.created_at.asc()
    ).limit(10)
    
    result = await db_session.execute(stmt)
    batch = result.scalars().all()
    
    assert batch[0].id == crit.id
    assert batch[1].id == low.id

@pytest.mark.asyncio
async def test_worker_retry_backoff(db_session: AsyncSession):
    """Test retry count logic."""
    trig = TriggerEvent(
        id=uuid.uuid4(),
        merchant_id=uuid.uuid4(),
        event_type="RETRY_TEST",
        priority=1,
        payload={},
        status="PENDING",
        retry_count=0
    )
    now = datetime.utcnow()
    
    # Simulate Failure 1
    NotificationWorker._handle_failure(trig, now)
    assert trig.retry_count == 1
    assert trig.status == "PENDING"
    assert (trig.next_retry_at - now).seconds == 30
    
    # Simulate Failure 6 (Max 5)
    trig.retry_count = 5
    NotificationWorker._handle_failure(trig, now)
    assert trig.status == "FAILED"
