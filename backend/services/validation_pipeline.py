"""Data validation pipeline — confidence scoring, human correction queue, verification workflow."""
import logging
from typing import Optional, List, Dict, Tuple
from uuid import UUID
from enum import Enum

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func

from backend.models.models import Invoice, InvoiceItem, Product

logger = logging.getLogger("kosh.validation")


# ── Confidence Thresholds ──────────────────────────────────

class ConfidenceLevel(Enum):
    HIGH = "high"         # ≥ 0.85 — auto-accept
    MEDIUM = "medium"     # 0.60–0.84 — flag for review
    LOW = "low"           # < 0.60 — requires human correction


CONFIDENCE_THRESHOLDS = {
    "auto_accept": 0.85,
    "needs_review": 0.60,
    "reject": 0.30,
}


def classify_confidence(score: float) -> ConfidenceLevel:
    """Classify an OCR confidence score into action tiers."""
    if score >= CONFIDENCE_THRESHOLDS["auto_accept"]:
        return ConfidenceLevel.HIGH
    elif score >= CONFIDENCE_THRESHOLDS["needs_review"]:
        return ConfidenceLevel.MEDIUM
    else:
        return ConfidenceLevel.LOW


# ── Item-level validation ─────────────────────────────────

def validate_line_item(item_data: dict) -> Tuple[bool, List[str], float]:
    """Validate a single parsed line item.

    Returns: (is_valid, issues, quality_score)
    """
    issues = []
    score = 1.0

    desc = item_data.get("description", "").strip()
    qty = item_data.get("quantity")
    unit_price = item_data.get("unit_price")
    total_price = item_data.get("total_price")

    # Check description
    if not desc or len(desc) < 2:
        issues.append("Missing or too-short description")
        score -= 0.3
    elif len(desc) > 500:
        issues.append("Description suspiciously long (possible OCR merge)")
        score -= 0.1

    # Check numeric fields
    if qty is not None:
        if qty <= 0:
            issues.append(f"Invalid quantity: {qty}")
            score -= 0.2
        elif qty > 100000:
            issues.append(f"Suspiciously large quantity: {qty}")
            score -= 0.1
    else:
        issues.append("Missing quantity")
        score -= 0.15

    if unit_price is not None:
        if unit_price <= 0:
            issues.append(f"Invalid unit price: {unit_price}")
            score -= 0.2
        elif unit_price > 10_000_000:
            issues.append(f"Suspiciously high price: {unit_price}")
            score -= 0.1
    else:
        issues.append("Missing unit price")
        score -= 0.15

    # Cross-check: qty × unit_price ≈ total_price
    if qty and unit_price and total_price:
        expected = qty * unit_price
        tolerance = max(expected * 0.05, 1.0)  # 5% or ₹1
        if abs(expected - total_price) > tolerance:
            issues.append(f"Price mismatch: {qty}×{unit_price}={expected:.2f} ≠ {total_price}")
            score -= 0.15

    return (len(issues) == 0, issues, max(0, score))


# ── Invoice-level validation ──────────────────────────────

def validate_invoice_data(
    ocr_confidence: float,
    line_items: List[dict],
    total_amount: Optional[float] = None,
) -> Dict:
    """Validate entire invoice OCR output.

    Returns validation report with action recommendation.
    """
    report = {
        "ocr_confidence": ocr_confidence,
        "confidence_level": classify_confidence(ocr_confidence).value,
        "item_count": len(line_items),
        "valid_items": 0,
        "flagged_items": 0,
        "issues": [],
        "item_validations": [],
        "action": "reject",  # Start pessimistic, upgrade as we validate
        "overall_quality": 0.0,
    }

    if not line_items:
        report["issues"].append("No line items extracted")
        report["action"] = "needs_review"
        report["overall_quality"] = 0.0
        return report

    item_scores = []
    for i, item in enumerate(line_items):
        is_valid, issues, quality = validate_line_item(item)
        report["item_validations"].append({
            "index": i,
            "description": item.get("description", "")[:100],
            "is_valid": is_valid,
            "issues": issues,
            "quality_score": round(quality, 2),
        })
        if is_valid:
            report["valid_items"] += 1
        else:
            report["flagged_items"] += 1
        item_scores.append(quality)

    # Overall quality = weighted avg of OCR confidence and item quality
    avg_item_quality = sum(item_scores) / len(item_scores) if item_scores else 0
    report["overall_quality"] = round(
        0.4 * ocr_confidence + 0.6 * avg_item_quality, 3
    )

    # Total amount cross-check
    if total_amount and line_items:
        items_total = sum(
            item.get("total_price", 0) or 0 for item in line_items
        )
        if items_total > 0:
            diff_pct = abs(items_total - total_amount) / total_amount
            if diff_pct > 0.1:
                report["issues"].append(
                    f"Total mismatch: items sum ₹{items_total:.2f} vs invoice ₹{total_amount:.2f} "
                    f"({diff_pct*100:.1f}% off)"
                )

    # Determine action
    if report["overall_quality"] >= CONFIDENCE_THRESHOLDS["auto_accept"]:
        report["action"] = "auto_accept"
    elif report["overall_quality"] >= CONFIDENCE_THRESHOLDS["reject"]:
        report["action"] = "needs_review"
    else:
        report["action"] = "reject"

    # Override: too many flagged items
    if report["item_count"] > 0:
        flagged_ratio = report["flagged_items"] / report["item_count"]
        if flagged_ratio > 0.5:
            report["action"] = "needs_review"
            report["issues"].append(f"{report['flagged_items']}/{report['item_count']} items flagged")

    return report


