"""Authentication API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

from ..models.database import get_db, User
from ..utils.auth import (
    verify_password, get_password_hash, create_access_token, 
    create_refresh_token, validate_email, validate_password,
    generate_session_id
)
from ..middleware.auth_middleware import JWTBearer, get_current_user

router = APIRouter(prefix="/api/auth", tags=["authentication"])


# Pydantic models for request/response
class UserRegister(BaseModel):
    email: EmailStr
    password: str
    account_type: Optional[str] = "free"


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: int
    email: str
    account_type: str
    created_at: datetime
    daily_generations: int
    daily_limit: int
    
    class Config:
        orm_mode = True


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserResponse


@router.post("/register", response_model=TokenResponse)
async def register(user_data: UserRegister, db: Session = Depends(get_db)):
    """Register a new user account."""
    
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
    new_user = User(
        email=user_data.email,
        password_hash=hashed_password,
        account_type=user_data.account_type if user_data.account_type in ["free", "premium"] else "free"
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # Create tokens
    access_token = create_access_token(data={"sub": new_user.id, "email": new_user.email})
    refresh_token = create_refresh_token(data={"sub": new_user.id, "email": new_user.email})
    
    # Prepare user response
    user_response = UserResponse(
        id=new_user.id,
        email=new_user.email,
        account_type=new_user.account_type,
        created_at=new_user.created_at,
        daily_generations=new_user.daily_generations,
        daily_limit=new_user.get_daily_limit()
    )
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=user_response
    )


@router.post("/login", response_model=TokenResponse)
async def login(user_credentials: UserLogin, db: Session = Depends(get_db)):
    """Login with email and password."""
    
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
    db.commit()
    
    # Create tokens
    access_token = create_access_token(data={"sub": user.id, "email": user.email})
    refresh_token = create_refresh_token(data={"sub": user.id, "email": user.email})
    
    # Prepare user response
    user_response = UserResponse(
        id=user.id,
        email=user.email,
        account_type=user.account_type,
        created_at=user.created_at,
        daily_generations=user.daily_generations,
        daily_limit=user.get_daily_limit()
    )
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=user_response
    )


@router.get("/profile", response_model=UserResponse)
async def get_profile(current_user: User = Depends(get_current_user)):
    """Get current user profile."""
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        account_type=current_user.account_type,
        created_at=current_user.created_at,
        daily_generations=current_user.daily_generations,
        daily_limit=current_user.get_daily_limit()
    )


@router.post("/logout")
async def logout(response: Response):
    """Logout user (client should remove tokens)."""
    # For session-based tracking, we could clear the session cookie
    response.delete_cookie("session_id")
    return {"message": "Logged out successfully"}


@router.post("/refresh")
async def refresh_token(refresh_token: str, db: Session = Depends(get_db)):
    """Refresh access token using refresh token."""
    try:
        from ..utils.auth import decode_token
        payload = decode_token(refresh_token)
        
        if payload.get("type") != "refresh":
            raise ValueError("Invalid token type")
        
        user_id = payload.get("sub")
        user = db.query(User).filter(User.id == user_id).first()
        
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        
        # Create new access token
        access_token = create_access_token(data={"sub": user.id, "email": user.email})
        
        return {
            "access_token": access_token,
            "token_type": "bearer"
        }
    except:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )


@router.get("/session")
async def get_session(request: Request, response: Response):
    """Get or create session ID for anonymous users."""
    session_id = request.cookies.get("session_id")
    
    if not session_id:
        session_id = generate_session_id()
        response.set_cookie(
            key="session_id",
            value=session_id,
            httponly=True,
            secure=True,
            samesite="lax",
            max_age=86400  # 24 hours
        )
    
    return {"session_id": session_id}