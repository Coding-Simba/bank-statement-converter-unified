"""Common dependencies for FastAPI routes."""

from fastapi import HTTPException, Security, status, Request, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Optional

from models.database import get_db, User
from middleware.auth_middleware import get_current_user as _get_current_user, security
from utils.auth import decode_token

# Re-export the main get_current_user function
get_current_user = _get_current_user


def get_current_user_optional(
    request: Request,
    db: Session = Depends(get_db)
) -> Optional[User]:
    """Get current user from JWT token, but don't fail if not authenticated."""
    
    # Check for Authorization header
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return None
    
    try:
        token = auth_header.split(" ")[1]
        payload = decode_token(token)
        user_id = payload.get("sub")
        
        if not user_id:
            return None
        
        user = db.query(User).filter(User.id == user_id).first()
        return user
    except Exception:
        return None