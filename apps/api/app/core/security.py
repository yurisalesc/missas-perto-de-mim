"""Security helpers."""

import secrets

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from passlib.context import CryptContext

from app.core.config import settings

pwd_context = CryptContext(schemes=["argon2", "bcrypt"], deprecated="auto")
security = HTTPBasic()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Validate a plain password against a hash."""

    return pwd_context.verify(plain_password, hashed_password)


def require_admin(credentials: HTTPBasicCredentials = Depends(security)) -> str:
    """Validate admin credentials and return username."""

    if settings.app_env != "development" and settings.admin_password is not None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Plain ADMIN_PASSWORD is disabled outside development",
        )
    if settings.admin_password is None and not settings.admin_password_hash:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Admin credentials are not configured",
        )

    valid_user = credentials.username == settings.admin_username
    if settings.admin_password is not None:
        valid_password = secrets.compare_digest(credentials.password, settings.admin_password)
    else:
        valid_password = verify_password(credentials.password, settings.admin_password_hash)
    if not (valid_user and valid_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid admin credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username


def hash_password(plain_password: str) -> str:
    """Generate a secure password hash for admin credentials."""

    return pwd_context.hash(plain_password)
