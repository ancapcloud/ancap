"""API dependencies for FastAPI routers."""
from typing import Generator, Optional
from contextlib import asynccontextmanager

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db as _get_db
from app.config import get_settings
from app.db.models import User


def get_db() -> Generator[Session, None, None]:
    """Get database session."""
    db = _get_db()
    try:
        yield db
    finally:
        db.close()


def require_admin(db: Session) -> bool:
    """Require admin privileges for admin endpoints.
    
    In production, this would check the user's role/permissions.
    For now, we assume the caller is authorized (admin-only endpoint).
    """
    return True


def require_auth(token: Optional[str] = None) -> dict:
    """Require authentication for protected endpoints.
    
    Returns user data if authenticated and admin, raises 401 if no token provided,
    raises 403 if user is not admin.
    In production, this would validate the token and load the user from DB.
    For now, we accept any non-empty token as valid (placeholder for JWT/OAuth).
    """
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    # Placeholder: in production, validate token and load user from DB
    # For now, assume all authenticated users are admins (simplified)
    return {"user_id": "admin-placeholder", "is_admin": True}
