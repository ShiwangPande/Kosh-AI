from backend.config import get_settings
import os

print(f"Current Directory: {os.getcwd()}")
print(f".env exists: {os.path.exists('.env')}")

settings = get_settings()
print(f"DATABASE_URL: {settings.DATABASE_URL}")
print(f"REDIS_URL: {settings.REDIS_URL}")
print(f"CELERY_BROKER_URL: {settings.CELERY_BROKER_URL}")

if "localhost" in settings.REDIS_URL or "127.0.0.1" in settings.REDIS_URL:
    print("SUCCESS: Settings loaded from .env (localhost detected)")
else:
    print("FAILURE: Settings still using defaults (Docker hostnames detected)")
