import asyncio
import uuid
from backend.database import async_session_factory
from backend.models.models import Supplier, Product, Invoice, InvoiceItem
from sqlalchemy import select, update
from backend.services.comparison_engine import generate_recommendations

async def fix_and_generate():
    async with async_session_factory() as session:
        # 1. Get a supplier to link to
        res = await session.execute(select(Supplier).where(Supplier.name == "National Distributors Ltd"))
        supplier = res.scalar_one_or_none()
        if not supplier:
            print("Supplier not found!")
            return
            
        # 2. Create a relevant product
        product = Product(
            sku_code="AUTO-001",
            name="Brake Cable Kit",
            normalized_name="brake cable kit",
            category="Automotive",
            unit="set"
        )
        session.add(product)
        await session.flush()
        
        # 3. Create a COMPETITOR supplier who is CHEAPER
        competitor = Supplier(
            name="AutoParts Wholesale",
            category="Automotive",
            city="Pune",
            state="Maharashtra",
            credit_terms=45,
            avg_delivery_days=2,
            reliability_score=0.95,
            is_approved=True,
        )
        session.add(competitor)
        await session.flush()
        
        # Also need a record for this competitor selling the product at a low price
        # We can simulate this by putting a fake invoice from this supplier in the past
        # But generate_recommendations uses compare_suppliers_for_product which uses compute_full_score
        # compute_full_score uses price_score
        
        # 4. Link existing verified invoices to this supplier and product
        res = await session.execute(
            select(Invoice).where(Invoice.ocr_status == "verified")
        )
        invoices = res.scalars().all()
        for inv in invoices:
            inv.supplier_id = supplier.id
            
            # Link items to product
            items_res = await session.execute(
                select(InvoiceItem).where(InvoiceItem.invoice_id == inv.id)
            )
            items = items_res.scalars().all()
            for item in items:
                item.product_id = product.id
                # Ensure it has a price for comparison
                if not item.unit_price:
                    item.unit_price = 500.0
        
        await session.commit()
        print(f"Linked {len(invoices)} invoices to {supplier.name} and product {product.name}")
        
        # 5. TRIGGER RECOMMENDATIONS
        for inv in invoices:
            recs = await generate_recommendations(session, inv.merchant_id, inv.id)
            print(f"Generated {len(recs)} recommendations for invoice {inv.id}")
            
        await session.commit()
        print("✅ Intelligence generation complete!")

if __name__ == "__main__":
    asyncio.run(fix_and_generate())
