"""Confidence Engine & Explainability.

Utilities for scoring predictions and generating explanations.
"""
import math
from typing import Dict, Any, List

def calculate_confidence(data_points: int, variance: float, min_points: int = 10) -> float:
    """
    Calculate confidence score (0.0 - 1.0).
    - Penalize low data volume.
    - Penalize high variance.
    """
    if data_points < 3:
        return 0.1
    
    # Volume score: sigmoid-like growth
    vol_score = min(1.0, data_points / min_points)
    
    # Variance score: inverse of relative variance (coefficient of variation approx)
    # Simplified: if variance is high relative to mean, confidence drops
    # Here we assume variance is passed.
    # We map variance to 0-1 penalty.
    # Placeholder: Assuming normalized variance or just heuristic
    var_score = 1.0 / (1.0 + math.log(1.0 + variance))
    
    return vol_score * var_score

def format_explanation(factors: Dict[str, float]) -> Dict[str, Any]:
    """
    Format contributing factors.
    factors: {"seasonality": 0.4, "trend": 0.2}
    """
    # Normalize weights
    total = sum(abs(v) for v in factors.values())
    if total == 0:
        normalized = factors
    else:
        normalized = {k: round(v / total, 2) for k, v in factors.items()}
        
    # Sort by impact
    sorted_factors = sorted(normalized.items(), key=lambda x: abs(x[1]), reverse=True)
    
    return {
        "factors": [{"name": k, "weight": v} for k, v in sorted_factors],
        "primary_driver": sorted_factors[0][0] if sorted_factors else "None"
    }
