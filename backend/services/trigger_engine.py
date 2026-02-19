"""
Trigger Engine Service.

The "Habit Layer" core. Converts system signals into persistable, actionable
TriggerEvents for the user. Handles deduplication and prioritization.
"""
import uuid
import hashlib
import json
from datetime import datetime, timedelta
from typing import Dict, Optional, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.models.models import TriggerEvent

# Priority Levels
PRIORITY_CRITICAL = 1
PRIORITY_HIGH = 2
PRIORITY_MEDIUM = 3
PRIORITY_LOW = 4

# Event Types
EVENT_PRICE_DROP = "PRICE_DROP"
EVENT_RISK_ALERT = "RISK_ALERT" 
EVENT_PAYMENT_DUE = "PAYMENT_DUE"
EVENT_STOCK_LOW = "STOCK_LOW"
EVENT_OPPORTUNITY = "OPPORTUNITY"

class TriggerEngine:
    
    @staticmethod
    def _generate_dedupe_key(merchant_id: uuid.UUID, event_type: str, target_id: Optional[str] = None) -> str:
        """Create a unique key for deduplication."""
        raw = f"{merchant_id}:{event_type}:{target_id or ''}"
        return hashlib.sha256(raw.encode()).hexdigest()

    @staticmethod
    def _get_config(event_type: str):
        """Return (Priority, ExpirationHours) based on type."""
        if event_type == EVENT_RISK_ALERT:
            return (PRIORITY_CRITICAL, 24 * 7) # Week
        elif event_type == EVENT_PAYMENT_DUE:
            return (PRIORITY_CRITICAL, 24)
        elif event_type == EVENT_PRICE_DROP:
            return (PRIORITY_HIGH, 6) # Valid only for 6 hours
        elif event_type == EVENT_STOCK_LOW:
            return (PRIORITY_HIGH, 24)
        else:
            return (PRIORITY_MEDIUM, 12)

    @staticmethod
    async def emit(
        db: AsyncSession,
        merchant_id: uuid.UUID,
        event_type: str,
        payload: Dict[str, Any],
        target_id: Optional[str] = None
    ) -> Optional[TriggerEvent]:
        """
        Ingest a signal and create a TriggerEvent if valid and not duplicate.
        """
        # 1. Deduplication
        dedupe_key = TriggerEngine._generate_dedupe_key(merchant_id, event_type, target_id)
        
        # Check for existing active trigger (created recently)
        # We allow re-trigger if previous one is older than 24h OR expired
        # For simplicity, let's just check if there is a PENDING one with same key
        stmt = select(TriggerEvent).where(
            TriggerEvent.dedupe_key == dedupe_key,
            TriggerEvent.status == "PENDING",
            TriggerEvent.expires_at > datetime.utcnow()
        )
        existing = await db.execute(stmt)
        if existing.scalar_one_or_none():
            return None # Duplicate suppressed

        # 2. Configure
        priority, hours = TriggerEngine._get_config(event_type)
        expires_at = datetime.utcnow() + timedelta(hours=hours)
        
        # 3. Create
        trigger = TriggerEvent(
            merchant_id=merchant_id,
            event_type=event_type,
            priority=priority,
            payload=payload,
            status="PENDING",
            dedupe_key=dedupe_key,
            expires_at=expires_at
        )
        
        db.add(trigger)
        await db.flush()
        
        return trigger

    @staticmethod
    async def get_pending_triggers(db: AsyncSession, merchant_id: uuid.UUID):
        """Fetch active triggers for the feed."""
        stmt = select(TriggerEvent).where(
            TriggerEvent.merchant_id == merchant_id,
            TriggerEvent.status == "PENDING",
            TriggerEvent.expires_at > datetime.utcnow()
        ).order_by(
            TriggerEvent.priority.asc(), # 1 is highest
            TriggerEvent.created_at.desc()
        )
        result = await db.execute(stmt)
        return result.scalars().all()
