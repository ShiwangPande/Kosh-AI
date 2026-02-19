"""Price Forecaster.

Predicts future product prices using Exponential Smoothing.
Input: Historical prices (time-series).
"""
from datetime import date, timedelta
import statistics
from typing import List, Tuple
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.models.models import AggregatedPrice, PricePrediction

from .confidence_engine import calculate_confidence, format_explanation

async def forecast_price(
    db: AsyncSession, 
    product_id: str, 
    city: str, 
    horizon_days: int = 7
) -> PricePrediction:
    """
    Generate price forecast.
    """
    # 1. Fetch History (Aggregated Prices)
    # We use AggregatedPrice as source of truth
    query = (
        select(AggregatedPrice)
        .where(AggregatedPrice.product_id == product_id, AggregatedPrice.city == city)
        .order_by(AggregatedPrice.time_window.asc())
        .limit(60) # Last 60 points
    )
    result = await db.execute(query)
    history = result.scalars().all()
    
    if not history:
        return None
        
    prices = [h.median_price for h in history]
    
    # 2. Model: Simple Exponential Smoothing
    alpha = 0.3 # Smoothing factor
    level = prices[0]
    
    for p in prices:
        level = alpha * p + (1 - alpha) * level
        
    predicted_price = level
    
    # 3. Trend Detection (Compare latest vs price 5 periods ago)
    if len(prices) >= 5:
        current_price = prices[-1]
        past_price = prices[-5]
        pct_change = (current_price - past_price) / past_price if past_price != 0 else 0
        
        if pct_change > 0.02:
            direction = "UP"
        elif pct_change < -0.02:
            direction = "DOWN"
        else:
            direction = "STABLE"
    else:
        direction = "STABLE"
        
    # 4. Confidence
    variance = statistics.variance(prices) if len(prices) > 1 else 0.0
    conf_score = calculate_confidence(len(prices), variance)
    
    # 5. Explanation
    explanation = format_explanation({
        "historical_trend": 0.6,
        "recent_volatility": 0.3 if variance > 1.0 else 0.1,
        "data_stability": 0.1
    })
    
    prediction = PricePrediction(
        product_id=product_id,
        city=city,
        target_date=date.today() + timedelta(days=horizon_days),
        predicted_price=round(predicted_price, 2),
        confidence_score=round(conf_score, 2),
        trend_direction=direction,
        explanation=explanation
    )
    
    return prediction
