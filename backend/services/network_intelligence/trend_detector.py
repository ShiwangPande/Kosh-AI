"""Trend Detector.

Identifies significant market movements.
Trigger: > 2 standard deviations deviation from historical mean.
"""
from datetime import datetime, timedelta
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from backend.models.models import AggregatedPrice, MarketTrend

async def detect_market_trends(db: AsyncSession):
    """
    Scan recent aggregated prices for anomalies.
    """
    # Look at last 24h vs previous 30 days
    recent_window = datetime.utcnow() - timedelta(hours=24)
    
    # Get recent aggregations
    recent_res = await db.execute(
        select(AggregatedPrice).where(AggregatedPrice.time_window >= recent_window)
    )
    recent_points = recent_res.scalars().all()
    
    for point in recent_points:
        # Check history for this product/city
        hist_res = await db.execute(
            select(AggregatedPrice)
            .where(
                AggregatedPrice.product_id == point.product_id,
                AggregatedPrice.city == point.city,
                AggregatedPrice.time_window < recent_window
            )
            .order_by(AggregatedPrice.time_window.desc())
            .limit(30) # Last 30 points
        )
        history = hist_res.scalars().all()
        
        if len(history) < 5:
            continue # Not enough history
            
        # Calculate stats
        hist_prices = [h.median_price for h in history]
        mean = sum(hist_prices) / len(hist_prices)
        
        # Simple std dev
        variance = sum((p - mean) ** 2 for p in hist_prices) / len(hist_prices)
        std_dev = variance ** 0.5
        
        if std_dev == 0:
            continue
            
        z_score = (point.median_price - mean) / std_dev
        
        if abs(z_score) > 2.0:
            # Trend Detected
            direction = "UP" if z_score > 0 else "DOWN"
            trend_type = "PRICE_SPIKE" if direction == "UP" else "PRICE_DROP"
            
            trend = MarketTrend(
                product_id=point.product_id,
                city=point.city,
                trend_type=trend_type,
                direction=direction,
                magnitude=abs(z_score),
                confidence=0.8
            )
            db.add(trend)
            
    await db.commit()