# ── Verification Queue ─────────────────────────────────────

async def enqueue_for_verification(
    db: AsyncSession,
    invoice_id: UUID,
    validation_report: dict,
):
    """Mark an invoice as needing human verification."""
    from backend.models.models import ActivityLog

    await db.execute(
        update(Invoice)
        .where(Invoice.id == invoice_id)
        .values(ocr_status="needs_review")
    )

    log = ActivityLog(
        action="invoice.needs_verification",
        resource_type="invoice",
        resource_id=invoice_id,
        details={
            "overall_quality": validation_report["overall_quality"],
            "confidence_level": validation_report["confidence_level"],
            "flagged_items": validation_report["flagged_items"],
            "issues": validation_report["issues"][:10],
        },
    )
    db.add(log)
    await db.flush()

    logger.info(f"Invoice {invoice_id} queued for verification "
                f"(quality={validation_report['overall_quality']:.2f})")


async def apply_human_corrections(
    db: AsyncSession,
    invoice_id: UUID,
    corrections: List[Dict],
    reviewer_id: UUID,
) -> int:
    """Apply human corrections to invoice items.

    corrections = [{"item_id": "...", "description": "...", "quantity": ..., "unit_price": ...}]
    """
    applied = 0
    for correction in corrections:
        item_id = correction.get("item_id")
        if not item_id:
            continue

        update_data = {}
        if "description" in correction:
            update_data["raw_description"] = correction["description"]
        if "quantity" in correction:
            update_data["quantity"] = correction["quantity"]
        if "unit_price" in correction:
            update_data["unit_price"] = correction["unit_price"]
        if "total_price" in correction:
            update_data["total_price"] = correction["total_price"]

        if update_data:
            await db.execute(
                update(InvoiceItem)
                .where(InvoiceItem.id == item_id, InvoiceItem.invoice_id == invoice_id)
                .values(**update_data)
            )
            applied += 1

    # Mark invoice as verified
    await db.execute(
        update(Invoice)
        .where(Invoice.id == invoice_id)
        .values(ocr_status="verified")
    )

    from backend.utils.audit import log_activity
    await log_activity(
        db, action="invoice.human_corrected", actor_id=reviewer_id,
        actor_role="admin", resource_type="invoice", resource_id=invoice_id,
        details={"corrections_applied": applied},
    )
    await db.flush()

    logger.info(f"Invoice {invoice_id}: {applied} corrections applied by {reviewer_id}")
    return applied


# ── Quality metrics ────────────────────────────────────────

async def get_data_quality_stats(db: AsyncSession) -> dict:
    """Get aggregate data quality statistics."""
    total = (await db.execute(
        select(func.count(Invoice.id)).where(Invoice.ocr_status.in_(["completed", "verified", "needs_review"]))
    )).scalar() or 0

    verified = (await db.execute(
        select(func.count(Invoice.id)).where(Invoice.ocr_status == "verified")
    )).scalar() or 0

    needs_review = (await db.execute(
        select(func.count(Invoice.id)).where(Invoice.ocr_status == "needs_review")
    )).scalar() or 0

    avg_confidence = (await db.execute(
        select(func.avg(Invoice.ocr_confidence)).where(Invoice.ocr_confidence.isnot(None))
    )).scalar() or 0

    return {
        "total_processed": total,
        "auto_accepted": total - verified - needs_review,
        "human_verified": verified,
        "pending_review": needs_review,
        "avg_confidence": round(float(avg_confidence), 3),
        "verification_rate": round(verified / total, 3) if total else 0,
    }
