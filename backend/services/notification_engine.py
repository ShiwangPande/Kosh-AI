"""
Notification Delivery Engine.

Handles the "Last Mile" delivery of triggers to users via WhatsApp/Email.
"""
import uuid
import logging
from datetime import datetime, time
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from backend.models.models import TriggerEvent, Merchant, NotificationLog, NotificationTemplate
from backend.api.whatsapp import send_whatsapp_message

logger = logging.getLogger(__name__)

class NotificationEngine:
    
    @staticmethod
    async def deliver_trigger(db: AsyncSession, trigger_id: uuid.UUID):
        """
        Process a single pending trigger.
        1. Access Check (Quiet Hours)
        2. Rate Limit Check
        3. Delivery
        """
        # 1. Fetch Context
        trigger = (await db.execute(select(TriggerEvent).where(TriggerEvent.id == trigger_id))).scalar_one_or_none()
        if not trigger or trigger.status != "PENDING":
            return
            
        merchant = (await db.execute(select(Merchant).where(Merchant.id == trigger.merchant_id))).scalar_one_or_none()
        if not merchant:
            return

        # 2. Quiet Hours Check (Skip if CRITICAL)
        if trigger.priority > 1: # Not Critical
            if NotificationEngine._is_quiet_hours(merchant):
                logger.info(f"Skipping delivery for {merchant.id} due to Quiet Hours.")
                return # Leave as PENDING, pick up later

        # 3. Rate Limit Check (Max 3/hr)
        last_hour = datetime.utcnow() - timedelta(hours=1)
        count_q = select(func.count(NotificationLog.id)).where(
            NotificationLog.merchant_id == merchant.id,
            NotificationLog.sent_at >= last_hour
        )
        sent_count = (await db.execute(count_q)).scalar() or 0
        
        if sent_count >= 3 and trigger.priority > 1:
             logger.info(f"Rate limit exceeded for {merchant.id}")
             return # Queue

        # 4. Render Message
        # Mock Template for now
        message_body = f"Alert: {trigger.event_type} - {trigger.payload}"
        
        # 5. Send (WhatsApp Default)
        if merchant.phone:
            success = await send_whatsapp_message(merchant.phone, message_body, db)
            status = "SENT" if success else "FAILED"
        else:
            status = "FAILED_NO_PHONE"
            
        # 6. Log & Update
        log = NotificationLog(
            trigger_id=trigger.id,
            merchant_id=merchant.id,
            channel="WHATSAPP",
            status=status
        )
        db.add(log)
        
        if status == "SENT":
            trigger.status = "SENT"
        
        await db.flush()

    @staticmethod
    def _is_quiet_hours(merchant: Merchant) -> bool:
        if not merchant.quiet_hours_start or not merchant.quiet_hours_end:
            return False
            
        now = datetime.utcnow().time() # UTC! Need timezone awareness later.
        # Simple check assuming UTC for now
        start = merchant.quiet_hours_start
        end = merchant.quiet_hours_end
        
        if start < end:
            return start <= now <= end
        else: # Crosses midnight
            return start <= now or now <= end
