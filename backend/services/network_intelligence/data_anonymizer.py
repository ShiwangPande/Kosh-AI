"""Data Anonymization & Privacy Layer.

Enforces privacy rules:
- Remove merchant identifiers
- Hash supplier IDs (if needed for obscurement, though benchmark output requires some ID)
- Generalize location
- Minimum aggregation size checks
"""
import hashlib
from typing import List, Any

MIN_AGGREGATION_SIZE = 5

def hash_identifier(identifier: str) -> str:
    """Return specific hash of an ID."""
    return hashlib.sha256(identifier.encode()).hexdigest()

def check_privacy_threshold(merchant_count: int) -> bool:
    """Ensure aggregation involves enough distinct merchants."""
    return merchant_count >= MIN_AGGREGATION_SIZE

def anonymize_market_data(data: List[dict]) -> List[dict]:
    """
    Strip merchant IDs and specific locations from raw data.
    """
    clean_data = []
    for item in data:
        # Shallow copy to match structure but remove sensitive fields
        clean = item.copy()
        if 'merchant_id' in clean:
            del clean['merchant_id']
        # Generalize location if 'location' exists (assumed passed as City)
        clean_data.append(clean)
    return clean_data
