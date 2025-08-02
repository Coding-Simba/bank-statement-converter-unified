"""Authentication endpoints with session tracking integration."""

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

# Import session tracking
try:
    from api.login_sessions import create_login_session, end_login_session, update_session_activity
    from models.login_session import LoginSession
    SESSION_TRACKING_ENABLED = True
except ImportError:
    SESSION_TRACKING_ENABLED = False
    print("Session tracking not available")

router = APIRouter(prefix="/api/auth", tags=["authentication"])

# Constants
ACCESS_TOKEN_EXPIRE_MINUTES = 15
REFRESH_TOKEN_EXPIRE_HOURS = 24  # Default without remember me
REFRESH_TOKEN_EXPIRE_DAYS = 90  # With remember me
COOKIE_DOMAIN = ".bankcsvconverter.com"  # Cross-subdomain support


# Pydantic models
class UserLogin(BaseModel):
    email: EmailStr
    password: str
    remember_me: bool = False


class UserRegister(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    company_name: Optional[str] = None


class UserData(BaseModel):
    id: int
    email: str
    full_name: str
    company_name: Optional[str]
    account_type: str
    created_at: Optional[datetime]
    daily_generations: int
    daily_limit: int
    session_id: Optional[str] = None  # Include session ID


# Helper functions
def set_auth_cookies(
    response: Response, 
    access_token: str, 
    refresh_token: str,
    remember_me: bool = False,
    request: Optional[Request] = None,
    session_id: Optional[str] = None
):
    """Set authentication cookies with proper security settings."""
    # Determine if we're on localhost
    is_localhost = False
    if request:
        host = request.headers.get("host", "").lower()
        is_localhost = "localhost" in host or "127.0.0.1" in host
    
    # Cookie settings
    cookie_settings = {
        "httponly": True,
        "samesite": "lax",
        "path": "/"
    }
    
    if not is_localhost:
        cookie_settings["secure"] = True
        cookie_settings["domain"] = COOKIE_DOMAIN
    
    # Set access token cookie (short-lived)
    response.set_cookie(
        key="access_token",
        value=access_token,
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,  # Convert to seconds
        **cookie_settings
    )
    
    # Set refresh token cookie (long-lived)
    refresh_max_age = (
        REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60 if remember_me 
        else REFRESH_TOKEN_EXPIRE_HOURS * 60 * 60
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        max_age=refresh_max_age,
        **cookie_settings
    )
    
    # Set session ID cookie if available
    if session_id:
        response.set_cookie(
            key="session_id",
            value=session_id,
            max_age=refresh_max_age,
            **cookie_settings
        )


def clear_auth_cookies(response: Response, request: Optional[Request] = None):
    """Clear all authentication cookies."""
    is_localhost = False
    if request:
        host = request.headers.get("host", "").lower()
        is_localhost = "localhost" in host or "127.0.0.1" in host
    
    cookie_settings = {
        "httponly": True,
        "samesite": "lax",
        "path": "/"
    }
    
    if not is_localhost:
        cookie_settings["secure"] = True
        cookie_settings["domain"] = COOKIE_DOMAIN
    
    # Clear all auth cookies
    for cookie_name in ["access_token", "refresh_token", "session_id"]:
        response.set_cookie(
            key=cookie_name,
            value="",
            max_age=0,
            expires=0,
            **cookie_settings
        )


# Auth endpoints
@router.post("/register")
async def register(
    user_data: UserRegister,
    response: Response,
    request: Request,
    db: Session = Depends(get_db)
):
    """Register a new user with email and password."""
    # Validate email
    is_valid_email, email_error = validate_email(user_data.email)
    if not is_valid_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=email_error
        )
    
    # Validate password
    is_valid_password, password_error = validate_password(user_data.password)
    if not is_valid_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=password_error
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
    
    # Track login session
    session_id = None
    if SESSION_TRACKING_ENABLED:
        session = create_login_session(new_user.id, request, db, login_successful=True)
        session_id = session.session_id
    
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
    set_auth_cookies(response, access_token, refresh_token, request=request, session_id=session_id)
    
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
            daily_limit=new_user.get_daily_limit(),
            session_id=session_id
        )
    }


