"""Relink Kaggle Data — Matches invoices to new products for demo visibility."""
import asyncio
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from backend.database import async_session_factory
from backend.models.models import Product, Invoice, InvoiceItem, Recommendation
from backend.services.comparison_engine import generate_recommendations
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MERCHANT_ID = UUID("d5fd7962-d36c-42cf-f172-4b859d7d2459")

async def relink_and_recommend():
    async with async_session_factory() as db:
        # 1. Find the latest verified invoice for this merchant
        inv_res = await db.execute(
            select(Invoice)
            .where(Invoice.merchant_id == MERCHANT_ID, Invoice.ocr_status == 'verified')
            .order_by(Invoice.created_at.desc())
            .limit(1)
        )
        invoice = inv_res.scalar_one_or_none()
        if not invoice:
            logger.error("No verified invoice found to relink.")
            return

        # 2. Find some of the new Kaggle products
        prod_res = await db.execute(select(Product).limit(5))
        products = prod_res.scalars().all()
        if not products:
            logger.error("No products found in DB.")
            return

        # 3. Update invoice items to these products
        item_res = await db.execute(
            select(InvoiceItem).where(InvoiceItem.invoice_id == invoice.id)
        )
        items = item_res.scalars().all()
        
        for i, item in enumerate(items):
            target_prod = products[i % len(products)]
            item.product_id = target_prod.id
            item.raw_description = f"[Demo] {target_prod.name}"
            logger.info(f"Relinked item {item.id} to product {target_prod.name}")

        # 4. Clear old recommendations for this invoice (to avoid duplicates)
        await db.execute(delete(Recommendation).where(Recommendation.invoice_id == invoice.id))
        
        await db.commit()

        # 5. Trigger recommendation engine
        recs = await generate_recommendations(db, MERCHANT_ID, invoice.id)
        await db.commit()
        
        logger.info(f"Relinking complete! Generated {len(recs)} new Kaggle-powered recommendations.")

if __name__ == "__main__":
    from sqlalchemy import delete
    asyncio.run(relink_and_recommend())
