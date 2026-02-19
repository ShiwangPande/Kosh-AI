from sqlalchemy import create_url
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
from backend.models.models import Invoice
from backend.config import get_settings
import asyncio

settings = get_settings()

async def get_ids():
    engine = create_async_engine(settings.DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        result = await session.execute(select(Invoice).limit(5))
        invoices = result.scalars().all()
        for inv in invoices:
            print(f"ID: {inv.id}, Status: {inv.ocr_status}")

if __name__ == "__main__":
    asyncio.run(get_ids())
