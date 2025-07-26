"""Authentication middleware for FastAPI."""

from fastapi import Request, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
from ..utils.auth import decode_token
from ..models.database import get_db, User


class JWTBearer(HTTPBearer):
    """JWT Bearer token authentication."""
    
    def __init__(self, auto_error: bool = True):
        super(JWTBearer, self).__init__(auto_error=auto_error)
    
    async def __call__(self, request: Request) -> Optional[HTTPAuthorizationCredentials]:
        credentials: HTTPAuthorizationCredentials = await super(JWTBearer, self).__call__(request)
        if credentials:
            if not credentials.scheme == "Bearer":
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Invalid authentication scheme."
                )
            if not self.verify_jwt(credentials.credentials):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Invalid token or expired token."
                )
            return credentials.credentials
        else:
            return None
    
    def verify_jwt(self, token: str) -> bool:
        """Verify if the JWT token is valid."""
        try:
            payload = decode_token(token)
            return True
        except:
            return False


def get_current_user(token: str = None) -> Optional[User]:
    """Get the current user from JWT token."""
    if not token:
        return None
    
    try:
        payload = decode_token(token)
        user_id = payload.get("sub")
        
        if not user_id:
            return None
        
        # Get user from database
        db = next(get_db())
        user = db.query(User).filter(User.id == user_id).first()
        db.close()
        
        return user
    except:
        return None


def require_auth(token: str = None) -> User:
    """Require authentication - raises exception if not authenticated."""
    user = get_current_user(token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    return user


def get_user_or_session(request: Request) -> tuple[Optional[User], Optional[str]]:
    """
    Get user from token or session ID for tracking.
    Returns (user, session_id)
    """
    # Try to get user from authorization header
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
        user = get_current_user(token)
        if user:
            return user, None
    
    # Get or create session ID for anonymous users
    session_id = request.cookies.get("session_id")
    if not session_id:
        from ..utils.auth import generate_session_id
        session_id = generate_session_id()
    
    return None, session_id