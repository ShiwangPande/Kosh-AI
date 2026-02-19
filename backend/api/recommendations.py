from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from uuid import UUID

from backend.database import get_db
from backend.utils.auth import get_current_user
from backend.models.models import Merchant, Recommendation
from backend.services.recommendation_engine import generate_invoice_recommendations
from backend.schemas.schemas import RecommendationOut, RecommendationUpdate, PaginatedResponse

router = APIRouter(prefix="/recommendations", tags=["Recommendations"])


@router.post("/generate/{invoice_id}")
async def trigger_recommendations(
    invoice_id: UUID,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: Merchant = Depends(get_current_user),
):
    """
    Trigger recommendation generation for an invoice.
    """
    # Verify ownership
    # (assuming invoice ownership check happens in service or here)
    
    # Run in background to ensure fast response, 
    # but requirement involved "return top 3". 
    # If user wants immediate results, we await. 
    # "Recommendation must compute under 2 seconds".
    # So we await it.
    
    try:
        result = await generate_invoice_recommendations(db, invoice_id, current_user.id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{invoice_id}", response_model=List[RecommendationOut])
async def get_invoice_recommendations(
    invoice_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Merchant = Depends(get_current_user),
):
    """Get existing recommendations for an invoice."""
    from sqlalchemy.orm import selectinload
    
    result = await db.execute(
        select(Recommendation)
        .where(
            Recommendation.invoice_id == invoice_id,
            Recommendation.merchant_id == current_user.id
        )
        .options(
            selectinload(Recommendation.product),
            selectinload(Recommendation.recommended_supplier),
            selectinload(Recommendation.current_supplier)
        )
    )
    items = result.scalars().all()
    
    out = []
    for i in items:
        model = RecommendationOut.model_validate(i)
        model.product_name = i.product.name if i.product else "Product"
        model.recommended_supplier_name = i.recommended_supplier.name if i.recommended_supplier else "Unknown Supplier"
        model.current_supplier_name = i.current_supplier.name if i.current_supplier else "Current Supplier"
        out.append(model)
        
    return out

@router.get("", response_model=PaginatedResponse)
async def list_recommendations(
    page: int = 1,
    per_page: int = 20,
    db: AsyncSession = Depends(get_db),
    current_user: Merchant = Depends(get_current_user),
):
    """List all recommendations for the current merchant (paginated)."""
    from sqlalchemy.orm import selectinload
    
    offset = (page - 1) * per_page
    
    # Count total
    count_result = await db.execute(
        select(func.count(Recommendation.id)).where(Recommendation.merchant_id == current_user.id)
    )
    total = count_result.scalar() or 0
    
    # Fetch items with related names
    result = await db.execute(
        select(Recommendation)
        .where(Recommendation.merchant_id == current_user.id)
        .options(
            selectinload(Recommendation.product),
            selectinload(Recommendation.recommended_supplier),
            selectinload(Recommendation.current_supplier)
        )
        .order_by(Recommendation.created_at.desc())
        .offset(offset)
        .limit(per_page)
    )
    items = result.scalars().all()
    
    out_items = []
    for i in items:
        model = RecommendationOut.model_validate(i)
        model.product_name = i.product.name if i.product else "Product"
        model.recommended_supplier_name = i.recommended_supplier.name if i.recommended_supplier else "Unknown Supplier"
        model.current_supplier_name = i.current_supplier.name if i.current_supplier else "Current Supplier"
        out_items.append(model)
    
    pages = (total + per_page - 1) // per_page if per_page > 0 else 0
    
    return PaginatedResponse(
        items=out_items,
        total=total,
        page=page,
        per_page=per_page,
        pages=pages,
    )


@router.patch("/{recommendation_id}", response_model=RecommendationOut)
async def update_recommendation_status(
    recommendation_id: UUID,
    update_data: RecommendationUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: Merchant = Depends(get_current_user),
):
    """Update recommendation status (accept/reject)."""
    from sqlalchemy.orm import selectinload
    
    result = await db.execute(
        select(Recommendation)
        .where(
            Recommendation.id == recommendation_id,
            Recommendation.merchant_id == current_user.id
        )
        .options(
            selectinload(Recommendation.product),
            selectinload(Recommendation.recommended_supplier),
            selectinload(Recommendation.current_supplier)
        )
    )
    rec = result.scalar_one_or_none()
    if not rec:
        raise HTTPException(status_code=404, detail="Recommendation not found")
        
    rec.status = update_data.status
    await db.commit()
    await db.refresh(rec)
    
    model = RecommendationOut.model_validate(rec)
    model.product_name = rec.product.name if rec.product else "Product"
    model.recommended_supplier_name = rec.recommended_supplier.name if rec.recommended_supplier else "Unknown Supplier"
    model.current_supplier_name = rec.current_supplier.name if rec.current_supplier else "Current Supplier"
    
    return model
