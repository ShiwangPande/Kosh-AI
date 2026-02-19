"""Market Price Engine.

Computes benchmark prices from aggregated invoice data.
"""
from datetime import datetime, timedelta
import statistics
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from backend.models.models import InvoiceItem, Invoice, AggregatedPrice, Product, Merchant

from .data_anonymizer import check_privacy_threshold

async def update_market_prices(db: AsyncSession, lookback_hours: int = 24):
    """
    Aggregate prices for the last window.
    Group by: Product, City.
    Compute: Median, P25, P75, Volatility.
    Save to AggregatedPrice if privacy check passes.
    """
    window_start = datetime.utcnow() - timedelta(hours=lookback_hours)
    
    # 1. Fetch raw data (Invoice Items joined with Invoice and Merchant)
    # We need product_id, price, merchant_id, merchant_city
    query = (
        select(
            InvoiceItem.product_id,
            InvoiceItem.unit_price,
            Merchant.id.label("merchant_id"),
            Merchant.city
        )
        .join(Invoice, InvoiceItem.invoice_id == Invoice.id)
        .join(Merchant, Invoice.merchant_id == Merchant.id)
        .where(Invoice.invoice_date >= window_start)
    )
    
    result = await db.execute(query)
    rows = result.all()
    
    # 2. Group data in memory (for simplicity, or use complex SQL group by)
    # Grouping key: (product_id, city)
    grouped_data = {}
    
    for row in rows:
        key = (row.product_id, row.city)
        if key not in grouped_data:
            grouped_data[key] = {
                "prices": [],
                "merchants": set()
            }
        grouped_data[key]["prices"].append(row.unit_price)
        grouped_data[key]["merchants"].add(row.merchant_id)
        
    # 3. Compute Stats and Save
    new_records = []
    
    for (prod_id, city), data in grouped_data.items():
        merchant_count = len(data["merchants"])
        prices = sorted(data["prices"])
        
        # Privacy Rule
        if not check_privacy_threshold(merchant_count):
            continue
            
        if len(prices) < 2:
            # Need at least 2 points for variance
            continue

        median = float(statistics.median(prices))
        # quantiles returns list of cut points. 
        # For P25, P75 we can use quantiles(n=4) -> [25, 50, 75]
        # Or simplistic index
        if len(prices) >= 4:
            quants = statistics.quantiles(prices, n=4)
            p25 = quants[0]
            p75 = quants[2]
        else:
            p25 = prices[0]
            p75 = prices[-1]
            
        volatility = float(statistics.stdev(prices))
        
        record = AggregatedPrice(
            product_id=prod_id,
            city=city,
            time_window=window_start,
            median_price=median,
            p25_price=p25,
            p75_price=p75,
            volatility=volatility,
            data_points=len(prices),
            merchant_count=merchant_count
        )
        new_records.append(record)
        
    if new_records:
        db.add_all(new_records)
        await db.commit()
    
    return len(new_records)
