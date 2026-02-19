import asyncio
import sys
import os

# Add project root to path
sys.path.append(os.getcwd())

# Force local DB URL BEFORE imports
# os.environ["DATABASE_URL"] = "postgresql+asyncpg://kosh:kosh_password@localhost:5432/kosh_ai"

from backend.database import async_session_factory
from backend.models.models import Merchant
from backend.utils.auth import hash_password
from sqlalchemy import select

async def reset_password():
    email = "shiwangpande1@gmail.com"
    new_password = "Password123!"
    
    hashed = hash_password(new_password)
    print(f"Generated Hash: {hashed}")
    
    async with async_session_factory() as db:
        result = await db.execute(select(Merchant).where(Merchant.email == email))
        user = result.scalar_one_or_none()
        
        if user:
            user.password_hash = hashed
            await db.commit()
            print(f"Password updated for {email}")
        else:
            print(f"User {email} not found")

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(reset_password())
