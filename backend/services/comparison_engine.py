"""Supplier comparison engine + recommendation generation."""
from typing import List, Optional, Dict
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, literal_column
from sqlalchemy.orm import aliased

from backend.models.models import (
    Supplier, Score, InvoiceItem, Invoice, Recommendation, Product,
)
from backend.services.value_score import compute_full_score


async def compare_suppliers_for_product(
    db: AsyncSession,
    merchant_id: UUID,
    product_id: UUID,
    current_supplier_id: Optional[UUID] = None,
) -> List[Score]:
    """Compare all approved suppliers for a given product and return sorted scores.

    SC2 fix: Uses batched queries instead of per-supplier loops.
    - Batch 1: All approved suppliers (single query)
    - Batch 2: Latest unit price per supplier for this product (single query with window fn)
    - Batch 3: Invoice counts per supplier for this merchant (single query with GROUP BY)
    - Loop: Score computation only (no DB calls inside loop except upsert)
    """
    # 1. Fetch all approved suppliers (single query)
    suppliers_result = await db.execute(
        select(Supplier).where(Supplier.is_approved == True)
    )
    suppliers = suppliers_result.scalars().all()
    if not suppliers:
        return []

    supplier_ids = [s.id for s in suppliers]

    supplier_ids = [s.id for s in suppliers]

    # 2. Get average market price (Phase 6: Use MarketIndex)
    # Fetch product details first
    product_query = await db.execute(select(Product.normalized_name).where(Product.id == product_id))
    normalized_name = product_query.scalar_one_or_none()

    avg_market_price = 0.0
    if normalized_name:
        from backend.models.models import MarketIndex
        market_idx = await db.execute(
            select(MarketIndex).where(MarketIndex.normalized_product_name == normalized_name)
        )
        entry = market_idx.scalar_one_or_none()
        if entry:
             avg_market_price = float(entry.avg_price)
    
    # Fallback to raw aggregation if no index (e.g. historical data before backfill)
    if avg_market_price == 0.0:
         avg_price_result = await db.execute(
            select(func.avg(InvoiceItem.unit_price)).where(
                InvoiceItem.product_id == product_id,
                InvoiceItem.unit_price.isnot(None),
            )
        )
         avg_market_price = float(avg_price_result.scalar() or 0.0)

    # 3. Batch-fetch latest price per supplier (single query, replaces N queries)
    # Uses a subquery to get the most recent invoice item price per supplier
    latest_prices_query = (
        select(
            Invoice.supplier_id,
            InvoiceItem.unit_price,
            func.row_number().over(
                partition_by=Invoice.supplier_id,
                order_by=Invoice.created_at.desc(),
            ).label("rn"),
        )
        .join(Invoice, Invoice.id == InvoiceItem.invoice_id)
        .where(
            Invoice.supplier_id.in_(supplier_ids),
            InvoiceItem.product_id == product_id,
            InvoiceItem.unit_price.isnot(None),
        )
        .subquery()
    )

    price_result = await db.execute(
        select(latest_prices_query.c.supplier_id, latest_prices_query.c.unit_price)
        .where(latest_prices_query.c.rn == 1)
    )
    price_map: Dict[UUID, float] = {
        row.supplier_id: float(row.unit_price) for row in price_result
    }

    # 4. Batch-fetch invoice counts per supplier for this merchant (single query)
    count_result = await db.execute(
        select(Invoice.supplier_id, func.count(Invoice.id).label("cnt"))
        .where(
            Invoice.merchant_id == merchant_id,
            Invoice.supplier_id.in_(supplier_ids),
        )
        .group_by(Invoice.supplier_id)
    )
    count_map: Dict[UUID, int] = {
        row.supplier_id: row.cnt for row in count_result
    }

    # 5. Compute scores (only score upsert hits DB inside loop, not avoidable)
    scores = []
    for supplier in suppliers:
        last_price = price_map.get(supplier.id, avg_market_price)
        invoice_count = count_map.get(supplier.id, 0)
        is_current = supplier.id == current_supplier_id

        score = await compute_full_score(
            db=db,
            merchant_id=merchant_id,
            supplier=supplier,
            product_id=product_id,
            unit_price=last_price,
            avg_market_price=avg_market_price,
            is_current_supplier=is_current,
            invoice_count=invoice_count,
        )
        scores.append(score)

    # Sort by total_score descending
    scores.sort(key=lambda s: s.total_score, reverse=True)
    return scores


async def generate_recommendations(
    db: AsyncSession,
    merchant_id: UUID,
    invoice_id: UUID,
) -> List[Recommendation]:
    """Generate supplier recommendations for all items in an invoice."""
    # Get invoice and its items
    invoice_result = await db.execute(
        select(Invoice).where(Invoice.id == invoice_id)
    )
    invoice = invoice_result.scalar_one_or_none()
    if not invoice:
        return []

    items_result = await db.execute(
        select(InvoiceItem).where(InvoiceItem.invoice_id == invoice_id)
    )
    items = items_result.scalars().all()

    recommendations = []
    for item in items:
        if not item.product_id:
            continue

        scores = await compare_suppliers_for_product(
            db=db,
            merchant_id=merchant_id,
            product_id=item.product_id,
            current_supplier_id=invoice.supplier_id,
        )

        if not scores:
            continue

        best = scores[0]

        # Only recommend if best supplier is different from current
        if best.supplier_id == invoice.supplier_id:
            continue

        # Estimate savings
        current_price = float(item.unit_price or 0)
        quantity = float(item.quantity or 1)
        savings = max(0, current_price * quantity * (1 - (1 / max(best.total_score, 0.01))))

        rec = Recommendation(
            merchant_id=merchant_id,
            invoice_id=invoice_id,
            product_id=item.product_id,
            recommended_supplier_id=best.supplier_id,
            current_supplier_id=invoice.supplier_id,
            score_id=best.id,
            savings_estimate=round(savings, 2),
            reason=f"Better value score ({best.total_score:.2f}) — "
                   f"price: {best.price_score:.2f}, "
                   f"reliability: {best.reliability_score:.2f}, "
                   f"delivery: {best.delivery_speed:.2f}",
        )
        db.add(rec)
        recommendations.append(rec)

    await db.flush()
    return recommendations
