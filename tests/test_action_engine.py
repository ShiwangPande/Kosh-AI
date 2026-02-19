"""
Action Engine Tests.
"""
import pytest
import uuid
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from backend.services.action_engine import ActionEngine
from backend.services.trigger_engine import EVENT_PRICE_DROP
from backend.models.models import TriggerEvent, UserAction, Order

@pytest.mark.asyncio
async def test_action_flow_yes(db_session: AsyncSession):
    """Test YES response flow."""
    merchant_id = uuid.uuid4()
    
    # 1. Create PRE-EXISTING Order (Draft)
    order = Order(
        id=uuid.uuid4(),
        merchant_id=merchant_id,
        status="pending",
        total_amount=500,
        po_number="PO-AUTO-1"
    )
    db_session.add(order)
    
    # 2. Create Trigger pointing to this Order
    trigger = TriggerEvent(
        id=uuid.uuid4(),
        merchant_id=merchant_id,
        event_type=EVENT_PRICE_DROP,
        priority=2,
        payload={"order_id": str(order.id), "sku": "TEST"},
        status="SENT",
        expires_at=datetime.utcnow() + timedelta(hours=1)
    )
    db_session.add(trigger)
    await db_session.flush()
    
    # Needs Wallet for transaction engine to work (it checks balance)
    # We mock TransactionEngine call? Or just let it fail/succeed if balance is checked.
    # To make integration test real, let's give merchant money.
    from backend.services.ledger import LedgerService
    wallet = await LedgerService.get_or_create_account(db_session, "MERCHANT", merchant_id, "WALLET")
    wallet.balance = 1000
    db_session.add(wallet)
    await db_session.flush()

    # 3. Simulate User Reply "YES"
    response_msg = await ActionEngine.handle_response(db_session, merchant_id, "YES")
    
    assert "Order placed successfully" in response_msg
    
    # 4. Verify Action Recorded
    import sqlalchemy
    stmt = sqlalchemy.select(UserAction).where(UserAction.trigger_id == trigger.id)
    actions = (await db_session.execute(stmt)).scalars().all()
    assert len(actions) == 1
    assert actions[0].action_type == "ACCEPT"
    assert actions[0].status == "EXECUTED"

@pytest.mark.asyncio
async def test_action_idempotency(db_session: AsyncSession):
    """Test double reply prevention."""
    merchant_id = uuid.uuid4()
    trigger = TriggerEvent(
        id=uuid.uuid4(),
        merchant_id=merchant_id,
        event_type="TEST",
        priority=2,
        payload={},
        status="SENT",
        expires_at=datetime.utcnow() + timedelta(hours=1)
    )
    db_session.add(trigger)
    await db_session.flush()
    
    # First Reply
    await ActionEngine.handle_response(db_session, merchant_id, "NO")
    
    # Second Reply
    msg = await ActionEngine.handle_response(db_session, merchant_id, "NO")
    assert "already responded" in msg

@pytest.mark.asyncio
async def test_expired_trigger(db_session: AsyncSession):
    """Test reply to expired trigger."""
    merchant_id = uuid.uuid4()
    trigger = TriggerEvent(
        id=uuid.uuid4(),
        merchant_id=merchant_id,
        event_type="TEST",
        priority=2,
        payload={},
        status="SENT",
        expires_at=datetime.utcnow() - timedelta(hours=1) # Expired
    )
    db_session.add(trigger)
    await db_session.flush()
    
    msg = await ActionEngine.handle_response(db_session, merchant_id, "YES")
    assert "offer has expired" in msg
