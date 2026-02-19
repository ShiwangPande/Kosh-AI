"""Audit OCR Raw Text from DB."""
import asyncio
from sqlalchemy import select
from backend.database import async_session_factory
from backend.models.models import Invoice

async def audit():
    async with async_session_factory() as db:
        result = await db.execute(
            select(Invoice).order_by(Invoice.created_at.desc()).limit(10)
        )
        invoices = result.scalars().all()
        
        for inv in invoices:
            print(f"ID: {inv.id}")
            print(f"Status: {inv.ocr_status}")
            print(f"Raw Text Length: {len(inv.ocr_raw_text) if inv.ocr_raw_text else 0}")
            if inv.ocr_raw_text:
                print(f"--- START RAW TEXT ---\n{inv.ocr_raw_text}\n--- END RAW TEXT ---")
            print("="*40)

if __name__ == "__main__":
    asyncio.run(audit())
