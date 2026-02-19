"""Restock Predictor.

Calculates optimal reorder time.
Logic: Reorder Date = (Current Stock / Daily Velocity) - Lead Time.
"""
from datetime import date, timedelta
from backend.models.models import RestockPrediction, Product, Merchant

from .demand_forecaster import forecast_demand
from .confidence_engine import format_explanation

async def predict_restock(
    db, 
    merchant_id, 
    product_id, 
    current_stock: int, 
    lead_time_days: int = 3
) -> RestockPrediction:
    """
    Predict when to restock.
    """
    # 1. Get Demand Forecast (Velocity)
    demand_pred = await forecast_demand(db, merchant_id, product_id)
    
    # Daily sales velocity
    if demand_pred.expected_quantity <= 0:
        velocity = 0.5 # Fallback minimal movement
    else:
        velocity = demand_pred.expected_quantity / 7.0
        
    # 2. Days of coverage
    if velocity == 0:
        days_coverage = 999
    else:
        days_coverage = current_stock / velocity
        
    # 3. Reorder Point
    # If we have 10 days stock, and lead time 3 days, we order in 7 days.
    # Buffer: 2 days safety stock
    buffer_days = 2
    days_until_reorder = days_coverage - lead_time_days - buffer_days
    
    if days_until_reorder < 0:
        days_until_reorder = 0 # Urgent!
        urgency = 100.0
    else:
        urgency = max(0, 100 - (days_until_reorder * 10))
        
    reorder_date = date.today() + timedelta(days=int(days_until_reorder))
    
    # 4. Recommended Qty
    # Target 14 days stock
    target_days = 14
    needed = (velocity * target_days) - (current_stock - (velocity * lead_time_days))
    if needed < 0: needed = 0
    
    expl = format_explanation({
        "sales_velocity": 0.5,
        "lead_time": 0.3, 
        "current_stock": 0.2
    })
    
    return RestockPrediction(
        merchant_id=merchant_id,
        product_id=product_id,
        recommended_date=reorder_date,
        recommended_quantity=round(needed, 0),
        urgency_score=round(urgency, 1),
        explanation=expl
    )
