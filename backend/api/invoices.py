"""Invoice API routes — upload + OCR pipeline trigger."""
from uuid import UUID
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from backend.config import get_settings
from backend.database import get_db
from backend.models.models import Invoice, InvoiceItem, Merchant
from backend.schemas.schemas import (
    InvoiceOut, InvoiceItemOut, PaginatedResponse,
    InvoiceVerification, MessageResponse
)
from backend.utils.auth import get_current_user
from backend.utils.cloudinary_storage import upload_file_to_cloudinary, delete_file_from_cloudinary
from backend.utils.audit import log_activity
from backend.workers.celery_app import celery_app

settings = get_settings()
router = APIRouter(prefix="/invoices", tags=["Invoices"])

ALLOWED_TYPES = {"application/pdf", "image/png", "image/jpeg", "image/jpg", "image/tiff"}

@router.post("/upload", response_model=InvoiceOut, status_code=201)
async def upload_invoice(
    file: UploadFile = File(...),
    supplier_id: Optional[UUID] = None,
    current_user: Merchant = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {file.content_type}. Allowed: {', '.join(ALLOWED_TYPES)}",
        )

    if file.size and file.size > settings.max_upload_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum size: {settings.MAX_UPLOAD_SIZE_MB}MB",
        )

    file_url, file_key = await upload_file_to_cloudinary(file, folder="kosh_ai_invoices")

    invoice = Invoice(
        merchant_id=current_user.id,
        supplier_id=supplier_id,
        file_url=file_url,
        file_key=file_key,
        ocr_status="pending",
    )
    db.add(invoice)
    await db.flush()

    task = celery_app.send_task(
        "backend.workers.ocr_worker.process_invoice_ocr",
        args=[str(invoice.id)],
    )
    invoice.ocr_task_id = task.id

    await log_activity(
        db, action="invoice.upload", actor_id=current_user.id,
        actor_role=current_user.role, resource_type="invoice",
        resource_id=invoice.id,
        details={"file_key": file_key, "supplier_id": str(supplier_id) if supplier_id else None},
    )
    await db.commit()
    return invoice

@router.get("", response_model=PaginatedResponse)
async def list_invoices(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
    current_user: Merchant = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    query = select(Invoice).where(Invoice.merchant_id == current_user.id)
    count_query = select(func.count(Invoice.id)).where(Invoice.merchant_id == current_user.id)

    if status:
        query = query.where(Invoice.ocr_status == status)
        count_query = count_query.where(Invoice.ocr_status == status)

    total_result = await db.execute(count_query)
    total = total_result.scalar()

    query = query.order_by(Invoice.created_at.desc()).offset((page - 1) * per_page).limit(per_page)
    result = await db.execute(query)
    invoices = result.scalars().all()

    return PaginatedResponse(
        items=[InvoiceOut.model_validate(i) for i in invoices],
        total=total,
        page=page,
        per_page=per_page,
        pages=(total + per_page - 1) // per_page,
    )

@router.post("/{invoice_id}/verify", response_model=MessageResponse)
async def verify_invoice(
    invoice_id: UUID,
    verification: InvoiceVerification,
    current_user: Merchant = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from backend.services.validation_pipeline import apply_human_corrections
    from backend.services.comparison_engine import generate_recommendations

    # 1. Check invoice
    result = await db.execute(
        select(Invoice).where(Invoice.id == invoice_id, Invoice.merchant_id == current_user.id)
    )
    invoice = result.scalar_one_or_none()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    # 2. Apply corrections
    corrections_data = [c.model_dump() for c in verification.corrections]
    applied = await apply_human_corrections(
        db, invoice_id, corrections_data, current_user.id
    )

    # 3. Trigger recommendations
    await generate_recommendations(db, current_user.id, invoice_id)

    # 4. Auto-Approve Supplier
    # If the user verifies the invoice, they implicitly trust the supplier.
    await db.refresh(invoice) # Ensure we have latest supplier_id
    if invoice.supplier_id:
        from backend.models.models import Supplier
        supplier_result = await db.execute(select(Supplier).where(Supplier.id == invoice.supplier_id))
        supplier = supplier_result.scalar_one_or_none()
        if supplier and not supplier.is_approved:
            supplier.is_approved = True

    # 5. Live Market Intelligence (Phase 6)
    # Update the pricing graph with verified data
    try:
        from backend.services.market_intelligence import MarketIntelligenceService
        await MarketIntelligenceService.update_index_from_invoice(db, invoice_id)
        
        # 6. Supplier Intelligence Scoring (Phase 8)
        if invoice.supplier_id:
            from backend.services.supplier_scoring import SupplierScoreService
            await SupplierScoreService.update_supplier_score(db, invoice.supplier_id)

    except Exception as e:
        # Don't fail verification if market update fails, just log it
        print(f"Intelligence Update Failed: {e}")

    await db.commit()
    return MessageResponse(
        message=f"Invoice verified and {applied} corrections applied. Recommendations generated."
    )

@router.post("/{invoice_id}/cancel", status_code=200)
async def cancel_invoice_ocr(
    invoice_id: UUID,
    current_user: Merchant = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Invoice).where(
            Invoice.id == invoice_id,
            Invoice.merchant_id == current_user.id,
        )
    )
    invoice = result.scalar_one_or_none()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    if invoice.ocr_status not in ["pending", "processing"]:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot cancel invoice in {invoice.ocr_status} state"
        )

    if invoice.ocr_task_id:
        celery_app.control.revoke(invoice.ocr_task_id, terminate=True)

    invoice.ocr_status = "failed"
    await db.commit()

    await log_activity(
        db, action="invoice.cancel", actor_id=current_user.id,
        actor_role=current_user.role, resource_type="invoice",
        resource_id=invoice_id,
    )
    return {"message": "Processing cancelled"}

@router.get("/{invoice_id}/items", response_model=list[InvoiceItemOut])
async def get_invoice_items(
    invoice_id: UUID,
    current_user: Merchant = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    inv = await db.execute(
        select(Invoice).where(Invoice.id == invoice_id, Invoice.merchant_id == current_user.id)
    )
    if not inv.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Invoice not found")

    result = await db.execute(
        select(InvoiceItem).where(InvoiceItem.invoice_id == invoice_id)
    )
    return result.scalars().all()

@router.get("/{invoice_id}", response_model=InvoiceOut)
async def get_invoice(
    invoice_id: UUID,
    current_user: Merchant = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Invoice).where(
            Invoice.id == invoice_id,
            Invoice.merchant_id == current_user.id,
        )
    )
    invoice = result.scalar_one_or_none()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return invoice

@router.delete("/{invoice_id}", status_code=204)
async def delete_invoice(
    invoice_id: UUID,
    current_user: Merchant = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Invoice).where(
            Invoice.id == invoice_id,
            Invoice.merchant_id == current_user.id,
        )
    )
    invoice = result.scalar_one_or_none()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    if invoice.ocr_status in ["pending", "processing"] and invoice.ocr_task_id:
        celery_app.control.revoke(invoice.ocr_task_id, terminate=True)

    try:
        await delete_file_from_cloudinary(invoice.file_key)
    except Exception:
        pass

    await db.delete(invoice)
    await db.commit()

    await log_activity(
        db, action="invoice.delete", actor_id=current_user.id,
        actor_role=current_user.role, resource_type="invoice",
        resource_id=invoice_id,
        details={"file_key": invoice.file_key},
    )
    return None
