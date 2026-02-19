from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import model_validator
from typing import List, Optional
from functools import lru_cache


class Settings(BaseSettings):
    # ── App ──
    APP_NAME: str = "kosh-ai"
    APP_ENV: str = "development"
    DEBUG: bool = True
    SECRET_KEY: str = "change-me"

    # ── Backend ──
    BACKEND_HOST: str = "0.0.0.0"
    BACKEND_PORT: int = 8000
    BACKEND_CORS_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000"

    @property
    def cors_origins(self) -> List[str]:
        return [o.strip() for o in self.BACKEND_CORS_ORIGINS.split(",")]

    # ── Database ──
    DATABASE_URL: str = "postgresql+asyncpg://kosh:kosh_secret@localhost:5432/kosh_ai"
    DATABASE_URL_SYNC: str = "postgresql://kosh:kosh_secret@localhost:5432/kosh_ai"


    # ── Redis / Celery ──
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"

    # ── JWT ──
    JWT_SECRET_KEY: str = "leh8RC5KPTNekUEZcmr8h2PaCvpg1W_HKcx_fEpcV8w"
    JWT_REFRESH_SECRET_KEY: str = "rJz4AWD3La1X-7Bg_OGMTivYKwGXRfRSGmNAjECIG2U"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # ── Upload Limits ──
    MAX_UPLOAD_SIZE_MB: int = 10

    # ── Cloudinary ──
    CLOUDINARY_CLOUD_NAME: str = ""
    CLOUDINARY_API_KEY: str = ""
    CLOUDINARY_API_SECRET: str = ""

    # ── OCR ──
    OCR_PRIMARY_PROVIDER: str = "tesseract"
    TESSERACT_CMD: Optional[str] = None
    POPPLER_PATH: Optional[str] = None

    # ── WhatsApp ──
    WHATSAPP_API_URL: str = "https://graph.facebook.com/v18.0"
    WHATSAPP_API_TOKEN: str = ""
    WHATSAPP_VERIFY_TOKEN: str = ""
    WHATSAPP_PHONE_NUMBER_ID: str = ""

    # ── Rate Limiting ──
    RATE_LIMIT_PER_MINUTE: int = 60

    # ── Computed Properties ──

    @property
    def docs_url(self) -> Optional[str]:
        """Disable API docs in production."""
        return "/docs" if self.DEBUG else None

    @property
    def redoc_url(self) -> Optional[str]:
        """Disable ReDoc in production."""
        return "/redoc" if self.DEBUG else None

    @property
    def max_upload_bytes(self) -> int:
        return self.MAX_UPLOAD_SIZE_MB * 1024 * 1024

    # ── Startup Validation ──

    @model_validator(mode="after")
    def validate_secrets(self):
        """Raise on default secrets in non-development environments."""
        if self.APP_ENV not in ("development", "test"):
            insecure_defaults = {
                "SECRET_KEY": "change-me",
                "JWT_SECRET_KEY": "change-me-jwt",
                "JWT_REFRESH_SECRET_KEY": "change-me-refresh",
            }
            for field_name, default_val in insecure_defaults.items():
                if getattr(self, field_name) == default_val:
                    raise ValueError(
                        f"SECURITY: {field_name} is set to its default value. "
                        f"Set a strong secret in .env for APP_ENV={self.APP_ENV}"
                    )
        return self

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
