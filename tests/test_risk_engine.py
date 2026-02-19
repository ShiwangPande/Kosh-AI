"""
Risk Engine Safety Tests.
"""
import pytest
import uuid
from decimal import Decimal
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from backend.services.risk_engine import RiskEngine
from backend.services.transaction_engine import TransactionEngine
from backend.models.models import Order
from backend.services.ledger import LedgerService, SYSTEM_ID

@pytest.mark.asyncio
async def test_risk_high_value_block(db_session: AsyncSession):
    """Test that high value transactions are flagged/blocked."""
    
    # 1. Use RiskEngine directly
    decision = await RiskEngine.evaluate_transaction(
        db_session, 
        uuid.uuid4(), 
        Decimal("60000.00"), # > 50k
        None
    )
    assert decision.decision == "REVIEW" # Or BLOCK depending on score? Base 10 + 40 = 50 -> REVIEW
    assert "High Value" in decision.reasons[0]

@pytest.mark.asyncio
async def test_risk_velocity_block(db_session: AsyncSession):
    """Test velocity limit."""
    merchant_id = uuid.uuid4()
    
    # Create 11 orders in last hour
    for i in range(11):
        order = Order(
            id=uuid.uuid4(),
            merchant_id=merchant_id,
            total_amount=100,
            created_at=datetime.utcnow()
        )
        db_session.add(order)
    await db_session.flush()
    
    decision = await RiskEngine.evaluate_transaction(
        db_session,
        merchant_id,
        Decimal("100.00"),
        None
    )
    # Score: 10 (Base) + 50 (Velocity) = 60 -> REVIEW
    assert decision.decision == "REVIEW"
    assert "High Velocity" in decision.reasons[0]

@pytest.mark.asyncio
async def test_transaction_engine_integration(db_session: AsyncSession):
    """Test TransactionEngine enforces Risk Gate."""
    merchant_id = uuid.uuid4()
    supplier_id = uuid.uuid4()
    
    # Fund Wallet
    wallet = await LedgerService.get_or_create_account(db_session, "MERCHANT", merchant_id, "WALLET")
    wallet.balance = 100000
    db_session.add(wallet)
    
    # Create High Risk Order (> 50k)
    order = Order(
        id=uuid.uuid4(),
        merchant_id=merchant_id,
        supplier_id=supplier_id,
        po_number="RISKY-1",
        status="pending",
        total_amount=60000 
    )
    db_session.add(order)
    await db_session.flush()
    
    # Attempt Hold -> Should Fail due to REVIEW/BLOCK
    with pytest.raises(ValueError, match="MANUAL REVIEW"):
         await TransactionEngine.place_order_hold(db_session, order.id)
         
    # Verify State Remains Pending (No Money Moved/Locked)
    await db_session.refresh(order)
    assert order.status == "pending"
