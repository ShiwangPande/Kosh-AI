"""Supplier Scoring Engine.

Calculates normalized 0-100 scores for various supplier metrics:
- Delivery Timeliness (avg_delivery_days)
- Price Competitiveness (vs market avg)
- Reliability (manual score + history)
- Merchant Rating (manual inputs)

Usage:
    score = await calculate_supplier_score(supplier, db)
"""
from typing import Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from backend.models.models import Supplier, Invoice, InvoiceItem


async def calculate_supplier_score(
    supplier: Supplier,
    db: AsyncSession,
) -> Dict[str, Any]:
    """Calculate detailed supplier score breakdown."""
    
    # 1. Delivery Score (0-100) — Lower days is better
    # Benchmark: 1 day = 100, 14 days = 0
    days = supplier.avg_delivery_days or 7
    delivery_score = max(0, min(100, 100 - (days - 1) * (100 / 13)))

    # 2. Reliability Score (0-100) — Base from manual score
    # Normalize 0.0-1.0 to 0-100
    reliability_base = (supplier.reliability_score or 0.5) * 100
    
    # Adjust based on successful invoice count (Bonus up to +20)
    # 50+ invoices = max bonus
    invoice_count_result = await db.execute(
        select(func.count(Invoice.id)).where(
            Invoice.supplier_id == supplier.id,
            Invoice.ocr_status == "completed"
        )
    )
    invoice_count = invoice_count_result.scalar() or 0
    reliability_bonus = min(20, invoice_count * 0.4)
    reliability_final = min(100, reliability_base + reliability_bonus)

    # 3. Credit Terms Score (0-100) — Higher is better
    # Benchmark: 0 days = 0, 90 days = 100
    terms = supplier.credit_terms or 0
    credit_score = min(100, (terms / 90.0) * 100)

    # 4. Overall Weighted Score
    # Weights: Reliability (40%), Delivery (30%), Credit (30%)
    overall = (
        0.40 * reliability_final +
        0.30 * delivery_score +
        0.30 * credit_score
    )

    return {
        "overall_score": round(overall, 2),
        "breakdown": {
            "delivery_score": round(delivery_score, 2),
            "reliability_score": round(reliability_final, 2),
            "credit_score": round(credit_score, 2),
        },
        "metrics": {
            "avg_delivery_days": days,
            "invoice_count": invoice_count,
            "credit_terms": terms,
        }
    }
