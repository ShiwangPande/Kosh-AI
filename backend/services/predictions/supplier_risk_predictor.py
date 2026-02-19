"""Supplier Risk Predictor.

Estimates probability of delivery issues.
"""
from backend.models.models import SupplierRiskPrediction, Supplier

from .confidence_engine import format_explanation

async def predict_supplier_risk(db, supplier_id) -> SupplierRiskPrediction:
    """
    Predict risk score.
    """
    # 1. Fetch historical performance (Mocked for brevity)
    # Real impl would query SupplierBenchmark or Invoice delays
    late_deliveries_pct = 0.15 # 15% late
    stockout_rate = 0.05
    
    # 2. Calculate Probability
    prob_issue = late_deliveries_pct + stockout_rate
    risk_score = min(100.0, prob_issue * 100 * 2) # amplify 2x
    
    risk_type = "LATE_DELIVERY" if late_deliveries_pct > stockout_rate else "STOCKOUT"
    
    expl = format_explanation({
        "late_delivery_history": 0.7,
        "market_volatility": 0.3
    })
    
    return SupplierRiskPrediction(
        supplier_id=supplier_id,
        risk_type=risk_type,
        probability=round(prob_issue, 2),
        risk_score=round(risk_score, 1),
        explanation=expl
    )
