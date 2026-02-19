from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from backend.database import get_db
from backend.services.docs_service import DocsService
from typing import List, Optional
from pydantic import BaseModel, UUID4
from uuid import UUID

router = APIRouter()

class DocArticleOut(BaseModel):
    id: UUID
    slug: str
    title: str
    summary: Optional[str] = None
    content: Optional[str] = None
    category: Optional[str] = None
    order_index: int
    
    class Config:
        from_attributes = True

@router.get("/categories", response_model=List[str])
async def get_categories(db: AsyncSession = Depends(get_db)):
    return await DocsService.get_categories(db)

@router.get("/articles", response_model=List[DocArticleOut])
async def list_articles(
    category: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    return await DocsService.get_articles(db, category)

@router.get("/article/{slug}", response_model=DocArticleOut)
async def get_article(slug: str, db: AsyncSession = Depends(get_db)):
    article = await DocsService.get_article(db, slug)
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    return article

@router.get("/search", response_model=List[DocArticleOut])
async def search_docs(q: str = Query(..., min_length=2), db: AsyncSession = Depends(get_db)):
    return await DocsService.search_articles(db, q)

@router.post("/seed")
async def seed_docs(db: AsyncSession = Depends(get_db)):
    """Manually trigger seeding (idempotent)"""
    await DocsService.seed_initial_data(db)
    return {"message": "Documentation seeded successfully"}
