import asyncio
import logging
import sys
import os

# Add parent directory to path to allow importing backend
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sqlalchemy import select
from backend.database import async_session_factory
from backend.models.models import Merchant
from backend.utils.auth import hash_password
from backend.config import get_settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
settings = get_settings()

async def ensure_admin():
    """Ensure that at least one admin user exists."""
    admin_email = "admin@kosh.ai"
    # Note: Using Admin@123 to satisfy the 8+ char, upper, lower, digit, special requirement
    default_password = "Admin@123" 
    
    async with async_session_factory() as session:
        try:
            # Check if admin already exists
            result = await session.execute(
                select(Merchant).where(Merchant.email == admin_email)
            )
            admin = result.scalar_one_or_none()
            
            if admin:
                logger.info(f"Admin user {admin_email} already exists.")
                return
            
            # Create admin if missing
            logger.info(f"Creating default admin user: {admin_email}")
            new_admin = Merchant(
                email=admin_email,
                password_hash=hash_password(default_password),
                business_name="Kosh Admin",
                phone="+919876543210",
                role="admin",
                city="Mumbai",
                state="Maharashtra",
                is_active=True
            )
            session.add(new_admin)
            await session.commit()
            logger.info("✅ Admin user created successfully.")
            logger.info(f"   Credentials: {admin_email} / {default_password}")
            
        except Exception as e:
            await session.rollback()
            logger.error(f"❌ Failed to ensure admin: {str(e)}")
            # Don't exit with error, we want the app to start even if this fails
            # (e.g. if DB is not ready yet, though migrations already ran)

if __name__ == "__main__":
    asyncio.run(ensure_admin())
