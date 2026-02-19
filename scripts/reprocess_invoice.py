
import asyncio
from sqlalchemy import select, update
from backend.database import async_session_factory
from backend.models.models import Invoice
from backend.workers.celery_app import celery_app

async def rescue_stuck_invoices():
    async with async_session_factory() as session:
        # malicious/stuck tasks are 'processing' but not updated recently?
        # For now, just grab the one we know is stuck
        stmt = select(Invoice).where(Invoice.ocr_status.in_(['processing', 'pending']))
        result = await session.execute(stmt)
        invoices = result.scalars().all()
        
        print(f"Found {len(invoices)} stuck invoices.")
        
        for invoice in invoices:
            print(f"Rescuing Invoice {invoice.id}...")
            
            # 1. Reset status
            invoice.ocr_status = 'pending'
            session.add(invoice)
            await session.commit()
            
            # 2. Re-queue task
            celery_app.send_task(
                "backend.workers.ocr_worker.process_invoice_ocr",
                args=[str(invoice.id)],
            )
            print(f" -> Re-queued task for {invoice.id}")

if __name__ == "__main__":
    asyncio.run(rescue_stuck_invoices())
