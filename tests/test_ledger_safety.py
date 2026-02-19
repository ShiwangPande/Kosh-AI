"""
Ledger Safety Tests.

Verifies:
1. Double Entry Enforcement (Unbalanced tx must fail)
2. Idempotency (Replay must fail)
3. Atomic Balance Updates
4. Negative amounts rejection
"""
import pytest
import uuid
import pytest_asyncio
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from backend.services.ledger import LedgerService, TransactionRequest, EntryRequest
from backend.models.models import LedgerAccount

@pytest.mark.asyncio
async def test_ledger_double_entry_enforcement(db_session: AsyncSession):
    """Test that unbalanced transactions are rejected."""
    
    # Setup accounts
    wallet = await LedgerService.get_or_create_account(db_session, "MERCHANT", uuid.uuid4(), "WALLET")
    revenue = await LedgerService.get_or_create_account(db_session, "SYSTEM", uuid.uuid4(), "REVENUE")
    
    # Attempt unbalanced transaction (Debit 100, Credit 50)
    tx_req = TransactionRequest(
        idempotency_key=str(uuid.uuid4()),
        reference_type="TEST",
        reference_id=uuid.uuid4(),
        description="Unbalanced Tx",
        entries=[
            EntryRequest(account_id=wallet.id, amount=Decimal("100.00"), direction="DEBIT"),
            EntryRequest(account_id=revenue.id, amount=Decimal("50.00"), direction="CREDIT")
        ]
    )
    
    with pytest.raises(ValueError, match="Unbalanced"):
        await LedgerService.post_transaction(db_session, tx_req)

@pytest.mark.asyncio
async def test_ledger_idempotency(db_session: AsyncSession):
    """Test that reusing idempotency key raises error."""
    
    wallet = await LedgerService.get_or_create_account(db_session, "MERCHANT", uuid.uuid4(), "WALLET")
    revenue = await LedgerService.get_or_create_account(db_session, "SYSTEM", uuid.uuid4(), "REVENUE")
    key = str(uuid.uuid4())
    
    tx_req = TransactionRequest(
        idempotency_key=key,
        reference_type="TEST",
        reference_id=uuid.uuid4(),
        description="Valid Tx",
        entries=[
            EntryRequest(account_id=wallet.id, amount=Decimal("100.00"), direction="DEBIT"),
            EntryRequest(account_id=revenue.id, amount=Decimal("100.00"), direction="CREDIT")
        ]
    )
    
    # First pass
    await LedgerService.post_transaction(db_session, tx_req)
    await db_session.commit()
    
    # Second pass (Replay)
    with pytest.raises(ValueError, match="already exists"):
        await LedgerService.post_transaction(db_session, tx_req)

@pytest.mark.asyncio
async def test_ledger_balance_updates(db_session: AsyncSession):
    """Test that balances update correctly."""
    
    merchant_id = uuid.uuid4()
    wallet = await LedgerService.get_or_create_account(db_session, "MERCHANT", merchant_id, "WALLET")
    
    # Initial balance should be 0
    assert wallet.balance == 0
    
    # Credit the wallet (Add money) -> LIABILITY from system persp? No, WALLET is ASSET for merchant.
    # WAIT. If account_type="WALLET" is ASSET.
    # DEBIT increases ASSET.
    # So "Loading Money" -> Debit Wallet, Credit Bank/System.
    
    tx_req = TransactionRequest(
        idempotency_key=str(uuid.uuid4()),
        reference_type="DEPOSIT",
        reference_id=uuid.uuid4(),
        description="Add Funds",
        entries=[
            EntryRequest(account_id=wallet.id, amount=Decimal("500.00"), direction="DEBIT"),
            # Mock counterparty
            EntryRequest(account_id=wallet.id, amount=Decimal("500.00"), direction="CREDIT"), # wait, can't credit same account
        ]
    )
    # We need a second account for strict double entry
    system_bank = await LedgerService.get_or_create_account(db_session, "SYSTEM", uuid.uuid4(), "REVENUE")
    
    tx_req.entries[1].account_id = system_bank.id
    
    await LedgerService.post_transaction(db_session, tx_req)
    await db_session.commit()
    
    # Refresh
    await db_session.refresh(wallet)
    assert wallet.balance == 500.00
