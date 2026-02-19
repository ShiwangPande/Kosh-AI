import asyncio
import sys
import os
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Add root to sys.path
sys.path.append(os.getcwd())

# Load env vars (though config.py does it, we might need to be explicit if running standalone)
from dotenv import load_dotenv
load_dotenv()

from backend.config import get_settings
from backend.models.models import Merchant
from backend.utils.auth import verify_password, hash_password

settings = get_settings()

async def main():
    print(f"Connecting to DB: {settings.DATABASE_URL.split('@')[1]}") # Hide credentials
    
    engine = create_async_engine(settings.DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    try:
        async with async_session() as session:
            print("\n--- Listing Merchants ---")
            sys.stdout.flush()
            result = await session.execute(select(Merchant))
            merchants = result.scalars().all()
            
            with open('debug_output.txt', 'w') as f:
                if not merchants:
                    f.write("No merchants found.\n")
                
                for m in merchants:
                    f.write(f"ID: {m.id}, Email: {m.email}, Active: {m.is_active}, Role: {m.role}\n")
                    f.write(f"Hash: {m.password_hash[:20]}...\n")
            
            print("Debug info written to debug_output.txt")

            print("\n--- Test Password Verification ---")
            if len(sys.argv) > 2:
                test_email = sys.argv[1]
                password = sys.argv[2]
                print(f"Testing email: {test_email}")
                
                merchant = next((m for m in merchants if m.email == test_email), None)
                if merchant:
                    is_valid = verify_password(password, merchant.password_hash)
                    print(f"Password valid: {is_valid}")
                    # Also write result to file
                    with open('debug_output.txt', 'a') as f:
                        f.write(f"\nTested email: {test_email}\n")
                        f.write(f"Password valid: {is_valid}\n")

                    if not is_valid:
                        hashed_input = hash_password(password)
                        print(f"Input hash: {hashed_input}")
                else:
                    print(f"Merchant with email {test_email} not found.")
            else:
                print("To test password, run: python debug_auth.py <email> <password>")
    except Exception as e:
        with open('debug_output.txt', 'w') as f:
            f.write(f"Error: {e}\n")
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await engine.dispose()

if __name__ == "__main__":
    # if sys.platform == 'win32':
    #     asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    try:
        asyncio.run(main())
    except RuntimeError as e:
        if str(e) == "Event loop is closed":
            pass
        else:
            raise
