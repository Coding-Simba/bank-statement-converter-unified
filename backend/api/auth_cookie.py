"""Modern authentication API with HTTP-only cookies."""

from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime, timedelta
import secrets
import uuid

from models.database import get_db, User
from utils.auth import (
    verify_password, get_password_hash, create_access_token, 
    create_refresh_token, validate_email, validate_password,
    decode_token
)
from jwt.exceptions import InvalidTokenError
# from api.sessions import create_session  # TODO: Implement sessions module

router = APIRouter(prefix="/api/auth", tags=["authentication"])

# Constants
ACCESS_TOKEN_EXPIRE_MINUTES = 15
REFRESH_TOKEN_EXPIRE_HOURS = 24  # Default without remember me
REFRESH_TOKEN_EXPIRE_DAYS = 90  # With remember me
COOKIE_DOMAIN = ".bankcsvconverter.com"  # Cross-subdomain support

# Session tracking
current_session_id = None


# Pydantic models
class UserLogin(BaseModel):
    email: EmailStr
    password: str
    remember_me: bool = False


class UserRegister(BaseModel):
    email: EmailStr
    password: str
    full_name: Optional[str] = None
    company_name: Optional[str] = None


class UserData(BaseModel):
    id: int
    email: str
    full_name: Optional[str]
    company_name: Optional[str]
    account_type: str
    created_at: datetime
    daily_generations: int
    daily_limit: int


def set_auth_cookies(response: Response, access_token: str, refresh_token: str, remember_me: bool = False, request: Optional[Request] = None):
    """Set authentication cookies with proper security settings."""
    # Detect if we're in production based on request
    is_production = True  # Default to secure
    if request:
        # Check if HTTPS or if domain contains bankcsvconverter.com
        is_production = (request.url.scheme == "https" or 
                        "bankcsvconverter.com" in str(request.url.hostname) or
                        request.url.hostname not in ["localhost", "127.0.0.1"])
    
    # Access token cookie
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=is_production,  # HTTPS only in production
        samesite="lax",
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        path="/",
        domain=COOKIE_DOMAIN if is_production else None
    )
    
    # Refresh token cookie (only sent to refresh endpoint)
    refresh_max_age = (REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60) if remember_me else (REFRESH_TOKEN_EXPIRE_HOURS * 60 * 60)
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=is_production,
        samesite="lax",
        max_age=refresh_max_age,
        path="/api/auth/refresh",
        domain=COOKIE_DOMAIN if is_production else None
    )


def clear_auth_cookies(response: Response):
    """Clear all authentication cookies."""
    response.delete_cookie(key="access_token", path="/", domain=COOKIE_DOMAIN)
    response.delete_cookie(key="refresh_token", path="/api/auth/refresh", domain=COOKIE_DOMAIN)
    response.delete_cookie(key="csrf_token", path="/", domain=COOKIE_DOMAIN)


@router.get("/csrf")
async def get_csrf_token(response: Response):
    """Generate and return CSRF token."""
    csrf_token = secrets.token_urlsafe(32)
    
    # Set CSRF cookie (readable by JavaScript)
    response.set_cookie(
        key="csrf_token",
        value=csrf_token,
        httponly=False,  # JavaScript needs to read this
        secure=True,
        samesite="strict",
        max_age=3600,  # 1 hour
        path="/",
        domain=COOKIE_DOMAIN
    )
    
    return {"csrf_token": csrf_token}


