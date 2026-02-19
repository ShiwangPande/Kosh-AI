from uuid import UUID
from typing import List, Optional
from datetime import date, datetime
import random

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from sqlalchemy.orm import selectinload
from pydantic import BaseModel

from backend.database import get_db
from backend.models.models import Order, OrderItem, Supplier, Merchant, Product
from backend.utils.auth import get_current_user
from backend.utils.audit import log_activity
from backend.schemas.schemas import PaginatedResponse, SupplierOut

class OrderItemOut(BaseModel):
    id: UUID
    product_id: Optional[UUID] = None
    description: str
    quantity: float
    unit_price: float
    total_price: float

    class Config:
        from_attributes = True

class OrderOut(BaseModel):
    id: UUID
    po_number: Optional[str]
    supplier_id: Optional[UUID]
    status: str
    total_amount: float
    expected_delivery_date: Optional[date]
    created_at: datetime
    items: List[OrderItemOut] = []
    supplier: Optional[SupplierOut] = None
    
    class Config:
        from_attributes = True

class OrderItemCreate(BaseModel):
    product_id: Optional[UUID] = None
    description: str
    quantity: float
    unit_price: float

class OrderCreate(BaseModel):
    supplier_id: UUID
    expected_delivery_date: Optional[date] = None
    items: List[OrderItemCreate]

router = APIRouter(prefix="/orders", tags=["Orders"])

@router.post("", response_model=OrderOut, status_code=201)
async def create_order(
    data: OrderCreate,
    current_user: Merchant = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Generate PO Number
    po_number = f"PO-{random.randint(10000, 99999)}"
    
    total_amount = sum(item.quantity * item.unit_price for item in data.items)
    
    new_order = Order(
        merchant_id=current_user.id,
        supplier_id=data.supplier_id,
        po_number=po_number,
        status="pending",
        total_amount=total_amount,
        expected_delivery_date=data.expected_delivery_date
    )
    db.add(new_order)
    await db.flush()
    
    for item_data in data.items:
        item = OrderItem(
            order_id=new_order.id,
            product_id=item_data.product_id,
            description=item_data.description,
            quantity=item_data.quantity,
            unit_price=item_data.unit_price,
            total_price=item_data.quantity * item_data.unit_price
        )
        db.add(item)
    
    await db.commit()
        
    # Eager load items AND supplier for response
    result = await db.execute(
        select(Order)
        .where(Order.id == new_order.id)
        .options(selectinload(Order.items), selectinload(Order.supplier))
    )
    detailed_order = result.scalar_one()

    await log_activity(db, "order.create", current_user.id, current_user.role, "order", new_order.id)
    
    return detailed_order

@router.get("", response_model=PaginatedResponse)
async def list_orders(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
    current_user: Merchant = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    query = select(Order).where(Order.merchant_id == current_user.id)
    
    if status:
        query = query.where(Order.status == status)
    
    query = query.order_by(desc(Order.created_at))
    
    # Pagination logic (simplified)
    # Load supplier too
    result = await db.execute(
        query.offset((page-1)*per_page).limit(per_page)
        .options(selectinload(Order.items), selectinload(Order.supplier))
    )
    orders = result.scalars().all()
    
    # Total count (simplified)
    # total = ...
    
    return PaginatedResponse(
        items=[OrderOut.model_validate(o) for o in orders],
        total=len(orders), # Todo: Fix count
        page=page,
        per_page=per_page,
        pages=1
    )

@router.get("/{order_id}", response_model=OrderOut)
async def get_order(
    order_id: UUID,
    current_user: Merchant = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Order)
        .where(Order.id == order_id)
        .where(Order.merchant_id == current_user.id)
        .options(selectinload(Order.items), selectinload(Order.supplier))
    )
    order = result.scalar_one_or_none()
    
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
        
    return order
