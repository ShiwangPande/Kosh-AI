"""WhatsApp webhook API layer."""
from fastapi import APIRouter, Depends, HTTPException, Request, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.config import get_settings
from backend.models.models import WhatsAppMessage
from backend.utils.audit import log_activity

settings = get_settings()
router = APIRouter(prefix="/whatsapp", tags=["WhatsApp"])


@router.get("/webhook")
async def verify_webhook(
    hub_mode: str = Query(None, alias="hub.mode"),
    hub_verify_token: str = Query(None, alias="hub.verify_token"),
    hub_challenge: str = Query(None, alias="hub.challenge"),
):
    """WhatsApp webhook verification endpoint."""
    if hub_mode == "subscribe" and hub_verify_token == settings.WHATSAPP_VERIFY_TOKEN:
        return int(hub_challenge)
    raise HTTPException(status_code=403, detail="Verification failed")


@router.post("/webhook")
async def receive_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Receive incoming WhatsApp messages."""
    body = await request.json()

    try:
        entry = body.get("entry", [{}])[0]
        changes = entry.get("changes", [{}])[0]
        value = changes.get("value", {})
        messages = value.get("messages", [])

        for msg in messages:
            wa_message = WhatsAppMessage(
                direction="inbound",
                phone_number=msg.get("from", ""),
                message_type=msg.get("type", "text"),
                content=msg.get("text", {}).get("body", ""),
                external_id=msg.get("id", ""),
            )
            db.add(wa_message)

        await db.flush()
    except Exception:
        pass  # Log but don't fail — WhatsApp expects 200

    return {"status": "ok"}


async def send_whatsapp_message(
    phone_number: str,
    message: str,
    db: AsyncSession,
) -> bool:
    """Send a WhatsApp message via the Cloud API."""
    import httpx

    url = f"{settings.WHATSAPP_API_URL}/{settings.WHATSAPP_PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {settings.WHATSAPP_API_TOKEN}",
        "Content-Type": "application/json",
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": phone_number,
        "type": "text",
        "text": {"body": message},
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()

        wa_message = WhatsAppMessage(
            direction="outbound",
            phone_number=phone_number,
            message_type="text",
            content=message,
            status="sent",
        )
        db.add(wa_message)
        await db.flush()
        return True
    except Exception:
        return False
