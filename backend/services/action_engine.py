"""
Action Engine Service.

Converts "YES/NO" merchant replies into system actions.
"""
import uuid
import logging
from datetime import datetime
from typing import Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from sqlalchemy.exc import IntegrityError

from backend.models.models import TriggerEvent, UserAction, Merchant, NegotiationSignal, DecisionContext, EventLog
from backend.services.trigger_engine import EVENT_PRICE_DROP, EVENT_RISK_ALERT
from backend.services.transaction_engine import TransactionEngine

logger = logging.getLogger(__name__)

class ActionEngine:
    
    @staticmethod
    async def handle_response(db: AsyncSession, merchant_id: uuid.UUID, raw_text: str) -> str:
        """
        Main Entry Point.
        1. Find Context (Latest Trigger)
        2. Parse Intent & Capture Signals
        3. Execute Action
        """
        # 1. Normalize
        text = raw_text.strip().upper()
        
        # 2. Find Latest Trigger (Sent to this merchant)
        stmt = select(TriggerEvent).where(
            TriggerEvent.merchant_id == merchant_id,
            TriggerEvent.status == "SENT"
        ).order_by(desc(TriggerEvent.created_at)).limit(1)
        
        trigger = (await db.execute(stmt)).scalar_one_or_none()
        
        if not trigger:
            return "No active alert found to reply to."
            
        # 3. Check Expiry
        if trigger.expires_at and trigger.expires_at < datetime.utcnow():
            return "This offer has expired."
            
        # 4. Map Intent
        intent, action_type = ActionEngine._map_intent(text)
        if not intent:
            # Capture as Negotiation Signal even if we don't understand it yet
            await ActionEngine._capture_negotiation(db, merchant_id, trigger.id, raw_text)
            return "Reply YES to accept or NO to dismiss."
            
        # 5. Idempotency Check & Persistence
        try:
            action = UserAction(
                merchant_id=merchant_id,
                trigger_id=trigger.id,
                action_type=action_type,
                raw_response=raw_text,
                status="RECEIVED"
            )
            db.add(action)
            await db.flush() # Get ID
            
            # 6. Capture Context Snapshot (The Time Machine)
            await ActionEngine._capture_context(db, merchant_id, trigger, action)
            
        except IntegrityError:
            await db.rollback()
            return "You have already responded to this alert."
            
        # 7. Execution
        try:
            if action_type == "ACCEPT":
                result_msg = await ActionEngine._execute_accept(db, trigger)
                action.status = "EXECUTED"
            elif action_type == "DISMISS":
                trigger.status = "DISMISSED"
                action.status = "EXECUTED"
                await ActionEngine._capture_negotiation(db, merchant_id, trigger.id, raw_text) # Capture "NO" reason too
                result_msg = "Alert dismissed."
            else:
                result_msg = "Unknown action."
                
            action.executed_at = datetime.utcnow()
            
            # Log Event
            db.add(EventLog(event_type="USER_ACTION_COMPLETED", entity_id=action.id, payload={"type": action_type}))
            
            await db.commit()
            return result_msg
            
        except Exception as e:
            logger.error(f"Action Execution Failed: {e}")
            action.status = "FAILED"
            await db.commit()
            return f"Action failed: {str(e)}"

    @staticmethod
    async def _capture_negotiation(db: AsyncSession, merchant_id: uuid.UUID, trigger_id: uuid.UUID, text: str):
        """Parse and store negotiation intent."""
        # Simple heuristic parser
        t = text.lower()
        price_obj = "expensive" in t or "price" in t or "high" in t
        urgency = "now" in t or "tomorrow" in t
        
        signal = NegotiationSignal(
            merchant_id=merchant_id,
            trigger_id=trigger_id,
            message_text=text,
            price_objection=price_obj,
            delivery_issue=urgency,
            intent_detected="NEGOTIATION" if (price_obj or urgency) else "UNKNOWN"
        )
        db.add(signal)

    @staticmethod
    async def _capture_context(db: AsyncSession, merchant_id: uuid.UUID, trigger: TriggerEvent, action: UserAction):
        """Snapshot the state of the world."""
        # In a real system, we'd fetch Credit, Supplier Score, etc
        # Mocking values for now
        
        ctx = DecisionContext(
            merchant_id=merchant_id,
            trigger_id=trigger.id,
            user_action_id=action.id,
            request_time=datetime.utcnow(),
            decision=action.action_type,
            
            # Captured Variables
            time_of_day=datetime.utcnow().time(),
            day_of_week=datetime.utcnow().weekday(),
            price_at_time=trigger.payload.get("price"), # Assuming price is in trigger
            response_time_ms=int((datetime.utcnow() - trigger.created_at).total_seconds() * 1000)
        )
        db.add(ctx)

    @staticmethod
    def _map_intent(text: str) -> Tuple[Optional[str], Optional[str]]:
        if text in ["YES", "Y", "CONFIRM", "BUY"]:
            return "POSITIVE", "ACCEPT"
        elif text in ["NO", "N", "CANCEL", "DISMISS"]:
            return "NEGATIVE", "DISMISS"
        return None, None

    @staticmethod
    async def _execute_accept(db: AsyncSession, trigger: TriggerEvent) -> str:
        """Execute the business logic for ACCEPT."""
        
        if trigger.event_type == EVENT_PRICE_DROP:
            # Payload example: {"sku": "SUGAR", "price": 38, "order_id": ...} 
            # If it's just a price alert, we might need to CREATE an order.
            # If the payload has an 'order_id' (e.g. pre-built cart), we use that.
            
            payload = trigger.payload
            
            if "order_id" in payload:
                # Confirm an existing draft order
                 order_id = uuid.UUID(payload["order_id"])
                 # Call TransactionEngine to Hold Funds
                 await TransactionEngine.place_order_hold(db, order_id)
                 return "✅ Order placed successfully! Funds reserved."
            
            elif "sku" in payload:
                 # Create a new Order? 
                 # For now, let's assume simple flow: We need an Order ID.
                 # If we just have SKU, we can't easily auto-order without quantity.
                 # Let's assume the Trigger CREATION Logic pre-created a 'Draft' Order 
                 # and put the ID in the payload.
                 return "Please checkout on dashboard (Order Creation via text not fully implemented)."
                 
        return "Action recorded."
