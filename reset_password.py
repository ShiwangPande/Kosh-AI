import asyncio
import sys
import os
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession

# Add root to sys.path
sys.path.append(os.getcwd())

from backend.config import get_settings
from backend.models.models import Merchant
from backend.utils.auth import hash_password

settings = get_settings()

async def reset_password(email: str, new_password: str):
    print(f"Connecting to DB...")
    engine = create_async_engine(settings.DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    try:
        async with async_session() as session:
            print(f"Searching for user: {email}")
            result = await session.execute(select(Merchant).where(Merchant.email == email))
            merchant = result.scalar_one_or_none()
            
            if not merchant:
                # Try case-insensitive search if exact match fails
                print("Exact match not found. Trying case-insensitive search...")
                # Fetch all and filter in python for safety if ILIKE is tricky with current imports
                result = await session.execute(select(Merchant))
                all_merchants = result.scalars().all()
                merchant = next((m for m in all_merchants if m.email.lower() == email.lower()), None)

            if merchant:
                print(f"Found user ID: {merchant.id}")
                print(f"Original Email: {merchant.email}")
                
                # Update password
                new_hash = hash_password(new_password)
                merchant.password_hash = new_hash
                
                # Also normalize email if it wasn't
                if merchant.email != email.lower():
                    print(f"Normalizing email to lowercase: {email.lower()}")
                    merchant.email = email.lower()
                
                await session.commit()
                print(f"Password updated successfully for {merchant.email}")
                print(f"New Password: {new_password}")
            else:
                print(f"User with email {email} not found.")
                
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await engine.dispose()

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python reset_password.py <email> <new_password>")
        sys.exit(1)
        
    email = sys.argv[1]
    new_password = sys.argv[2]
    
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    try:
        asyncio.run(reset_password(email, new_password))
    except RuntimeError as e:
        if str(e) == "Event loop is closed":
            pass
        else:
            raise
