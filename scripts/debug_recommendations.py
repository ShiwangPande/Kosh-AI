"""Debug Recommendations — Checks why an invoice didn't get results."""
import asyncio
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.database import async_session_factory
from backend.models.models import Invoice, InvoiceItem, Recommendation, Product, Score
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MERCHANT_ID = UUID("d5fd7962-d36c-42cf-f172-4b859d7d2459")

async def debug_invoice():
    async with async_session_factory() as db:
        # 1. Get latest invoice
        res = await db.execute(
            select(Invoice)
            .where(Invoice.merchant_id == MERCHANT_ID)
            .order_by(Invoice.created_at.desc())
            .limit(1)
        )
        invoice = res.scalar_one_or_none()
        if not invoice:
            print("No invoices found for this merchant.")
            return

        print(f"--- Latest Invoice Audit ---")
        print(f"Invoice ID: {invoice.id}")
        print(f"Status: {invoice.ocr_status}")
        print(f"Created At: {invoice.created_at}")

        # 2. Check items
        item_res = await db.execute(
            select(InvoiceItem).where(InvoiceItem.invoice_id == invoice.id)
        )
        items = item_res.scalars().all()
        print(f"Line Items Found: {len(items)}")
        
        for item in items:
            print(f" - Item: {item.raw_description} | Product ID: {item.product_id} | Price: {item.unit_price}")
            if item.product_id:
                # Check for benchmarks
                scores_res = await db.execute(
                    select(Score).where(Score.product_id == item.product_id)
                )
                scores = scores_res.scalars().all()
                print(f"   -> Market Benchmarks for this product: {len(scores)}")

        # 3. Check existing recommendations
        rec_res = await db.execute(
            select(Recommendation).where(Recommendation.invoice_id == invoice.id)
        )
        recs = rec_res.scalars().all()
        print(f"Recommendations Generated: {len(recs)}")
        for rec in recs:
            print(f" - Rec: {rec.recommended_supplier_id} | Savings: {rec.savings_estimate}")

if __name__ == "__main__":
    asyncio.run(debug_invoice())
