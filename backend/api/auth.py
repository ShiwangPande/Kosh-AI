"""Auth API routes — register, login, refresh, me."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.database import get_db
from backend.models.models import Merchant
from backend.schemas.schemas import (
    MerchantRegister, MerchantLogin, MerchantOut, TokenResponse, MessageResponse,
)
from backend.utils.auth import (
    hash_password, verify_password, create_tokens, decode_token, get_current_user,
)
from backend.utils.audit import log_activity

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=MerchantOut, status_code=201)
async def register(data: MerchantRegister, db: AsyncSession = Depends(get_db)):
    # Check existing
    email = data.email.lower()
    existing = await db.execute(select(Merchant).where(Merchant.email == email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")

    merchant = Merchant(
        email=email,
        password_hash=hash_password(data.password),
        business_name=data.business_name,
        phone=data.phone,
        business_type=data.business_type,
        gstin=data.gstin,
        address=data.address,
        city=data.city,
        state=data.state,
        pincode=data.pincode,
    )
    db.add(merchant)
    await db.flush()

    await log_activity(db, action="merchant.register", actor_id=merchant.id,
                       resource_type="merchant", resource_id=merchant.id)
    await db.commit()
    return merchant


@router.post("/login", response_model=TokenResponse)
async def login(data: MerchantLogin, db: AsyncSession = Depends(get_db)):
    email = data.email.lower()
    result = await db.execute(select(Merchant).where(Merchant.email == email))
    merchant = result.scalar_one_or_none()

    if not merchant or not verify_password(data.password, merchant.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if not merchant.is_active:
        raise HTTPException(status_code=403, detail="Account is deactivated")

    access, refresh = create_tokens(str(merchant.id), merchant.role)

    await log_activity(db, action="merchant.login", actor_id=merchant.id,
                       resource_type="merchant", resource_id=merchant.id)
    await db.commit()

    return TokenResponse(access_token=access, refresh_token=refresh)


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(refresh_token: str, db: AsyncSession = Depends(get_db)):
    payload = decode_token(refresh_token, token_type="refresh")
    if payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    access, refresh = create_tokens(payload["sub"], payload["role"])
    return TokenResponse(access_token=access, refresh_token=refresh)


@router.get("/me", response_model=MerchantOut)
async def get_me(current_user: Merchant = Depends(get_current_user)):
    return current_user

from pydantic import BaseModel
from datetime import datetime, timedelta
import random

class ForgotPassword(BaseModel):
    email: str

class ResetPassword(BaseModel):
    email: str
    token: str
    new_password: str

@router.post("/forgot-password")
async def forgot_password(data: ForgotPassword, db: AsyncSession = Depends(get_db)):
    email = data.email.lower()
    result = await db.execute(select(Merchant).where(Merchant.email == email))
    merchant = result.scalar_one_or_none()

    if merchant:
        otp = str(random.randint(100000, 999999))
        merchant.reset_token = otp
        merchant.reset_token_expiry = datetime.utcnow() + timedelta(minutes=15)
        await db.commit()
        # In production, integrate Resend here.
        print(f"--- RESET OTP for {email}: {otp} ---")
    
    # Always return success to prevent email enumeration
    return {"message": "If an account exists, an OTP has been sent."}

@router.post("/reset-password")
async def reset_password(data: ResetPassword, db: AsyncSession = Depends(get_db)):
    email = data.email.lower()
    result = await db.execute(select(Merchant).where(Merchant.email == email))
    merchant = result.scalar_one_or_none()

    if not merchant:
        raise HTTPException(status_code=400, detail="Invalid request")

    if not merchant.reset_token or merchant.reset_token != data.token:
        raise HTTPException(status_code=400, detail="Invalid or expired OTP")

    if merchant.reset_token_expiry and merchant.reset_token_expiry < datetime.utcnow():
        raise HTTPException(status_code=400, detail="OTP expired")

    merchant.password_hash = hash_password(data.new_password)
    merchant.reset_token = None
    merchant.reset_token_expiry = None
    await db.commit()

    return {"message": "Password reset successfully. You can now login."}
