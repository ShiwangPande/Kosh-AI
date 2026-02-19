"""
Risk Engine Service.

Evaluates financial transactions for fraud, credit risk, and compliance.
"""
import uuid
from decimal import Decimal
from typing import List, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from backend.models.models import Order, Supplier, Merchant, Score

class RiskDecision(BaseModel):
    decision: str # APPROVE, REVIEW, BLOCK
    score: float # 0-100 (0=Safe, 100=Toxic)
    reasons: List[str]

class RiskEngine:
    
    # Thresholds
    MAX_AUTO_APPROVE_AMOUNT = Decimal("50000.00")
    CRITICAL_RISK_SCORE_THRESHOLD = 80.0
    VELOCITY_LIMIT_1H = 10 # Max orders per hour
    
    @staticmethod
    async def evaluate_transaction(
        db: AsyncSession, 
        merchant_id: uuid.UUID, 
        amount: Decimal, 
        supplier_id: Optional[uuid.UUID]
    ) -> RiskDecision:
        """
        Calculates risk score and returns decision.
        Fail-Closed: Any error should raise exception (blocking tx).
        """
        reasons = []
        score = 0.0
        
        # 1. Start with Baseline Risk (New Account?)
        # For now, base risk 10
        score += 10.0
        
        # 2. Value Check
        if amount > RiskEngine.MAX_AUTO_APPROVE_AMOUNT:
            score += 40.0
            reasons.append(f"High Value Transaction (> {RiskEngine.MAX_AUTO_APPROVE_AMOUNT})")
            
        # 3. Velocity Check (Orders in last hour)
        one_hour_ago = datetime.utcnow() - timedelta(hours=1)
        velocity_query = select(func.count(Order.id)).where(
            Order.merchant_id == merchant_id,
            Order.created_at >= one_hour_ago
        )
        velocity = (await db.execute(velocity_query)).scalar() or 0
        
        if velocity > RiskEngine.VELOCITY_LIMIT_1H:
            score += 50.0
            reasons.append(f"High Velocity ({velocity} orders/hr)")
            
        # 4. Supplier Risk (if known)
        if supplier_id:
             # Check Score table
             supplier_score_q = select(Score).where(
                 Score.merchant_id == merchant_id,
                 Score.supplier_id == supplier_id
             )
             s_score = (await db.execute(supplier_score_q)).scalar_one_or_none()
             
             if s_score:
                 # In Score model, high score is GOOD.
                 # reliability_score is 0-? (Assume 0-100 normalized?)
                 # Let's assume standard is 0-1. So < 0.3 is risky.
                 if s_score.reliability_score < 0.3:
                      score += 30.0
                      reasons.append("Low Supplier Reliability")
        
        # 5. Final Decision
        details_str = ", ".join(reasons)
        decision_str = "APPROVE"
        
        if score >= RiskEngine.CRITICAL_RISK_SCORE_THRESHOLD:
             decision_str = "BLOCK"
        elif score >= 50.0 or amount > RiskEngine.MAX_AUTO_APPROVE_AMOUNT:
             decision_str = "REVIEW"
             
        # 6. LOG BLACK BOX (Data Moat)
        from backend.models.models import RiskDecisionLog
        import json
        
        features = {
            "amount": float(amount),
            "velocity_1h": velocity,
            "base_risk": 10.0,
            "supplier_score": s_score.reliability_score if supplier_id and s_score else None
        }
        
        log = RiskDecisionLog(
            merchant_id=merchant_id,
            risk_score=score,
            decision=decision_str,
            features_json=features
        )
        db.add(log) # Flush happens on caller commit
        
        return RiskDecision(decision=decision_str, score=score, reasons=reasons)

