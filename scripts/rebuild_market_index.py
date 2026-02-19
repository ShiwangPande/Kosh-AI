
import asyncio
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select
from backend.database import async_session_factory
from backend.models.models import Invoice
from backend.services.market_intelligence import MarketIntelligenceService

async def rebuild_index():
    print("Starting Market Index Rebuild...")
    async with async_session_factory() as db:
        # Fetch all completed/verified invoices
        result = await db.execute(
            select(Invoice.id).where(Invoice.ocr_status.in_(['completed', 'verified']))
        )
        invoice_ids = result.scalars().all()
        
        print(f"Found {len(invoice_ids)} verified invoices.")
        
        for i, inv_id in enumerate(invoice_ids):
            print(f"Processing invoice {i+1}/{len(invoice_ids)}: {inv_id}")
            try:
                await MarketIntelligenceService.update_index_from_invoice(db, inv_id)
                await db.commit() 
            except Exception as e:
                print(f"Error processing {inv_id}: {e}")
                
    print("Market Index Rebuild Complete.")

if __name__ == "__main__":
    asyncio.run(rebuild_index())
