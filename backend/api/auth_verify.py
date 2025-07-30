"""Auth verification endpoint"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import User
from ..auth import get_current_user

router = APIRouter()

@router.get("/auth/verify")
async def verify_token(current_user: User = Depends(get_current_user)):
    """Verify if the current auth token is valid"""
    if not current_user:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    return {
        "valid": True,
        "user": {
            "id": current_user.id,
            "email": current_user.email,
            "fullName": current_user.full_name,
            "plan": current_user.plan or "free"
        }
    }

@router.get("/auth/me")
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user information"""
    return {
        "id": current_user.id,
        "email": current_user.email,
        "fullName": current_user.full_name,
        "company": current_user.company,
        "plan": current_user.plan or "free",
        "created_at": current_user.created_at,
        "verified": current_user.is_verified
    }