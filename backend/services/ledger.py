"""
Immutable Ledger Service.

Handles all financial transactions with strict double-entry accounting.
Enforces:
- Atomicity (all or nothing)
- Consistency (sum(debits) == sum(credits))
- Isolation (row locking on accounts)
- Durability (DB commit)
"""
import uuid
from decimal import Decimal
from typing import List, Optional
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError

from backend.models.models import LedgerAccount, LedgerTransaction, LedgerEntry
from pydantic import BaseModel

class EntryRequest(BaseModel):
    account_id: uuid.UUID
    amount: Decimal
    direction: str # DEBIT or CREDIT

class TransactionRequest(BaseModel):
    idempotency_key: str
    reference_type: str
    reference_id: uuid.UUID
    description: str
    entries: List[EntryRequest]
    created_by: Optional[uuid.UUID] = None


class LedgerService:
    
    @staticmethod
    async def get_or_create_account(
        db: AsyncSession,
        owner_type: str,
        owner_id: uuid.UUID,
        account_type: str,
        currency: str = "INR"
    ) -> LedgerAccount:
        """
        Get existing account or create a new one safely.
        """
        query = select(LedgerAccount).where(
            LedgerAccount.owner_id == owner_id,
            LedgerAccount.owner_type == owner_type,
            LedgerAccount.account_type == account_type,
            LedgerAccount.currency == currency
        )
        result = await db.execute(query)
        account = result.scalar_one_or_none()
        
        if not account:
            account = LedgerAccount(
                owner_type=owner_type,
                owner_id=owner_id,
                account_type=account_type,
                currency=currency,
                balance=0
            )
            db.add(account)
            await db.flush() # Generate ID but don't commit global transaction
            
        return account

    @staticmethod
    async def post_transaction(db: AsyncSession, request: TransactionRequest) -> LedgerTransaction:
        """
        Execute a double-entry financial transaction.
        
        Steps:
        1. Check Idempotency
        2. Validate Balance (Dr == Cr)
        3. Lock Accounts & Update Balances
        4. Create Transaction & Entries
        """
        
        # 1. Idempotency Check
        existing = await db.execute(
            select(LedgerTransaction).where(LedgerTransaction.idempotency_key == request.idempotency_key)
        )
        if existing.scalar_one_or_none():
            raise ValueError(f"Transaction with idempotency_key {request.idempotency_key} already exists.")

        # 2. Validate Double Entry
        total_debit = sum(e.amount for e in request.entries if e.direction == "DEBIT")
        total_credit = sum(e.amount for e in request.entries if e.direction == "CREDIT")
        
        if total_debit != total_credit:
            raise ValueError(f"Transaction Unbalanced: Debits {total_debit} != Credits {total_credit}")
            
        if total_debit <= 0:
             raise ValueError("Transaction amount must be positive.")

        # 3. Create Transaction Record
        transaction = LedgerTransaction(
            idempotency_key=request.idempotency_key,
            reference_type=request.reference_type,
            reference_id=request.reference_id,
            description=request.description,
            created_by=request.created_by,
            status="posted"
        )
        db.add(transaction)
        await db.flush() # Get ID

        # 4. Process Entries
        # Sort by account_id to prevent deadlocks during locking
        sorted_entries = sorted(request.entries, key=lambda x: x.account_id)
        
        for entry_req in sorted_entries:
            # Lock Account Row (FOR UPDATE)
            # We must re-fetch strictly to lock
            query = select(LedgerAccount).where(LedgerAccount.id == entry_req.account_id).with_for_update()
            result = await db.execute(query)
            account = result.scalar_one()
            
            if account.is_frozen:
                 raise ValueError(f"Account {account.id} is frozen.")

            # Update Balance
            # Asset/Expense (Debit increases)
            # Liability/Equity/Income (Credit increases)
            # For simplicity, we store 'signed' balance logic:
            # WALLET (Asset): Debit (+), Credit (-)
            # PAYABLE (Liability): Credit (+), Debit (-)
            # RECEIVABLE (Asset): Debit (+), Credit (-)
            # REVENUE (Income): Credit (+), Debit (-)
            # EXPENSE (Expense): Debit (+), Credit (-)
            
            delta = entry_req.amount
            
            # Logic: 
            # If Asset/Expense: Balance = Dr - Cr
            # If Liability/Income: Balance = Cr - Dr
            # For generic storage, we can just say:
            # Debit adds to balance, Credit subtracts? 
            # NO. That's confusing for Liabilities.
            # Let's standardise: 
            # ACCOUNTS TRACK "NET VALUE" from their own perspective.
            # Wallet: Positive is good (You have money). Debit increases it.
            # Payable: Positive is bad (You owe money). Credit increases it.
            
            if account.account_type in ["WALLET", "RECEIVABLE", "EXPENSE"]:
                 if entry_req.direction == "DEBIT":
                     balance_change = delta
                 else:
                     balance_change = -delta
            else: # PAYABLE, REVENUE, EQUITY, CREDIT
                 if entry_req.direction == "CREDIT":
                     balance_change = delta
                 else:
                     balance_change = -delta
            
            account.balance += balance_change
            
            # Create Entry
            entry = LedgerEntry(
                transaction_id=transaction.id,
                account_id=account.id,
                direction=entry_req.direction,
                amount=entry_req.amount,
                balance_after=account.balance
            )
            db.add(entry)
            
        return transaction
