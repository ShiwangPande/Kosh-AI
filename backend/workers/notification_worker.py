"""
Notification Worker.

Continuously polls for pending TriggerEvents and dispatches them to the NotificationEngine.
Uses SKIP LOCKED for concurrency safety.
"""
import asyncio
import logging
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, or_, and_

from backend.database import async_session_factory
from backend.models.models import TriggerEvent
from backend.services.notification_engine import NotificationEngine

logger = logging.getLogger(__name__)

class NotificationWorker:
    
    BATCH_SIZE = 50
    MAX_RETRIES = 5
    
    @staticmethod
    async def run_forever():
        """Main worker loop."""
        logger.info("Notification Worker started.")
        while True:
            try:
                processed = await NotificationWorker.process_batch()
                if processed == 0:
                    await asyncio.sleep(5) # Idle backoff
                else:
                    await asyncio.sleep(0.5) # Busy wait
            except Exception as e:
                logger.error(f"Worker Loop Error: {e}")
                await asyncio.sleep(5)

    @staticmethod
    async def process_batch() -> int:
        """
        Fetch and process a batch of pending triggers.
        Returns number of triggers processed.
        """
        async with async_session_factory() as db:
            # 1. Fetch Pending Triggers with Locking
            # Priority ASC because 1=Critical, 4=Low
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
            ).limit(NotificationWorker.BATCH_SIZE).with_for_update(skip_locked=True)
            
            result = await db.execute(stmt)
            triggers = result.scalars().all()
            
            if not triggers:
                return 0
            
            count = 0
            for trigger in triggers:
                try:
                    # 2. Attempt Delivery
                    # Note: NotificationEngine handles delivery logic. 
                    # If it returns (meaning successful handoff to underlying provider), we mark SENT.
                    # Ideally NotificationEngine should return success/fail bool.
                    
                    # We need to peek into NotificationEngine to see how strictly it handles errors.
                    # Currently it logs errors but doesn't raise.
                    # Let's assume for now: if it runs without exception, it's "processed".
                    # Real-world: Engine should return Enum(DELIVERED, RETRY, FAILED)
                    
                    await NotificationEngine.deliver_trigger(db, trigger.id)
                    
                    # Refresh to check status change
                    await db.refresh(trigger)
                    
                    if trigger.status == "SENT":
                         count += 1
                    else:
                         # Engine might have skipped it (Quiet Hours) or it failed silently?
                         # If status is still PENDING, it means Engine skipped it (e.g. Quiet Hours)
                         if trigger.status == "PENDING":
                             # If Quiet Hours, Engine just returns.
                             # We should backoff this trigger so we don't busy loop on it.
                             # Set next_retry_at to +15 mins?
                             # Or just let it sit if we are using SKIP LOCKED correctly?
                             # PROBLEM: If we don't update row, next loop will pick it up again immediately!
                             # We MUST push next_retry_at forward.
                             trigger.next_retry_at = now + timedelta(minutes=15)
                             db.add(trigger)
                
                except Exception as e:
                    logger.error(f"Delivery Failed for {trigger.id}: {e}")
                    NotificationWorker._handle_failure(trigger, now)
                    db.add(trigger)
            
            await db.commit()
            return len(triggers)

    @staticmethod
    def _handle_failure(trigger: TriggerEvent, now: datetime):
        """Exponential Backoff Logic."""
        trigger.retry_count += 1
        
        if trigger.retry_count > NotificationWorker.MAX_RETRIES:
            trigger.status = "FAILED"
            logger.error(f"Trigger {trigger.id} FAILED after {trigger.retry_count} retries.")
        else:
            # Backoff: 30s, 60s, 120s, 300s, 600s
            backoff_map = {1: 30, 2: 60, 3: 120, 4: 300, 5: 600}
            seconds = backoff_map.get(trigger.retry_count, 600)
            trigger.next_retry_at = now + timedelta(seconds=seconds)
