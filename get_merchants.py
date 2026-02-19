from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
from backend.models.models import Merchant
from backend.config import get_settings
import asyncio

settings = get_settings()

async def get_merchants():
    engine = create_async_engine(settings.DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        result = await session.execute(select(Merchant).limit(5))
        merchants = result.scalars().all()
        for m in merchants:
            print(f"Email: {m.email}, ID: {m.id}")

if __name__ == "__main__":
    asyncio.run(get_merchants())