@router.post("/register")
async def register(
    response: Response,
    request: Request,
    user_data: UserRegister,
    db: Session = Depends(get_db)
):
    """Register a new user with cookie-based auth."""
    
    # Validate email
    if not validate_email(user_data.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid email format"
        )
    
    # Validate password
    is_valid, error_msg = validate_password(user_data.password)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg
        )
    
    # Check if user exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    hashed_password = get_password_hash(user_data.password)
    refresh_token_family = str(uuid.uuid4())
    
    new_user = User(
        email=user_data.email,
        password_hash=hashed_password,
        full_name=user_data.full_name,
        company_name=user_data.company_name,
        account_type="free",
        auth_provider="email",
        email_verified=False,
        refresh_token_family=refresh_token_family
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # Create tokens (sub must be a string for JWT)
    access_token = create_access_token(
        data={"sub": str(new_user.id), "email": new_user.email}
    )
    refresh_token = create_refresh_token(
        data={
            "sub": str(new_user.id), 
            "email": new_user.email,
            "family": refresh_token_family,
            "version": 1
        }
    )
    
    # Set cookies
    set_auth_cookies(response, access_token, refresh_token, request=request)
    
    # Return user data (no tokens)
    return {
        "user": UserData(
            id=new_user.id,
            email=new_user.email,
            full_name=new_user.full_name,
            company_name=new_user.company_name,
            account_type=new_user.account_type,
            created_at=new_user.created_at,
            daily_generations=new_user.daily_generations,
            daily_limit=new_user.get_daily_limit()
        )
    }


@router.post("/login")
async def login(
    response: Response,
    user_credentials: UserLogin,
    request: Request,
    db: Session = Depends(get_db)
):
    """Login with email and password using cookie auth."""
    
    # Find user
    user = db.query(User).filter(User.email == user_credentials.email).first()
    
    if not user or not verify_password(user_credentials.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated"
        )
    
    # Reset daily limit if needed
    user.reset_daily_limit_if_needed()
    
    # Update refresh token family
    if not user.refresh_token_family:
        user.refresh_token_family = str(uuid.uuid4())
    
    user.refresh_token_version = 1  # Reset version on new login
    db.commit()
    
    # Create session tracking
    session_id = str(uuid.uuid4())
    user_agent = request.headers.get("User-Agent", "Unknown")
    client_ip = request.client.host if request.client else "Unknown"
    
    # TODO: Re-enable when sessions module is implemented
    # create_session(
    #     user_id=user.id,
    #     session_id=session_id,
    #     user_agent=user_agent,
    #     ip_address=client_ip,
    #     is_remember_me=user_credentials.remember_me,
    #     db=db
    # )
    
    # Create tokens with session ID (sub must be a string for JWT)
    access_token = create_access_token(
        data={"sub": str(user.id), "email": user.email, "session_id": session_id}
    )
    refresh_token = create_refresh_token(
        data={
            "sub": str(user.id),
            "email": user.email,
            "family": user.refresh_token_family,
            "version": user.refresh_token_version,
            "session_id": session_id
        }
    )
    
    # Set cookies with remember me
    set_auth_cookies(response, access_token, refresh_token, remember_me=user_credentials.remember_me, request=request)
    
    # Return user data (no tokens)
    return {
        "user": UserData(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            company_name=user.company_name,
            account_type=user.account_type,
            created_at=user.created_at,
            daily_generations=user.daily_generations,
            daily_limit=user.get_daily_limit()
        )
    }


@router.post("/refresh")
async def refresh_token(
    request: Request,
    response: Response,
    db: Session = Depends(get_db)
):
    """Refresh access token using refresh token from cookie."""
    
    # Get refresh token from cookie
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token not found"
        )
    
    try:
        # Decode refresh token
        payload = decode_token(refresh_token)
        
        if payload.get("type") != "refresh":
            raise ValueError("Invalid token type")
        
        user_id = payload.get("sub")
        token_family = payload.get("family")
        token_version = payload.get("version", 1)
        
        # Get user
        user = db.query(User).filter(User.id == user_id).first()
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid user"
            )
        
        # Validate token family and version (refresh token rotation)
        if user.refresh_token_family != token_family:
            # Token family mismatch - possible token theft
            user.refresh_token_family = str(uuid.uuid4())  # Invalidate all tokens
            db.commit()
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        
        if hasattr(user, 'refresh_token_version') and user.refresh_token_version > token_version:
            # Old token used - possible token theft
            user.refresh_token_family = str(uuid.uuid4())  # Invalidate all tokens
            db.commit()
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token already used"
            )
        
        # Update token version
        user.refresh_token_version = token_version + 1
        db.commit()
        
        # Create new tokens (sub must be a string for JWT)
        new_access_token = create_access_token(
            data={"sub": str(user.id), "email": user.email}
        )
        new_refresh_token = create_refresh_token(
            data={
                "sub": str(user.id),
                "email": user.email,
                "family": user.refresh_token_family,
                "version": user.refresh_token_version
            }
        )
        
        # Set new cookies
        set_auth_cookies(response, new_access_token, new_refresh_token, request=request)
        
        return {"message": "Token refreshed successfully"}
        
    except (InvalidTokenError, ValueError) as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )


@router.post("/logout")
async def logout(response: Response):
    """Logout user by clearing cookies."""
    clear_auth_cookies(response)
    return {"message": "Logged out successfully"}


@router.get("/check")
async def check_auth(request: Request, db: Session = Depends(get_db)):
    """Check if user is authenticated via cookies."""
    
    # Get access token from cookie
    access_token = request.cookies.get("access_token")
    if not access_token:
        return {"authenticated": False}
    
    try:
        # Decode token
        payload = decode_token(access_token)
        user_id = payload.get("sub")
        
        # Get user
        user = db.query(User).filter(User.id == user_id).first()
        if not user or not user.is_active:
            return {"authenticated": False}
        
        return {
            "authenticated": True,
            "user": UserData(
                id=user.id,
                email=user.email,
                full_name=user.full_name,
                company_name=user.company_name,
                account_type=user.account_type,
                created_at=user.created_at,
                daily_generations=user.daily_generations,
                daily_limit=user.get_daily_limit()
            )
        }
        
    except (InvalidTokenError, ValueError):
        return {"authenticated": False}


# Cookie-based authentication dependency
async def get_current_user_cookie(request: Request, db: Session = Depends(get_db)) -> Optional[User]:
    """Get current user from access token cookie."""
    
    access_token = request.cookies.get("access_token")
    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    
    try:
        payload = decode_token(access_token)
        user_id = payload.get("sub")
        
        user = db.query(User).filter(User.id == user_id).first()
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid user"
            )
        
        return user
        
    except (InvalidTokenError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )


@router.get("/me")
async def get_current_user_info(request: Request, db: Session = Depends(get_db)):
    """Get current user info from cookie (no CSRF required for GET)."""
    
    # Get access token from cookie
    access_token = request.cookies.get("access_token")
    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    
    try:
        # Decode token
        payload = decode_token(access_token)
        user_id = payload.get("sub")
        
        # Get user
        user = db.query(User).filter(User.id == user_id).first()
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid user"
            )
        
        return {
            "user": UserData(
                id=user.id,
                email=user.email,
                full_name=user.full_name,
                company_name=user.company_name,
                account_type=user.account_type,
                created_at=user.created_at,
                daily_generations=user.daily_generations,
                daily_limit=user.get_daily_limit()
            )
        }
        
    except (InvalidTokenError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )


@router.get("/profile")
async def get_profile(current_user: User = Depends(get_current_user_cookie)):
    """Get current user profile using cookie auth."""
    
    return {
        "user": UserData(
            id=current_user.id,
            email=current_user.email,
            full_name=current_user.full_name,
            company_name=current_user.company_name,
            account_type=current_user.account_type,
            created_at=current_user.created_at,
            daily_generations=current_user.daily_generations,
            daily_limit=current_user.get_daily_limit()
        )
    }