@router.post("/login")
async def login(
    user_credentials: UserLogin,
    response: Response,
    request: Request,
    db: Session = Depends(get_db)
):
    """Login with email and password."""
    # Find user
    user = db.query(User).filter(User.email == user_credentials.email).first()
    
    if not user:
        # Track failed login attempt
        if SESSION_TRACKING_ENABLED:
            # We don't have a user ID, so we can't track this properly
            # In a real system, you might track by IP or create a separate failed_logins table
            pass
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Verify password
    if not verify_password(user_credentials.password, user.password_hash):
        # Track failed login attempt
        if SESSION_TRACKING_ENABLED:
            create_login_session(user.id, request, db, login_successful=False)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Track successful login
    session_id = None
    if SESSION_TRACKING_ENABLED:
        session = create_login_session(user.id, request, db, login_successful=True)
        session_id = session.session_id
    
    # Update refresh token family if needed
    if not user.refresh_token_family:
        user.refresh_token_family = str(uuid.uuid4())
        db.commit()
    
    # Create tokens
    access_token = create_access_token(
        data={"sub": str(user.id), "email": user.email}
    )
    refresh_token = create_refresh_token(
        data={
            "sub": str(user.id),
            "email": user.email,
            "family": user.refresh_token_family,
            "version": user.refresh_token_version or 1
        }
    )
    
    # Set cookies
    set_auth_cookies(
        response, 
        access_token, 
        refresh_token, 
        remember_me=user_credentials.remember_me,
        request=request,
        session_id=session_id
    )
    
    # Return user data
    return {
        "user": UserData(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            company_name=user.company_name,
            account_type=user.account_type,
            created_at=user.created_at,
            daily_generations=user.daily_generations,
            daily_limit=user.get_daily_limit(),
            session_id=session_id
        )
    }


@router.post("/logout")
async def logout(
    response: Response,
    request: Request,
    db: Session = Depends(get_db)
):
    """Logout user and clear cookies."""
    # Get session ID from cookie
    session_id = request.cookies.get("session_id")
    
    # Get user from access token to track logout
    access_token = request.cookies.get("access_token")
    if access_token and SESSION_TRACKING_ENABLED and session_id:
        try:
            payload = decode_token(access_token)
            user_id = int(payload.get("sub"))
            # End the session
            end_login_session(user_id, session_id, "manual", db)
        except:
            pass  # Ignore errors during logout
    
    # Clear cookies
    clear_auth_cookies(response, request)
    
    return {"message": "Logged out successfully"}


@router.get("/me")
async def get_current_user(
    request: Request,
    db: Session = Depends(get_db)
):
    """Get current user from cookies."""
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
        user_id = int(payload.get("sub"))
        
        # Get user
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
        
        # Update session activity
        session_id = request.cookies.get("session_id")
        if SESSION_TRACKING_ENABLED and session_id:
            update_session_activity(user_id, session_id, db)
        
        return UserData(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            company_name=user.company_name,
            account_type=user.account_type,
            created_at=user.created_at,
            daily_generations=user.daily_generations,
            daily_limit=user.get_daily_limit(),
            session_id=session_id
        )
        
    except InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )


@router.post("/refresh")
async def refresh_tokens(
    response: Response,
    request: Request,
    db: Session = Depends(get_db)
):
    """Refresh access token using refresh token."""
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
        user_id = int(payload.get("sub"))
        token_family = payload.get("family")
        token_version = payload.get("version", 1)
        
        # Get user
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
        
        # Validate token family and version
        if (token_family != user.refresh_token_family or 
            token_version < (user.refresh_token_version or 1)):
            # Token has been revoked or is outdated
            clear_auth_cookies(response, request)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        
        # Update session activity
        session_id = request.cookies.get("session_id")
        if SESSION_TRACKING_ENABLED and session_id:
            update_session_activity(user_id, session_id, db)
        
        # Create new access token
        new_access_token = create_access_token(
            data={"sub": str(user.id), "email": user.email}
        )
        
        # Update access token cookie only
        is_localhost = "localhost" in request.headers.get("host", "").lower()
        cookie_settings = {
            "httponly": True,
            "samesite": "lax",
            "path": "/"
        }
        if not is_localhost:
            cookie_settings["secure"] = True
            cookie_settings["domain"] = COOKIE_DOMAIN
        
        response.set_cookie(
            key="access_token",
            value=new_access_token,
            max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            **cookie_settings
        )
        
        return {"message": "Token refreshed successfully"}
        
    except InvalidTokenError:
        clear_auth_cookies(response, request)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )


# CSRF Protection
@router.get("/csrf")
async def get_csrf_token(request: Request):
    """Get CSRF token for forms."""
    # Generate CSRF token
    csrf_token = secrets.token_urlsafe(32)
    
    # Store in session or return directly
    # For now, return directly (in production, store in session)
    return {"csrf_token": csrf_token}