"""SKU extraction + normalization logic."""
import re
import unicodedata
from typing import Optional, List, Tuple
from difflib import SequenceMatcher

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from backend.models.models import Product

# ── Maximum candidates to load for fuzzy matching ───────────
_MAX_CANDIDATES = 200


def normalize_sku_name(raw_name: str) -> str:
    """Normalize a product/SKU name for matching.

    Steps:
    1. Unicode normalization
    2. Lowercase
    3. Remove special characters
    4. Collapse whitespace
    5. Remove common filler words
    """
    text = unicodedata.normalize("NFKD", raw_name)
    text = text.lower().strip()
    # Remove special chars except alphanumeric and spaces
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    # Remove filler words
    fillers = {"the", "a", "an", "of", "and", "or", "in", "for", "with", "to", "from", "by"}
    words = [w for w in text.split() if w not in fillers]
    # Collapse whitespace
    text = " ".join(words)
    return text


def compute_similarity(a: str, b: str) -> float:
    """Compute string similarity between two normalized names (0.0 - 1.0)."""
    return SequenceMatcher(None, a, b).ratio()


async def match_product(
    raw_description: str,
    db: AsyncSession,
    min_confidence: float = 0.6,
) -> Tuple[Optional[Product], float]:
    """Match a raw invoice item description to a product in the catalog.

    Uses a multi-step strategy to avoid full table scans (SC1 fix):
    1. Exact normalized_name match (indexed, O(1))
    2. Prefix-based LIKE search (indexed, narrows candidates)
    3. Word-overlap fuzzy match on limited candidate set

    For production at scale (10k+ products), consider enabling
    PostgreSQL pg_trgm extension and using:
        Product.normalized_name.op('%')(search_term)
    with a GIN/GiST trigram index.
    """
    normalized = normalize_sku_name(raw_description)

    # Step 1: Exact normalized_name match (fast, indexed)
    result = await db.execute(
        select(Product).where(Product.normalized_name == normalized)
    )
    exact = result.scalar_one_or_none()
    if exact:
        return exact, 1.0

    # Step 2: Build candidate set using word overlap (avoids full scan)
    words = normalized.split()
    if not words:
        return None, 0.0

    # Search for products whose normalized name starts with the first word
    # or contains any of the significant words (first 3)
    conditions = [Product.normalized_name.ilike(f"{words[0]}%")]
    for word in words[:3]:
        if len(word) >= 3:  # Only match on meaningful words
            conditions.append(Product.normalized_name.ilike(f"%{word}%"))

    result = await db.execute(
        select(Product)
        .where(or_(*conditions))
        .limit(_MAX_CANDIDATES)
    )
    candidates = result.scalars().all()

    # Step 3: Fuzzy match on the narrowed candidate set
    best_match = None
    best_score = 0.0

    for product in candidates:
        score = compute_similarity(normalized, product.normalized_name)
        if score > best_score:
            best_score = score
            best_match = product

    if best_match and best_score >= min_confidence:
        return best_match, best_score

    return None, 0.0


async def create_or_match_product(
    raw_description: str,
    db: AsyncSession,
    category: Optional[str] = None,
) -> Tuple[Product, float]:
    """Match to existing product or create a new one.

    Returns (product, confidence). Confidence = 1.0 for new products.
    """
    product, confidence = await match_product(raw_description, db)

    if product:
        return product, confidence

    # Create new product
    normalized = normalize_sku_name(raw_description)
    new_product = Product(
        name=raw_description.strip(),
        normalized_name=normalized,
        category=category,
    )
    db.add(new_product)
    await db.flush()
    return new_product, 1.0
