"""
🔐 SECURE COOKIE-BASED AUTHENTICATION UPDATE
This updates the backend to use secure HTTP-only cookies like Google/Facebook
"""

UPDATED_AUTH_PY = '''from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import secrets
import bcrypt
import jwt
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr

from ..database import get_db
from ..models import User
from ..config import settings

router = APIRouter(prefix="/api/auth", tags=["authentication"])

# Cookie configuration
COOKIE_NAME = "auth_token"
COOKIE_SECURE = True  # Always use secure cookies with HTTPS
COOKIE_HTTPONLY = True  # Prevent JavaScript access
COOKIE_SAMESITE = "lax"  # CSRF protection
COOKIE_MAX_AGE = 30 * 24 * 60 * 60  # 30 days for remember me
COOKIE_MAX_AGE_SHORT = 24 * 60 * 60  # 24 hours for regular login

class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    remember_me: bool = False

class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
    password: str

def create_access_token(user_id: int, email: str) -> str:
    """Create JWT token for user"""
    expire = datetime.utcnow() + timedelta(days=30)
    payload = {
        "sub": str(user_id),
        "email": email,
        "exp": expire,
        "iat": datetime.utcnow()
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")

def verify_token(token: str) -> Optional[Dict[str, Any]]:
    """Verify and decode JWT token"""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        return payload
    except jwt.ExpiredTokenError:
        return None
    except jwt.InvalidTokenError:
        return None

def get_current_user_from_cookie(request: Request, db: Session = Depends(get_db)) -> Optional[User]:
    """Get current user from auth cookie"""
    token = request.cookies.get(COOKIE_NAME)
    
    if not token:
        return None
    
    payload = verify_token(token)
    if not payload:
        return None
    
    user = db.query(User).filter(User.id == int(payload["sub"])).first()
    return user

def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    """Get current user or raise 401"""
    user = get_current_user_from_cookie(request, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    return user

@router.post("/register")
async def register(
    request: RegisterRequest,
    response: Response,
    db: Session = Depends(get_db)
):
    """Register new user with secure cookie auth"""
    # Check if user exists
    existing_user = db.query(User).filter(User.email == request.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Hash password
    hashed_password = bcrypt.hashpw(request.password.encode('utf-8'), bcrypt.gensalt())
    
    # Create user
    user = User(
        name=request.name,
        email=request.email,
        password_hash=hashed_password.decode('utf-8')
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    # Create token
    token = create_access_token(user.id, user.email)
    
    # Set secure cookie
    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        max_age=COOKIE_MAX_AGE,
        secure=COOKIE_SECURE,
        httponly=COOKIE_HTTPONLY,
        samesite=COOKIE_SAMESITE,
        path="/"
    )
    
    return {
        "message": "Registration successful",
        "user": {
            "id": user.id,
            "email": user.email,
            "name": user.name
        }
    }

@router.post("/login")
async def login(
    request: LoginRequest,
    response: Response,
    db: Session = Depends(get_db)
):
    """Login with secure cookie auth"""
    # Find user
    user = db.query(User).filter(User.email == request.email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    # Verify password
    if not bcrypt.checkpw(request.password.encode('utf-8'), user.password_hash.encode('utf-8')):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    # Create token
    token = create_access_token(user.id, user.email)
    
    # Set secure cookie
    max_age = COOKIE_MAX_AGE if request.remember_me else COOKIE_MAX_AGE_SHORT
    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        max_age=max_age,
        secure=COOKIE_SECURE,
        httponly=COOKIE_HTTPONLY,
        samesite=COOKIE_SAMESITE,
        path="/"
    )
    
    return {
        "message": "Login successful",
        "user": {
            "id": user.id,
            "email": user.email,
            "name": user.name
        }
    }

@router.post("/logout")
async def logout(response: Response):
    """Logout by clearing cookie"""
    response.delete_cookie(
        key=COOKIE_NAME,
        secure=COOKIE_SECURE,
        httponly=COOKIE_HTTPONLY,
        samesite=COOKIE_SAMESITE,
        path="/"
    )
    return {"message": "Logged out successfully"}

@router.get("/check")
async def check_auth(request: Request, db: Session = Depends(get_db)):
    """Check if user is authenticated"""
    user = get_current_user_from_cookie(request, db)
    
    if user:
        return {
            "authenticated": True,
            "user": {
                "id": user.id,
                "email": user.email,
                "name": user.name
            }
        }
    
    return {"authenticated": False}

@router.get("/me")
async def get_me(current_user: User = Depends(get_current_user)):
    """Get current user info"""
    return {
        "id": current_user.id,
        "email": current_user.email,
        "name": current_user.name
    }

# CSRF Token endpoint (optional but recommended)
@router.get("/csrf")
async def get_csrf_token(response: Response):
    """Generate CSRF token"""
    csrf_token = secrets.token_urlsafe(32)
    response.set_cookie(
        key="csrf_token",
        value=csrf_token,
        secure=COOKIE_SECURE,
        httponly=False,  # JavaScript needs to read this
        samesite=COOKIE_SAMESITE,
        path="/"
    )
    return {"csrf_token": csrf_token}
'''

print(UPDATED_AUTH_PY)