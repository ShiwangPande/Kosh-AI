from backend.config import get_settings
import os

print(f"Env var DATABASE_URL_SYNC: {os.environ.get('DATABASE_URL_SYNC')}")
settings = get_settings()
print(f"Settings DATABASE_URL_SYNC: {settings.DATABASE_URL_SYNC}")
print(f"Settings DATABASE_URL: {settings.DATABASE_URL}")
