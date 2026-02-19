from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from datetime import datetime
from typing import Optional

from backend.database import get_db
from backend.models.models import Merchant, UserOnboardingState
from backend.services.onboarding_service import OnboardingService
from backend.utils.auth import get_current_user
from pydantic import BaseModel

router = APIRouter(prefix="/onboarding", tags=["Onboarding"])

class OnboardingStateOut(BaseModel):
    step: str
    completed: bool
    skipped: bool
    completed_at: Optional[datetime] = None
    onboarding_metadata: Optional[dict] = None
    
    class Config:
        from_attributes = True

class StepCompleteRequest(BaseModel):
    step: str

@router.get("/state", response_model=OnboardingStateOut)
async def get_state(
    current_user: Merchant = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    state = await OnboardingService.get_state(db, current_user.id)
    return state

@router.post("/advance", response_model=OnboardingStateOut)
async def advance_step(
    current_user: Merchant = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    state = await OnboardingService.advance_step(db, current_user.id)
    return state

@router.post("/complete", response_model=OnboardingStateOut)
async def complete_step(
    request: StepCompleteRequest,
    current_user: Merchant = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    state = await OnboardingService.complete_specific_step_activity(db, current_user.id, request.step)
    return state

@router.post("/skip", response_model=OnboardingStateOut)
async def skip_onboarding(
    current_user: Merchant = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    state = await OnboardingService.skip_onboarding(db, current_user.id)
    return state
    
@router.post("/reset", response_model=OnboardingStateOut)
async def reset_onboarding(
    current_user: Merchant = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    state = await OnboardingService.reset_onboarding(db, current_user.id)
    return state
