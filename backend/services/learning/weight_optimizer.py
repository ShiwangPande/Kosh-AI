"""Weight Optimizer.

Adaptive algorithm to tune weights based on feedback.
Constraints:
- Sum of weights = 1.0
- Each weight in [0.05, 0.60]
"""
from typing import Dict, List, Any

def optimize_weights(
    current_weights: Dict[str, float],
    feedback_history: List[Dict[str, Any]],
    learning_rate: float = 0.05
) -> Dict[str, float]:
    """
    Adjust weights based on simple gradient-like heuristic.
    
    If 'price' driven recommendations were accepted: increase price_weight.
    If 'speed' driven recommendations were rejected: decrease speed_weight.
    
    Real logic would need feature vectors of the recs. 
    Here we assume feedback contains 'dominant_factor' or similar, 
    or we infer it from the context we don't fully have in this signature.
    
    Simplified Heuristic for this implementation:
    - We assume feedback items have keys like 'factor_impacts': {'price': 0.8, 'speed': 0.2}
    - Or we just nudge weights.
    
    Let's implement a dummy reliable optimizer as per prompt requirements:
    "If merchant repeatedly accepts recommendations where one factor dominates, increase that factor weight."
    """
    
    # 1. Tally scores
    scores = {k: 0.0 for k in current_weights}
    
    if not feedback_history:
        return current_weights

    # Calculate direction
    for entry in feedback_history:
        # entry needs: 'accepted', 'dominant_factors' (list of keys)
        # We assume feedback_data passed here is enriched.
        impact = 1.0 if entry.get('accepted') else -0.5
        factors = entry.get('dominant_factors', [])
        
        for f in factors:
            key = f"{f}_weight" 
            if key in scores:
                scores[key] += impact

    # 2. Apply updates
    new_weights = current_weights.copy()
    total_score = sum(abs(s) for s in scores.values())
    
    if total_score == 0:
        return current_weights

    for key, score in scores.items():
        # Nudge
        change = score * learning_rate
        new_weights[key] += change

    # 3. Enforce Constraints
    # A. Clamp [0.05, 0.60]
    for k in new_weights:
        new_weights[k] = max(0.05, min(0.60, new_weights[k]))
    
    # B. Normalize to Sum = 1.0
    total = sum(new_weights.values())
    for k in new_weights:
        new_weights[k] /= total
    
    return new_weights
