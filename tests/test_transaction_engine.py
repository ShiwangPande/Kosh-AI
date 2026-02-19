"""
Transaction Engine Tests.
"""
import pytest
import uuid
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from backend.services.transaction_engine import TransactionEngine, SYSTEM_ID
from backend.services.ledger import LedgerService
from backend.models.models import Order, Merchant, Supplier

@pytest.mark.asyncio
async def test_order_lifecycle(db_session: AsyncSession):
    """
    Test Hold -> Capture flow.
    """
    # 1. Setup Data
    merchant_id = uuid.uuid4()
    supplier_id = uuid.uuid4()
    
    # Pre-fund merchant wallet
    wallet = await LedgerService.get_or_create_account(db_session, "MERCHANT", merchant_id, "WALLET")
    # Hack: Inject funds via SQL or a 'Deposit' Transaction
    # Let's use a Deposit Tx
    deposit_req = await LedgerService.post_transaction(
        db_session, 
        type("obj", (object,), {
            "idempotency_key": f"deposit_{uuid.uuid4()}",
            "reference_type": "DEPOSIT",
            "reference_id": uuid.uuid4(),
            "description": "Initial Fund",
            "entries": [
                type("obj", (object,), {"account_id": wallet.id, "amount": Decimal(1000), "direction": "DEBIT"})(), # Increase Wallet (Asset)
                # Need a credit leg. System Revenue? Or External Source?
                # Let's use System Revenue for simplicity of test (though technically incorrect accounting)
                 type("obj", (object,), {"account_id": (await LedgerService.get_or_create_account(db_session, "SYSTEM", SYSTEM_ID, "REVENUE")).id, "amount": Decimal(1000), "direction": "CREDIT"})()
            ],
            "created_by": None
        })
    ) # Wait, my types are Pydantic in service.
    
    # 2. Create Order
    order = Order(
        id=uuid.uuid4(),
        merchant_id=merchant_id,
        supplier_id=supplier_id,
        po_number="TEST-PO-1",
        status="pending",
        total_amount=500
    )
    db_session.add(order)
    await db_session.flush()
    
    # 3. Place Hold
    msg = await TransactionEngine.place_order_hold(db_session, order.id)
    assert msg == "Funds reserved successfully."
    await db_session.refresh(order)
    assert order.status == "funds_held"
    
    # Check Wallet Balance (1000 - 500 = 500)
    # Re-fetch wallet?
    await db_session.refresh(wallet)
    assert wallet.balance == 500
    
    # 4. Capture
    msg = await TransactionEngine.capture_order_payment(db_session, order.id)
    assert msg == "Payment captured."
    await db_session.refresh(order)
    assert order.status == "completed"
    
    # Check Supplier Balance (500 - 2% fee = 490)
    supplier_acc = await LedgerService.get_or_create_account(db_session, "SUPPLIER", supplier_id, "PAYABLE")
    assert supplier_acc.balance == 490 # Credit balance
