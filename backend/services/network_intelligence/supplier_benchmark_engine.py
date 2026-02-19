"""Supplier Benchmark Engine.

Scores suppliers across the network and generates rankings.
Metrics: Price Competitiveness, Delivery Reliability, Fulfillment Accuracy, Retention.
"""
from datetime import datetime
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from backend.models.models import Supplier, Invoice, InvoiceItem, SupplierBenchmark, Merchant

async def update_supplier_benchmarks(db: AsyncSession):
    """
    Recompute scores for all suppliers and update network rankings.
    """
    # 1. Fetch performance stats per supplier (grouped by city)
    # Simplified logic: 
    # - Price Score: avg unit_price vs market median
    # - Reliability: on-time delivery rate (mocked)
    # - Accuracy: 1.0 (mocked)
    
    # We iterate cities first to rank within city
    cities_res = await db.execute(select(Merchant.city).distinct())
    cities = cities_res.scalars().all()
    
    for city in cities:
        if not city: continue
        
        # Get suppliers active in this city (via Invoices -> Merchant.city)
        # This join is complex. We simplify by iterating known suppliers.
        
        suppliers_res = await db.execute(select(Supplier))
        suppliers = suppliers_res.scalars().all()
        
        city_scores = []
        
        for sup in suppliers:
            # Check if active in city
            # Calculate metrics
            price_score = 80.0 # Placeholder calculation
            reliability = 90.0
            accuracy = 95.0
            retention = 85.0
            
            total_score = (price_score + reliability + accuracy + retention) / 4
            
            city_scores.append({
                "supplier_id": sup.id,
                "score": total_score,
                "metrics": (price_score, reliability, accuracy, retention)
            })
            
        # Rank
        city_scores.sort(key=lambda x: x["score"], reverse=True)
        total = len(city_scores)
        
        for rank, item in enumerate(city_scores, 1):
            # Save Benchmark
            (p, r, a, ret) = item["metrics"]
            
            record = SupplierBenchmark(
                supplier_id=item["supplier_id"],
                city=city,
                price_competitiveness=p,
                delivery_reliability=r,
                fulfillment_accuracy=a,
                merchant_retention=ret,
                network_rank=rank,
                total_suppliers_in_region=total
            )
            db.add(record)
            
    await db.commit()
