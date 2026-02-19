"""Test invoice items API endpoint"""
import asyncio
from backend.database import async_session_factory
from backend.models.models import Invoice, InvoiceItem
from sqlalchemy import select

async def test():
    async with async_session_factory() as db:
        # Get an invoice with items
        result = await db.execute(
            select(Invoice).where(Invoice.invoice_number == 'us-001').limit(1)
        )
        invoice = result.scalar_one_or_none()
        if not invoice:
            print("No us-001 invoice found!")
            return
            
        print(f"Invoice ID: {invoice.id}")
        print(f"Invoice Number: {invoice.invoice_number}")
        print(f"Merchant ID: {invoice.merchant_id}")
        
        # Get items for this invoice
        items_result = await db.execute(
            select(InvoiceItem).where(InvoiceItem.invoice_id == invoice.id)
        )
        items = items_result.scalars().all()
        
        print(f"\nFound {len(items)} items:")
        for item in items:
            print(f"  - {item.raw_description}: {item.quantity} x ₹{item.unit_price}")

if __name__ == "__main__":
    asyncio.run(test())
