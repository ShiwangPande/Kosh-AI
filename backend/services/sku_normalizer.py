"""SKU Normalizer & Matcher.

Handles:
- Text normalization (lowercase, punctuation, stopwords)
- Fuzzy matching against existing products
- Auto-creation of products if match confidence < threshold
"""
import re
import unicodedata
from difflib import SequenceMatcher
from typing import Tuple, Optional, List

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_

from backend.models.models import Product

# Stopwords to remove
STOPWORDS = {
    "the", "a", "an", "of", "and", "or", "in", "for", "with", "to", "from", "by",
    "piece", "pcs", "pkg", "set", "box", "case", "carton"
}

def normalize_text(raw_text: str) -> str:
    """
    1. Lowercase
    2. Strip punctuation
    3. Remove stopwords
    """
    if not raw_text:
        return ""
    
    # 1. Unicode normalization & Lowercase
    text = unicodedata.normalize("NFKD", raw_text).lower().strip()
    
    # 2. Strip punctuation (keep alphanumeric and spaces)
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    
    # 3. Remove stopwords & collapse whitespace
    words = [w for w in text.split() if w not in STOPWORDS and len(w) > 1]
    return " ".join(words)


def compute_similarity(a: str, b: str) -> float:
    """Return 0.0 - 1.0 similarity ratio."""
    return SequenceMatcher(None, a, b).ratio()


async def find_or_create_product(
    db: AsyncSession,
    raw_name: str,
    threshold: float = 0.85
) -> Tuple[Product, float, bool]:
    """
    Find best match for raw_name. 
    If max_score < threshold, auto-create new Product.
    
    Returns:
        (Product, confidence_score, is_newly_created)
    """
    normalized = normalize_text(raw_name)
    if not normalized:
        # Fallback for empty/garbage strings: create as-is
        new_prod = Product(name=raw_name, normalized_name=raw_name)
        db.add(new_prod)
        await db.flush()
        return new_prod, 1.0, True

    # 1. Exact Match via DB (fast)
    result = await db.execute(
        select(Product).where(Product.normalized_name == normalized)
    )
    exact_match = result.scalar_one_or_none()
    if exact_match:
        return exact_match, 1.0, False

    # 2. Candidate Search (Prefix/Word overlap) - to avoid full scan
    words = normalized.split()
    candidates = []
    if words:
        conditions = []
        # Match if starts with first word OR contains first 3 chars of first word
        trunc = words[0][:4]
        conditions.append(Product.normalized_name.ilike(f"%{trunc}%"))
        
        result = await db.execute(select(Product).where(or_(*conditions)).limit(200))
        candidates = result.scalars().all()
    
    # 3. Fuzzy Match
    best_match = None
    best_score = 0.0
    
    for prod in candidates:
        score = compute_similarity(normalized, prod.normalized_name)
        if score > best_score:
            best_score = score
            best_match = prod

    # 4. Decision
    if best_match and best_score >= threshold:
        return best_match, best_score, False
    
    # 5. Auto-create
    # Simple keyword-based categorization
    category = "uncategorized"
    cat_map = {
        "food": ["apple", "banana", "tomato", "onion", "milk", "bread", "grocery", "veg", "fruit"],
        "electronics": ["cable", "baterry", "charger", "led", "wire", "switch", "sensor"],
        "pharmacy": ["tablet", "capsule", "syrup", "medicine", "injection", "mask", "bandage"],
        "fmcg": ["soap", "shampoo", "paste", "detergent", "oil", "shave"],
    }
    
    for cat, keywords in cat_map.items():
        if any(kw in normalized for kw in keywords):
            category = cat
            break

    new_product = Product(
        name=raw_name,
        normalized_name=normalized,
        category=category
    )
    db.add(new_product)
    await db.flush()
    
    return new_product, 1.0, True
