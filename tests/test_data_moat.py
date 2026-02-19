"""
Data Moat Tests.
Verifies that proprietary signals are being captured.
"""
import pytest
import uuid
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.services.action_engine import ActionEngine
from backend.services.risk_engine import RiskEngine
from backend.models.models import TriggerEvent, NegotiationSignal, DecisionContext, RiskDecisionLog, Merchant

@pytest.mark.asyncio
async def test_negotiation_capture(db_session: AsyncSession):
    """Test that free text is captured as a signal."""
    merchant_id = uuid.uuid4()
    
    # 1. Setup Active Trigger
    trigger = TriggerEvent(
        id=uuid.uuid4(),
        merchant_id=merchant_id,
        event_type="TEST",
        priority=2,
        payload={"price": 100},
        status="SENT",
        expires_at=datetime.utcnow() + timedelta(hours=1)
    )
    db_session.add(trigger)
    await db_session.flush()
    
    # 2. Reply with Negotiation Text
    msg = "Too expensive, I need it for 90"
    await ActionEngine.handle_response(db_session, merchant_id, msg)
    
    # 3. Verify Signal Captured
    stmt = select(NegotiationSignal).where(NegotiationSignal.trigger_id == trigger.id)
    signal = (await db_session.execute(stmt)).scalar_one()
    
    assert signal.message_text == msg
    assert signal.price_objection == True # "expensive" detected

@pytest.mark.asyncio
async def test_decision_context_snapshot(db_session: AsyncSession):
    """Test that we snapshot the environment on decision."""
    merchant_id = uuid.uuid4()
    
    # 1. Setup
    trigger = TriggerEvent(
        id=uuid.uuid4(),
        merchant_id=merchant_id,
        event_type="TEST",
        priority=2,
        payload={"price": 500},
        status="SENT",
        expires_at=datetime.utcnow() + timedelta(hours=1)
    )
    db_session.add(trigger)
    from backend.services.ledger import LedgerService
    wallet = await LedgerService.get_or_create_account(db_session, "MERCHANT", merchant_id, "WALLET")
    wallet.balance = 1000
    db_session.add(wallet)
    await db_session.flush()
    
    # 2. Action
    await ActionEngine.handle_response(db_session, merchant_id, "YES")
    
    # 3. Verify Context
    stmt = select(DecisionContext).where(DecisionContext.trigger_id == trigger.id)
    ctx = (await db_session.execute(stmt)).scalar_one()
    
    assert ctx.decision == "ACCEPT"
    assert ctx.price_at_time == 500
    assert ctx.response_time_ms is not None

@pytest.mark.asyncio
async def test_risk_log_persistence(db_session: AsyncSession):
    """Test that risk inputs are logged."""
    merchant_id = uuid.uuid4()
    
    # 1. Evaluate
    await RiskEngine.evaluate_transaction(db_session, merchant_id, 1000, None)
    
    # 2. Verify Log
    stmt = select(RiskDecisionLog).where(RiskDecisionLog.merchant_id == merchant_id)
    log = (await db_session.execute(stmt)).scalar_one()
    
    assert log.risk_score > 0
    assert "velocity_1h" in log.features_json
    assert log.features_json["amount"] == 1000.0
