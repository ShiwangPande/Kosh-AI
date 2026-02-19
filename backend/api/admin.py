"""Admin API routes — weights, logs, fraud flags, analytics."""
from uuid import UUID
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update, case

from backend.database import get_db
from backend.models.models import (
    Merchant, Supplier, Invoice, Recommendation, ActivityLog, AdminSetting,
)
from backend.schemas.schemas import (
    WeightsUpdate, AdminAnalytics, ActivityLogOut,
    SupplierOut, MerchantOut, PaginatedResponse, MessageResponse,
)
from backend.utils.auth import require_admin
from backend.utils.audit import log_activity

router = APIRouter(prefix="/admin", tags=["Admin"])


# ── Weights ─────────────────────────────────────────────────

@router.get("/weights")
async def get_weights(
    admin: Merchant = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(AdminSetting).where(AdminSetting.key == "value_score_weights")
    )
    setting = result.scalar_one_or_none()
    if not setting:
        return {"credit_score": 0.30, "price_score": 0.25, "reliability_score": 0.20,
                "switching_friction": 0.15, "delivery_speed": 0.10}
    return setting.value


@router.put("/weights", response_model=MessageResponse)
async def update_weights(
    data: WeightsUpdate,
    admin: Merchant = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    total = (data.credit_score + data.price_score + data.reliability_score
             + data.switching_friction + data.delivery_speed)
    if abs(total - 1.0) > 0.01:
        raise HTTPException(status_code=400, detail=f"Weights must sum to 1.0 (got {total:.2f})")

    weights = data.model_dump()
    result = await db.execute(
        select(AdminSetting).where(AdminSetting.key == "value_score_weights")
    )
    setting = result.scalar_one_or_none()

    if setting:
        setting.value = weights
        setting.updated_by = admin.id
    else:
        setting = AdminSetting(
            key="value_score_weights", value=weights,
            description="Value Score weights", updated_by=admin.id,
        )
        db.add(setting)

    await log_activity(
        db, action="admin.update_weights", actor_id=admin.id,
        actor_role="admin", resource_type="admin_settings",
        details=weights,
    )
    await db.flush()
    await db.commit()
    return MessageResponse(message="Weights updated successfully")


# ── Activity Logs ───────────────────────────────────────────

@router.get("/logs", response_model=PaginatedResponse)
async def list_logs(
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
    action: Optional[str] = None,
    admin: Merchant = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    query = select(ActivityLog)
    count_query = select(func.count(ActivityLog.id))

    if action:
        safe_action = action.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        query = query.where(ActivityLog.action.ilike(f"%{safe_action}%"))
        count_query = count_query.where(ActivityLog.action.ilike(f"%{safe_action}%"))

    total = (await db.execute(count_query)).scalar()
    query = query.order_by(ActivityLog.created_at.desc()).offset(
        (page - 1) * per_page
    ).limit(per_page)
    result = await db.execute(query)
    logs = result.scalars().all()

    return PaginatedResponse(
        items=[ActivityLogOut.model_validate(l) for l in logs],
        total=total, page=page, per_page=per_page,
        pages=(total + per_page - 1) // per_page,
    )


# ── Fraud Flagging ──────────────────────────────────────────

@router.post("/merchants/{merchant_id}/flag", response_model=MessageResponse)
async def flag_merchant(
    merchant_id: UUID,
    reason: str = "Suspicious activity",
    admin: Merchant = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Merchant).where(Merchant.id == merchant_id))
    merchant = result.scalar_one_or_none()
    if not merchant:
        raise HTTPException(status_code=404, detail="Merchant not found")

    merchant.is_flagged = True
    merchant.flag_reason = reason

    await log_activity(
        db, action="admin.flag_merchant", actor_id=admin.id,
        actor_role="admin", resource_type="merchant",
        resource_id=merchant_id, details={"reason": reason},
    )
    await db.flush()
    await db.commit()
    return MessageResponse(message=f"Merchant {merchant_id} flagged")


@router.post("/merchants/{merchant_id}/unflag", response_model=MessageResponse)
async def unflag_merchant(
    merchant_id: UUID,
    admin: Merchant = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Merchant).where(Merchant.id == merchant_id))
    merchant = result.scalar_one_or_none()
    if not merchant:
        raise HTTPException(status_code=404, detail="Merchant not found")

    merchant.is_flagged = False
    merchant.flag_reason = None

    await log_activity(
        db, action="admin.unflag_merchant", actor_id=admin.id,
        actor_role="admin", resource_type="merchant", resource_id=merchant_id,
    )
    await db.flush()
    await db.commit()
    return MessageResponse(message=f"Merchant {merchant_id} unflagged")


# ── Supplier Approval ──────────────────────────────────────

@router.post("/suppliers/{supplier_id}/approve", response_model=MessageResponse)
async def approve_supplier(
    supplier_id: UUID,
    admin: Merchant = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Supplier).where(Supplier.id == supplier_id))
    supplier = result.scalar_one_or_none()
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")

    supplier.is_approved = True
    supplier.approved_by = admin.id

    await log_activity(
        db, action="admin.approve_supplier", actor_id=admin.id,
        actor_role="admin", resource_type="supplier", resource_id=supplier_id,
    )
    await db.flush()
    await db.commit()
    return MessageResponse(message=f"Supplier {supplier_id} approved")


# ── Analytics ───────────────────────────────────────────────

@router.get("/analytics", response_model=AdminAnalytics)
async def get_analytics(
    admin: Merchant = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    # P5 fix: single query with conditional counts instead of 7 sequential queries
    result = await db.execute(
        select(
            func.count(Merchant.id).label("total_merchants"),
            func.count(case((Merchant.is_flagged == True, 1))).label("flagged_merchants"),
        )
    )
    merchant_stats = result.one()

    result = await db.execute(
        select(func.count(Supplier.id).label("total_suppliers"))
    )
    total_suppliers = result.scalar()

    result = await db.execute(
        select(
            func.count(Invoice.id).label("total_invoices"),
            func.count(case((Invoice.ocr_status == "completed", 1))).label("invoices_processed"),
            func.count(case((Invoice.ocr_status == "pending", 1))).label("invoices_pending"),
        )
    )
    invoice_stats = result.one()

    recs = (await db.execute(select(func.count(Recommendation.id)))).scalar() or 0
    
    # Calculate realized savings
    savings_res = await db.execute(
        select(func.sum(Recommendation.savings_estimate))
        .where(Recommendation.status == "accepted")
    )
    realized_savings = float(savings_res.scalar() or 0.0)

    return AdminAnalytics(
        total_merchants=merchant_stats.total_merchants,
        total_suppliers=total_suppliers,
        total_invoices=invoice_stats.total_invoices,
        invoices_processed=invoice_stats.invoices_processed,
        invoices_pending=invoice_stats.invoices_pending,
        total_recommendations=recs,
        flagged_merchants=merchant_stats.flagged_merchants,
        realized_savings=realized_savings,
    )
