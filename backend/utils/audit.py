"""Audit logging utility."""
import uuid
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from backend.models.models import ActivityLog


async def log_activity(
    db: AsyncSession,
    action: str,
    actor_id: Optional[uuid.UUID] = None,
    actor_role: Optional[str] = None,
    resource_type: Optional[str] = None,
    resource_id: Optional[uuid.UUID] = None,
    details: Optional[dict] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
) -> ActivityLog:
    """Create an audit log entry."""
    log = ActivityLog(
        actor_id=actor_id,
        actor_role=actor_role,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        details=details,
        ip_address=ip_address,
        user_agent=user_agent,
    )
    db.add(log)
    await db.flush()
    return log
