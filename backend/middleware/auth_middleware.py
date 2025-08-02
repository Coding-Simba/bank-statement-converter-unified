"""JWT Authentication Middleware"""

from fastapi import HTTPException, Security, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Optional, Tuple

from models.database import get_db, User
from utils.auth import decode_token

security = HTTPBearer()


class JWTBearer(HTTPBearer):
    def __init__(self, auto_error: bool = True):
        super(JWTBearer, self).__init__(auto_error=auto_error)

    async def __call__(self, request):
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
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid authorization code."
            )

    def verify_jwt(self, token: str) -> bool:
        try:
            payload = decode_token(token)
            return True
        except:
            return False


def get_current_user(credentials: HTTPAuthorizationCredentials = Security(security)) -> Optional[User]:
    """Get current user from JWT token"""
    token = credentials.credentials
    
    try:
        # Debug logging
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"Attempting to validate token: {token[:20]}...")
        
        payload = decode_token(token)
        user_id = payload.get("sub")
        logger.info(f"Token validated successfully for user_id: {user_id}")
        
        # Convert user_id to int if it's a string
        if isinstance(user_id, str):
            try:
                user_id = int(user_id)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid user ID in token"
                )
        
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
        
        # Get database session
        db = next(get_db())
        user = db.query(User).filter(User.id == user_id).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
        
        return user
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Could not validate credentials: {str(e)}"
        )


def get_user_or_session(request: Request) -> Tuple[Optional[User], Optional[str]]:
    """Get current user or session ID"""
    # Try to get authenticated user first
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        try:
            token = auth_header.split(" ")[1]
            payload = decode_token(token)
            user_id = payload.get("sub")
            
            if user_id:
                db = next(get_db())
                user = db.query(User).filter(User.id == user_id).first()
                if user:
                    return (user, None)
        except:
            pass
    
    # Fall back to session ID
    session_id = request.cookies.get("session_id") or request.headers.get("X-Session-ID")
    if not session_id:
        # Generate new session ID if none exists
        import secrets
        session_id = secrets.token_urlsafe(32)
    
    return (None, session_id)