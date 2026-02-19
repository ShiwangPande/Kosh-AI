"""Anomaly Detector.

Detects suspicious patterns in invoices:
- Price deviation > 40% vs market avg
- Quantity spike > 3x average
- New supplier (never seen before)
- Round number pricing (often fake)

Returns:
    risk_score (0-100), flags (List[str])
"""
from typing import Tuple, List
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from backend.models.models import Invoice, InvoiceItem, Supplier

async def detect_anomalies(
    db: AsyncSession,
    invoice_id: UUID,
    items: List[InvoiceItem],
    supplier_id: UUID,
    merchant_id: UUID
) -> Tuple[float, List[str]]:
    """
    Analyze invoice for anomalies.
    Returns (risk_score, list_of_flags)
    """
    flags = []
    risk_score = 0.0
    
    # 1. New Supplier Check
    # Check if merchant has any *other* invoices with this supplier
    prev_invoices = await db.execute(
        select(func.count(Invoice.id)).where(
            Invoice.merchant_id == merchant_id,
            Invoice.supplier_id == supplier_id,
            Invoice.id != invoice_id
        )
    )
    count = prev_invoices.scalar() or 0
    if count == 0:
        flags.append("New Supplier")
        risk_score += 20.0

    # 2. Analyze Items
    for item in items:
        # A. Round Numbers Check (e.g., 500.00, 1000.00)
        # Often suspicious if unit prices are perfectly round large numbers
        price = float(item.unit_price or 0)
        if price > 50 and price.is_integer():
             # Basic heuristic: if it's perfectly integer and > 50
             # We might check if ALL items are round, but per-item check adds up
             pass 

        # B. Price Deviation > 40% vs Market
        if item.product_id:
            # Get avg price for product (excluding this invoice)
            avg_result = await db.execute(
                select(func.avg(InvoiceItem.unit_price)).where(
                    InvoiceItem.product_id == item.product_id,
                    InvoiceItem.id != item.id
                )
            )
            market_price = avg_result.scalar()
            
            if market_price:
                market_price = float(market_price)
                deviation = abs(price - market_price) / market_price
                if deviation > 0.40:
                    flags.append(f"Price Deviation > 40% for item {item.raw_description[:20]}")
                    risk_score += 30.0

        # C. Quantity Spike > 3x Avg
        # Get merchant's avg quantity for this product
        if item.product_id:
            qty_result = await db.execute(
                select(func.avg(InvoiceItem.quantity)).where(
                    InvoiceItem.product_id == item.product_id,
                    Invoice.merchant_id == merchant_id,
                    InvoiceItem.id != item.id
                ).join(Invoice)
            )
            avg_qty = qty_result.scalar()
            
            if avg_qty:
                avg_qty = float(avg_qty)
                if float(item.quantity) > (avg_qty * 3):
                    flags.append(f"Quantity Spike > 3x for item {item.raw_description[:20]}")
                    risk_score += 25.0

    # 3. All Round Numbers Check
    # If every single item has a round integer price, that's suspicious
    all_round = all(float(i.unit_price or 0).is_integer() for i in items if i.unit_price)
    if items and all_round:
        flags.append("All Prices Rounded")
        risk_score += 15.0

    return min(100.0, risk_score), flags
