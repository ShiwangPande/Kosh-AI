from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.models.models import UserOnboardingState
from typing import Optional
from datetime import datetime, timezone
import uuid

class OnboardingService:
    @staticmethod
    async def get_state(db: AsyncSession, merchant_id: uuid.UUID) -> UserOnboardingState:
        stmt = select(UserOnboardingState).where(UserOnboardingState.merchant_id == merchant_id)
        result = await db.execute(stmt)
        state = result.scalar_one_or_none()
        
        if not state:
            state = UserOnboardingState(merchant_id=merchant_id, step="WELCOME")
            db.add(state)
            await db.commit()
            await db.refresh(state)
            
        return state

    @staticmethod
    async def advance_step(db: AsyncSession, merchant_id: uuid.UUID) -> UserOnboardingState:
        state = await OnboardingService.get_state(db, merchant_id)
        
        if state.completed or state.skipped:
            return state

        current_step = state.step
        next_step = current_step # Default
        
        # Rigid transitions as fallback
        transitions = {
            "WELCOME": "UPLOAD_INVOICE",
            "UPLOAD_INVOICE": "INSIGHT_REVEAL",
            "INSIGHT_REVEAL": "FIRST_RECOMMENDATION",
            "FIRST_RECOMMENDATION": "ACTION_DEMO",
            "ACTION_DEMO": "COMPLETED"
        }
        
        if current_step in transitions:
             next_step = transitions[current_step]
        
        if next_step == "COMPLETED":
             state.completed = True
             state.completed_at = datetime.now(timezone.utc)
        
        if next_step != current_step:
            state.step = next_step
            await db.commit()
            await db.refresh(state)
            
        return state

    @staticmethod
    async def complete_specific_step_activity(db: AsyncSession, merchant_id: uuid.UUID, activity_step: str) -> UserOnboardingState:
        """
        Called when a user performs an action (e.g. Upload Invoice).
        If the user is at or before this step, advance them PAST it.
        """
        state = await OnboardingService.get_state(db, merchant_id)
        
        if state.completed or state.skipped:
            return state

        step_order = ["WELCOME", "UPLOAD_INVOICE", "INSIGHT_REVEAL", "FIRST_RECOMMENDATION", "ACTION_DEMO", "COMPLETED"]
        
        try:
            current_idx = step_order.index(state.step)
            activity_idx = step_order.index(activity_step)
        except ValueError:
            return state # Step not found
            
        # If user performs an activity (e.g. Upload Invoice)
        # We want to ensure they are at least at the step AFTER that.
        # e.g. activity=UPLOAD_INVOICE (index 1). Target state should be index 2 (INSIGHT_REVEAL).
        
        target_state_idx = activity_idx + 1
        
        if target_state_idx > current_idx:
            # Checking bounds
            if target_state_idx >= len(step_order):
                 target_step = "COMPLETED"
            else:
                 target_step = step_order[target_state_idx]
            
            state.step = target_step
            
            if target_step == "COMPLETED":
                state.completed = True
                state.completed_at = datetime.now(timezone.utc)
                
            await db.commit()
            await db.refresh(state)
            
        return state

    @staticmethod
    async def skip_onboarding(db: AsyncSession, merchant_id: uuid.UUID) -> UserOnboardingState:
        state = await OnboardingService.get_state(db, merchant_id)
        state.skipped = True
        state.completed = True
        state.completed_at = datetime.now(timezone.utc)
        await db.commit()
        await db.refresh(state)
        return state

    @staticmethod
    async def reset_onboarding(db: AsyncSession, merchant_id: uuid.UUID) -> UserOnboardingState:
        state = await OnboardingService.get_state(db, merchant_id)
        state.step = "WELCOME"
        state.completed = False
        state.skipped = False
        state.completed_at = None
        state.onboarding_metadata = {}
        await db.commit()
        await db.refresh(state)
        return state
