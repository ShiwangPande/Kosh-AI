from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.dialects.postgresql import insert
from backend.models.models import MarketIndex, Invoice, InvoiceItem, Product
import logging
import statistics

logger = logging.getLogger(__name__)

class MarketIntelligenceService:
    @staticmethod
    async def update_index_from_invoice(db: AsyncSession, invoice_id: str):
        """
        Updates the Market Index using verified items from a specific invoice.
        Should be called AFTER invoice is verified.
        """
        # 1. Fetch Invoice Items with Product details (Outer Join to capture unlinked items)
        result = await db.execute(
            select(InvoiceItem, Product.normalized_name, Product.category)
            .outerjoin(Product, InvoiceItem.product_id == Product.id)
            .join(Invoice, InvoiceItem.invoice_id == Invoice.id)
            .where(Invoice.id == invoice_id)
        )
        items = result.all()
        
        if not items:
            logger.info(f"No items found in verified invoice {invoice_id}")
            return

        # 2. Update Index for each item
        updated_count = 0
        for item, normalized_name, category in items:
            name_to_use = normalized_name
            
            # Fallback to raw description if not linked
            if not name_to_use and item.raw_description:
                cleaned = item.raw_description.strip().lower()
                if len(cleaned) > 2:
                    name_to_use = cleaned
            
            if not name_to_use or not item.unit_price:
                continue

            # Check if index exists
            idx_result = await db.execute(
                select(MarketIndex).where(MarketIndex.normalized_product_name == name_to_use)
            )
            market_entry = idx_result.scalar_one_or_none()
            
            price = float(item.unit_price)

            if market_entry:
                # Update existing stats
                new_count = market_entry.sample_size + 1
                current_total = float(market_entry.avg_price) * market_entry.sample_size
                new_avg = (current_total + price) / new_count
                
                market_entry.avg_price = new_avg
                market_entry.sample_size = new_count
                market_entry.min_price = min(float(market_entry.min_price), price)
                market_entry.max_price = max(float(market_entry.max_price), price)
            else:
                # Create new entry
                new_entry = MarketIndex(
                    normalized_product_name=name_to_use,
                    product_category=category,
                    avg_price=price,
                    min_price=price,
                    max_price=price,
                    sample_size=1
                )
                db.add(new_entry)
            updated_count += 1
        
        await db.flush()
        logger.info(f"Updated Market Index for {updated_count} items from invoice {invoice_id}")

    @staticmethod
    async def get_market_price(db: AsyncSession, normalized_name: str):
        """Returns {avg, min, max} or None"""
        result = await db.execute(
            select(MarketIndex).where(MarketIndex.normalized_product_name == normalized_name)
        )
        entry = result.scalar_one_or_none()
        return entry
