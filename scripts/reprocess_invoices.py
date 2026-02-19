"""Reprocess invoices to attempt line item extraction and recommendation generation."""
import asyncio
from sqlalchemy import select, update, delete
from backend.database import async_session_factory
from backend.models.models import Invoice, InvoiceItem, Product
from backend.services.ocr_service import OCRService
from backend.services.sku_service import create_or_match_product
from backend.services.comparison_engine import generate_recommendations
from backend.services.validation_pipeline import validate_invoice_data, validate_line_item
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def reprocess():
    print("DEBUG: Starting reprocess script...", flush=True)
    service = OCRService()
    async with async_session_factory() as db:
        print("DEBUG: Database session opened.", flush=True)
        
        # Get all invoices with raw text, grouped by merchant
        result = await db.execute(
            select(Invoice).where(Invoice.ocr_raw_text.isnot(None)).order_by(Invoice.created_at.desc())
        )
        invoices = result.scalars().all()
        print(f"DEBUG: Found {len(invoices)} invoices to check.", flush=True)
        
        for inv in invoices:
            print(f"DEBUG: Processing Invoice {inv.id} (Number: {inv.invoice_number}, Merchant: {inv.merchant_id})", flush=True)

            if not inv.ocr_raw_text:
                continue

            # Clear existing items for this invoice
            await db.execute(delete(InvoiceItem).where(InvoiceItem.invoice_id == inv.id))
            
            # Re-extract
            new_items_data = service._extract_line_items(inv.ocr_raw_text)
            if not new_items_data:
                logger.warning(f"No items extracted for Invoice {inv.id} even with new logic.")
                continue
            
            logger.info(f"Extracted {len(new_items_data)} items. Saving...")
            
            for item_data in new_items_data:
                # Per-item validation
                is_valid, issues, item_quality = validate_line_item(item_data)
                
                # Match or create product
                product, confidence = await create_or_match_product(
                    raw_description=item_data["description"],
                    db=db,
                )
                
                inv_item = InvoiceItem(
                    invoice_id=inv.id,
                    product_id=product.id,
                    raw_description=item_data["description"],
                    quantity=item_data.get("quantity"),
                    unit_price=item_data.get("unit_price"),
                    total_price=item_data.get("total_price"),
                    matched_sku=product.sku_code,
                    match_confidence=confidence,
                )
                db.add(inv_item)
            
            inv.ocr_status = "completed"
            await db.commit()
            
            # Generate recommendations
            logger.info(f"Generating recommendations for Invoice {inv.id}...")
            try:
                recs = await generate_recommendations(db, inv.merchant_id, inv.id)
                await db.commit()
                logger.info(f"Generated {len(recs)} recommendations.")
            except Exception as e:
                logger.error(f"Failed to generate recommendations for {inv.id}: {e}")

if __name__ == "__main__":
    asyncio.run(reprocess())
