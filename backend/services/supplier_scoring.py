from datetime import datetime, timedelta
from typing import List, Dict
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from backend.models.models import Supplier, Invoice, InvoiceItem, Product

class SupplierScoreService:
    @staticmethod
    async def update_supplier_score(db: AsyncSession, supplier_id: UUID):
        """
        Calculate and update intelligence scores for a supplier.
        Phase 13: Reliability (Fulfillment) + Consistency (Price Stability) + Speed + Categorization.
        """
        supplier = await db.get(Supplier, supplier_id)
        if not supplier:
            return None

        # 1. Reliability Score (Proxy: Successful Invoices ratio)
        # In a real procurement system, this would compare PO vs Invoice.
        # For Kosh: Use successful OCR vs Total as a proxy.
        total_res = await db.execute(
            select(func.count(Invoice.id)).where(Invoice.supplier_id == supplier_id)
        )
        total_invoices = total_res.scalar() or 1
        
        success_res = await db.execute(
            select(func.count(Invoice.id)).where(
                Invoice.supplier_id == supplier_id,
                Invoice.ocr_status.in_(['completed', 'verified'])
            )
        )
        success_invoices = success_res.scalar() or 0
        reliability = success_invoices / total_invoices

        # 2. Price Consistency
        items_result = await db.execute(
            select(InvoiceItem.product_id, InvoiceItem.unit_price)
            .join(Invoice)
            .where(
                Invoice.supplier_id == supplier_id,
                Invoice.ocr_status.in_(['completed', 'verified']),
                InvoiceItem.product_id.isnot(None),
                InvoiceItem.unit_price > 0
            )
        )
        items = items_result.all()
        
        product_prices: Dict[UUID, List[float]] = {}
        for pid, price in items:
            if pid not in product_prices: 
                product_prices[pid] = []
            product_prices[pid].append(float(price))
        
        variances = []
        for pid, prices in product_prices.items():
            if len(prices) > 1:
                import statistics
                mean = statistics.mean(prices)
                std = statistics.stdev(prices)
                if mean > 0:
                    cv = std / mean
                    variances.append(cv)
            else:
                # Neutral 1.0 for single item (no variance yet)
                variances.append(0.0)
        
        if variances:
            import statistics
            avg_cv = statistics.mean(variances)
            consistency = 1.0 / (1.0 + avg_cv) 
        else:
            consistency = 0.5 

        # 3. Delivery Speed Score
        # Benchmark: 3 days = 1.0, 14 days = 0.0
        days = supplier.avg_delivery_days or 7
        speed = max(0.0, min(1.0, 1.0 - (days - 3) / 11))

        # 4. Category Inference
        # Get most common product category
        if items:
            cat_query = await db.execute(
                select(Product.category, func.count(Product.id).label('cnt'))
                .join(InvoiceItem, Product.id == InvoiceItem.product_id)
                .join(Invoice, Invoice.id == InvoiceItem.invoice_id)
                .where(Invoice.supplier_id == supplier_id, Product.category != 'uncategorized')
                .group_by(Product.category)
                .order_by(desc('cnt'))
                .limit(1)
            )
            top_cat = cat_query.first()
            if top_cat:
                supplier.category = top_cat[0]

        # 5. Save Results
        supplier.reliability_score = round(reliability, 2)
        supplier.price_consistency_score = round(consistency, 2)
        supplier.delivery_speed_score = round(speed, 2)
        supplier.last_score_update = datetime.utcnow()
        
        await db.commit()
        return supplier
