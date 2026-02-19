"""Supplier API routes."""
from uuid import UUID
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from backend.database import get_db
from backend.models.models import Supplier, Merchant
from backend.schemas.schemas import (
    SupplierCreate, SupplierOut, SupplierUpdate, PaginatedResponse, MessageResponse,
    ProductOut,
)
from backend.utils.auth import get_current_user
from backend.utils.audit import log_activity

router = APIRouter(prefix="/suppliers", tags=["Suppliers"])


def _escape_like(value: str) -> str:
    """Escape SQL LIKE wildcard characters to prevent wildcard injection (S4 fix)."""
    return value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


@router.get("", response_model=PaginatedResponse)
async def list_suppliers(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    category: Optional[str] = None,
    search: Optional[str] = None,
    approved_only: bool = True,
    current_user: Merchant = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    query = select(Supplier)
    count_query = select(func.count(Supplier.id))

    if approved_only:
        query = query.where(Supplier.is_approved == True)
        count_query = count_query.where(Supplier.is_approved == True)
    if category:
        query = query.where(Supplier.category == category)
        count_query = count_query.where(Supplier.category == category)
    if search:
        safe_search = _escape_like(search)
        query = query.where(Supplier.name.ilike(f"%{safe_search}%"))
        count_query = count_query.where(Supplier.name.ilike(f"%{safe_search}%"))

    total_result = await db.execute(count_query)
    total = total_result.scalar()

    query = query.offset((page - 1) * per_page).limit(per_page)
    result = await db.execute(query)
    suppliers = result.scalars().all()

    return PaginatedResponse(
        items=[SupplierOut.model_validate(s) for s in suppliers],
        total=total,
        page=page,
        per_page=per_page,
        pages=(total + per_page - 1) // per_page,
    )


@router.post("", response_model=SupplierOut, status_code=201)
async def create_supplier(
    data: SupplierCreate,
    current_user: Merchant = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    supplier = Supplier(**data.model_dump())
    db.add(supplier)
    await db.flush()

    await log_activity(
        db, action="supplier.create", actor_id=current_user.id,
        actor_role=current_user.role, resource_type="supplier",
        resource_id=supplier.id,
    )
    await db.commit()
    return supplier


@router.get("/{supplier_id}", response_model=SupplierOut)
async def get_supplier(
    supplier_id: UUID,
    current_user: Merchant = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Supplier).where(Supplier.id == supplier_id))
    supplier = result.scalar_one_or_none()
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
    return supplier


@router.patch("/{supplier_id}", response_model=SupplierOut)
async def update_supplier(
    supplier_id: UUID,
    data: SupplierUpdate,
    current_user: Merchant = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Supplier).where(Supplier.id == supplier_id))
    supplier = result.scalar_one_or_none()
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")

    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(supplier, key, value)

    await log_activity(
        db, action="supplier.update", actor_id=current_user.id,
        actor_role=current_user.role, resource_type="supplier",
        resource_id=supplier.id,
    )
    await db.flush()
    await db.commit()
    return supplier


@router.post("/{supplier_id}/score", response_model=SupplierOut)
async def calculate_score(
    supplier_id: UUID,
    current_user: Merchant = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Manually trigger score recalculation."""
    from backend.services.supplier_scoring import SupplierScoreService
    supplier = await SupplierScoreService.update_supplier_score(db, supplier_id)
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
    return supplier


@router.get("/{supplier_id}/products", response_model=PaginatedResponse)
async def get_supplier_products(
    supplier_id: UUID,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    current_user: Merchant = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get products supplied by this supplier (based on invoice history)."""
    # Verify supplier exists
    result = await db.execute(select(Supplier).where(Supplier.id == supplier_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Supplier not found")

    from backend.models.models import Product, InvoiceItem, Invoice
    
    # Query distinct products linked via Invoices -> InvoiceItems
    # Use nested select or join
    # Select P.* from Products P join InvoiceItems II on P.id = II.product_id join Invoices I on I.id = II.invoice_id where I.supplier_id = :sid
    
    stmt = (
        select(Product)
        .join(InvoiceItem, Product.id == InvoiceItem.product_id)
        .join(Invoice, Invoice.id == InvoiceItem.invoice_id)
        .where(Invoice.supplier_id == supplier_id)
        .distinct()
    )
    
    # Pagination on distinct results is tricky in SQLAlchemy + AsyncPG sometimes
    # But let's try standard approach
    
    # Count
    count_stmt = (
        select(func.count(func.distinct(Product.id)))
        .join(InvoiceItem, Product.id == InvoiceItem.product_id)
        .join(Invoice, Invoice.id == InvoiceItem.invoice_id)
        .where(Invoice.supplier_id == supplier_id)
    )
    total_result = await db.execute(count_stmt)
    total = total_result.scalar() or 0
    
    # Fetch
    stmt = stmt.offset((page - 1) * per_page).limit(per_page)
    result = await db.execute(stmt)
    products = result.scalars().all()
    
    # We need a Product schema. SupplierOut is not it.
    # Reuse Product schema if available, or create generic one.
    # backend/schemas/schemas.py likely has ProductOut?
    # I need to check schemas.py.
    # For now, I'll return generic dict or define local schema if needed.
    # Assuming ProductOut exists.
    from backend.schemas.schemas import ProductOut
    
    return PaginatedResponse(
        items=[ProductOut.model_validate(p) for p in products],
        total=total,
        page=page,
        per_page=per_page,
        pages=(total + per_page - 1) // per_page,
    )
