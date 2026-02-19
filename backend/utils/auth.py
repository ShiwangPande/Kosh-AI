"""JWT authentication utilities."""
import re
import uuid
from datetime import datetime, timedelta
from typing import Optional, Tuple

from jose import JWTError, jwt
import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.config import get_settings
from backend.database import get_db
from backend.models.models import Merchant

settings = get_settings()
security = HTTPBearer()


# ── Password helpers ────────────────────────────────────────

def validate_password_strength(password: str) -> None:
    """Enforce password complexity: 8+ chars, upper, lower, digit, special."""
    if len(password) < 8:
        raise ValueError("Password must be at least 8 characters")
    if not re.search(r"[A-Z]", password):
        raise ValueError("Password must contain at least one uppercase letter")
    if not re.search(r"[a-z]", password):
        raise ValueError("Password must contain at least one lowercase letter")
    if not re.search(r"\d", password):
        raise ValueError("Password must contain at least one digit")
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>_\-+=\[\]\\\/~`]", password):
        raise ValueError("Password must contain at least one special character")


def hash_password(password: str) -> str:
    validate_password_strength(password)
    # Generate salt and hash
    # decode to utf-8 string for storage
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode('utf-8'), hashed.encode('utf-8'))


# ── Token helpers ───────────────────────────────────────────

def create_access_token(sub: str, role: str) -> str:
    expire = datetime.utcnow() + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": sub, "role": role, "exp": expire, "type": "access"}
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(sub: str, role: str) -> str:
    expire = datetime.utcnow() + timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)
    payload = {"sub": sub, "role": role, "exp": expire, "type": "refresh"}
    # Use separate key for refresh tokens (S2 fix)
    return jwt.encode(payload, settings.JWT_REFRESH_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_tokens(sub: str, role: str) -> Tuple[str, str]:
    return create_access_token(sub, role), create_refresh_token(sub, role)


def decode_token(token: str, token_type: str = "access") -> dict:
    """Decode a JWT token using the appropriate key for its type."""
    key = (
        settings.JWT_REFRESH_SECRET_KEY if token_type == "refresh"
        else settings.JWT_SECRET_KEY
    )
    try:
        return jwt.decode(token, key, algorithms=[settings.JWT_ALGORITHM])
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")


# ── FastAPI Dependencies ────────────────────────────────────

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> Merchant:
    payload = decode_token(credentials.credentials, token_type="access")
    if payload.get("type") != "access":
        raise HTTPException(status_code=401, detail="Invalid token type")

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    result = await db.execute(select(Merchant).where(Merchant.id == uuid.UUID(user_id)))
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or inactive")
    return user


async def require_admin(current_user: Merchant = Depends(get_current_user)) -> Merchant:
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user


def require_roles(*roles: str):
    """Factory for role-based guards. Returns a FastAPI dependency.

    Usage: Depends(require_roles("admin", "manager"))
    """
    async def dependency(current_user: Merchant = Depends(get_current_user)) -> Merchant:
        if current_user.role not in roles:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return current_user
    return dependency
