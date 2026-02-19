"""
Transaction Engine Service.

Orchestrates complex financial flows by chaining atomic Ledger transactions.
Acts as the "Financial Controller" ensuring business logic constraints (holds, risk, fees)
before moving money.
"""
import uuid
from decimal import Decimal
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.models.models import Order, Merchant, Supplier
from backend.services.ledger import LedgerService, TransactionRequest, EntryRequest

# Order States
ORDER_STATUS_DRAFT = "draft"
ORDER_STATUS_PENDING_FUNDS = "pending_funds"
ORDER_STATUS_FUNDS_HELD = "funds_held"
ORDER_STATUS_APPROVED = "approved"
ORDER_STATUS_SHIPPED = "shipped"
ORDER_STATUS_COMPLETED = "completed"
ORDER_STATUS_CANCELLED = "cancelled"

# Ledger Account Types
ACC_WALLET = "WALLET"
ACC_HOLD = "HOLD"
ACC_PAYABLE = "PAYABLE"
ACC_REVENUE = "REVENUE"

# Identities
SYSTEM_ID = uuid.UUID("00000000-0000-0000-0000-000000000000") # Virtual System ID

class TransactionEngine:
    
    @staticmethod
    async def place_order_hold(db: AsyncSession, order_id: uuid.UUID) -> str:
        """
        Reserve funds for an order.
        1. Validates Order Status.
        2. Checks Merchant Balance.
        3. Moves funds: Merchant Wallet -> Global Hold Account.
        """
        from backend.services.risk_engine import RiskEngine

        # 1. Fetch Order
        result = await db.execute(select(Order).where(Order.id == order_id))
        order = result.scalar_one_or_none()
        
        if not order:
            raise ValueError(f"Order {order_id} not found.")
            
        if order.status != "pending": # Assuming 'pending' is the initial state from API
            # Allow retry if already funds_held? No, idempotency handles at ledger layer.
            # But let's be strict on state transitions.
            if order.status == ORDER_STATUS_FUNDS_HELD:
                return "Funds already held."
            raise ValueError(f"Order must be in 'pending' state, is '{order.status}'.")

        amount = Decimal(str(order.total_amount))
        merchant_id = order.merchant_id
        
        # 1b. RISK GATE (Enforcement Point)
        risk_decision = await RiskEngine.evaluate_transaction(
            db, merchant_id, amount, order.supplier_id
        )
        
        # Log Audit (TODO: Separate Audit Log Table for Risk)
        # For now, we block on non-APPROVE
        if risk_decision.decision == "BLOCK":
             raise ValueError(f"Transaction BLOCKED by Risk Engine (Score: {risk_decision.score}). Reasons: {risk_decision.reasons}")
             
        if risk_decision.decision == "REVIEW":
             # In future, queue for manual review. For now, block to be safe.
             raise ValueError(f"Transaction requires MANUAL REVIEW (Score: {risk_decision.score}). Reasons: {risk_decision.reasons}")

        # 2. Setup Accounts
        merchant_wallet = await LedgerService.get_or_create_account(
            db, "MERCHANT", merchant_id, ACC_WALLET
        )
        
        # Global Hold Account (System owned)
        system_hold = await LedgerService.get_or_create_account(
            db, "SYSTEM", SYSTEM_ID, ACC_HOLD
        )
        
        # Check Balance (Read check, but actual prevention is failed ledger tx if we enforced non-negative)
        # We didn't enforce non-negative yet in LedgerService, but we should.
        # For now, let's check manually.
        if merchant_wallet.balance < amount:
             raise ValueError(f"Insufficient funds. Balance: {merchant_wallet.balance}, Required: {amount}")

        # 3. Create Ledger Transaction
        tx_req = TransactionRequest(
            idempotency_key=f"hold_order_{order_id}",
            reference_type="ORDER_HOLD",
            reference_id=order_id,
            description=f"Hold funds for Order {order.po_number}",
            entries=[
                EntryRequest(account_id=merchant_wallet.id, amount=amount, direction="DEBIT"), # Decrease Wallet
                EntryRequest(account_id=system_hold.id, amount=amount, direction="CREDIT")     # Increase Hold
            ],
            created_by=SYSTEM_ID # Auto
        )
        
        await LedgerService.post_transaction(db, tx_req)
        
        # 4. Update Order State
        order.status = ORDER_STATUS_FUNDS_HELD
        await db.flush()
        
        return "Funds reserved successfully."

    @staticmethod
    async def capture_order_payment(db: AsyncSession, order_id: uuid.UUID) -> str:
        """
        Finalize payment upon delivery.
        Moves funds: Global Hold -> Supplier Payable + Revenue (Fee)
        """
        # 1. Fetch Order
        result = await db.execute(select(Order).where(Order.id == order_id))
        order = result.scalar_one_or_none()
        
        if not order:
            raise ValueError("Order not found.")
            
        if order.status not in [ORDER_STATUS_SHIPPED, ORDER_STATUS_FUNDS_HELD]: # Allow capture if skipped shipping tracking?
             # Ideally strict: FUNDS_HELD -> APPROVED -> SHIPPED -> COMPLETED
             # Let's say we capture at COMPLETED.
             pass

        amount = Decimal(str(order.total_amount))
        supplier_id = order.supplier_id
        
        # Calculate Fees (e.g. 2%)
        platform_fee = amount * Decimal("0.02")
        payable_amount = amount - platform_fee
        
        # 2. Setup Accounts
        system_hold = await LedgerService.get_or_create_account(
            db, "SYSTEM", SYSTEM_ID, ACC_HOLD
        )
        supplier_payable = await LedgerService.get_or_create_account(
            db, "SUPPLIER", supplier_id, ACC_PAYABLE
        )
        system_revenue = await LedgerService.get_or_create_account(
            db, "SYSTEM", SYSTEM_ID, ACC_REVENUE
        )
        
        # 3. Ledger Tx
        tx_req = TransactionRequest(
            idempotency_key=f"capture_order_{order_id}",
            reference_type="ORDER_CAPTURE",
            reference_id=order_id,
            description=f"Release payment for Order {order.po_number}",
            entries=[
                EntryRequest(account_id=system_hold.id, amount=amount, direction="DEBIT"),       # Decrease Hold
                EntryRequest(account_id=supplier_payable.id, amount=payable_amount, direction="CREDIT"), # Pay Supplier
                EntryRequest(account_id=system_revenue.id, amount=platform_fee, direction="CREDIT")      # Pay Platform
            ],
            created_by=SYSTEM_ID
        )
        
        await LedgerService.post_transaction(db, tx_req)
        
        # 4. Update Order
        order.status = ORDER_STATUS_COMPLETED
        await db.flush()
        
        return "Payment captured."

    @staticmethod
    async def void_transaction(db: AsyncSession, order_id: uuid.UUID, reason: str) -> str:
        """
        Refund/Reverse a Hold.
        """
        order = (await db.execute(select(Order).where(Order.id == order_id))).scalar_one_or_none()
        if not order: raise ValueError("Order not found")
        
        if order.status != ORDER_STATUS_FUNDS_HELD:
             raise ValueError("Can only void held funds.")
             
        amount = Decimal(str(order.total_amount))
        
        merchant_wallet = await LedgerService.get_or_create_account(db, "MERCHANT", order.merchant_id, ACC_WALLET)
        system_hold = await LedgerService.get_or_create_account(db, "SYSTEM", SYSTEM_ID, ACC_HOLD)
        
        tx_req = TransactionRequest(
            idempotency_key=f"void_order_{order_id}",
            reference_type="ORDER_VOID",
            reference_id=order_id,
            description=f"Void Hold: {reason}",
            entries=[
                EntryRequest(account_id=system_hold.id, amount=amount, direction="DEBIT"),      # Decrease Hold
                EntryRequest(account_id=merchant_wallet.id, amount=amount, direction="CREDIT")  # Refund Wallet
            ],
            created_by=SYSTEM_ID
        )
        
        await LedgerService.post_transaction(db, tx_req)
        
        order.status = ORDER_STATUS_CANCELLED
        await db.flush()
        
        return "Transaction voided, funds refunded."
