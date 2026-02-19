"""Merchant API routes."""
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.database import get_db
from backend.models.models import Merchant
from backend.schemas.schemas import MerchantOut, MerchantUpdate, MessageResponse
from backend.utils.auth import get_current_user
from backend.utils.audit import log_activity

router = APIRouter(prefix="/merchants", tags=["Merchants"])


@router.get("/me", response_model=MerchantOut)
async def get_profile(current_user: Merchant = Depends(get_current_user)):
    return current_user


@router.patch("/me", response_model=MerchantOut)
async def update_profile(
    data: MerchantUpdate,
    current_user: Merchant = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(current_user, key, value)

    await log_activity(
        db, action="merchant.update_profile", actor_id=current_user.id,
        actor_role=current_user.role, resource_type="merchant",
        resource_id=current_user.id, details=update_data,
    )
    await db.flush()
    await db.commit()
    return current_user


@router.get("/{merchant_id}", response_model=MerchantOut)
async def get_merchant(
    merchant_id: UUID,
    current_user: Merchant = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if current_user.role != "admin" and current_user.id != merchant_id:
        raise HTTPException(status_code=403, detail="Access denied")

    result = await db.execute(select(Merchant).where(Merchant.id == merchant_id))
    merchant = result.scalar_one_or_none()
    if not merchant:
        raise HTTPException(status_code=404, detail="Merchant not found")
    return merchant
