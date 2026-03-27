"""Security helpers."""

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

    valid_user = credentials.username == settings.admin_username
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
