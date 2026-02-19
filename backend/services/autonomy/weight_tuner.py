"""Weight Tuner.

Adjusts scoring weights automatically.
Constraint: Max 10% change per step. Sum must be 1.0.
"""
from typing import Dict
from backend.models.models import MerchantPreference

class WeightTuner:
    
    @staticmethod
    def adjust_weights(current_weights: Dict[str, float], metric_weakness: str) -> Dict[str, float]:
        """
        Tune weights to improve specific metric.
        If 'acceptance_rate' low, maybe increase 'price_weight' or 'reliability_weight'.
        """
        # Strategy: Increase strongest factor for the goal, decrease others proportionally.
        
        # Map weakness to target weight to boost
        # If acceptance is low, users might want better prices.
        target_map = {
            "acceptance_rate": "price_weight",
            "savings_avg": "price_weight",
            "latency_ms": None # Can't fix latency with weights
        }
        
        target_key = target_map.get(metric_weakness)
        if not target_key or target_key not in current_weights:
            return current_weights
            
        # Tunable step
        step = 0.05 # 5%
        
        new_weights = current_weights.copy()
        
        # Boost target
        old_val = new_weights[target_key]
        new_val = min(old_val + step, 1.0)
        diff = new_val - old_val
        
        new_weights[target_key] = new_val
        
        # Normalize others
        # We need to subtract 'diff' from others safely
        remaining_keys = [k for k in new_weights if k != target_key]
        if not remaining_keys:
             return new_weights
             
        # Distribute extraction
        # Simple approach: subtract diff/N from each, clamping to 0.05
        deduction = diff / len(remaining_keys)
        
        for k in remaining_keys:
            new_weights[k] = max(0.05, new_weights[k] - deduction)
            
        # Re-normalize to ensure exact 1.0 sum
        total = sum(new_weights.values())
        for k in new_weights:
            new_weights[k] = new_weights[k] / total
            
        return new_weights
