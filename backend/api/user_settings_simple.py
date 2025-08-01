"""User settings API endpoints - Simplified version without email."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional
from datetime import datetime
import secrets
import logging
import json

from models.database import get_db, User
from middleware.auth_middleware import get_current_user
from utils.auth import verify_password, get_password_hash, validate_password
from utils.two_factor import (
    generate_secret, generate_qr_code, verify_token,
    generate_backup_codes, hash_backup_code, verify_backup_code,
    format_secret_for_display
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/user", tags=["user-settings"])


# Pydantic models
class ProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    company_name: Optional[str] = None
    timezone: Optional[str] = None


class PasswordChange(BaseModel):
    current_password: str
    new_password: str


class NotificationPreferences(BaseModel):
    security_alerts: bool = True
    product_updates: bool = True
    usage_reports: bool = False
    marketing_emails: bool = False


# Profile endpoints
@router.get("/profile")
async def get_profile(current_user: User = Depends(get_current_user)):
    """Get user profile information."""
    return {
        "id": current_user.id,
        "email": current_user.email,
        "full_name": current_user.full_name,
        "company_name": current_user.company_name,
        "timezone": current_user.timezone,
        "account_type": current_user.account_type,
        "created_at": current_user.created_at,
        "email_verified": current_user.email_verified,
        "two_factor_enabled": current_user.two_factor_enabled
    }


@router.put("/profile")
async def update_profile(
    request: ProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update user profile information."""
    try:
        # Update basic fields
        if request.full_name is not None:
            current_user.full_name = request.full_name
        if request.company_name is not None:
            current_user.company_name = request.company_name
        if request.timezone is not None:
            current_user.timezone = request.timezone
        
        db.commit()
        
        return {
            "message": "Profile updated successfully"
        }
        
    except Exception as e:
        db.rollback()
        logger.error(f"Profile update error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update profile"
        )


# Security endpoints
@router.put("/password")
async def change_password(
    request: PasswordChange,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Change user password."""
    # Verify current password
    if not verify_password(request.current_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )
    
    # Validate new password
    is_valid, message = validate_password(request.new_password)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message
        )
    
    # Update password
    current_user.password_hash = get_password_hash(request.new_password)
    current_user.refresh_token_version += 1
    
    db.commit()
    
    return {"message": "Password changed successfully"}


# Notification preferences
@router.get("/notifications")
async def get_notification_preferences(
    current_user: User = Depends(get_current_user)
):
    """Get notification preferences."""
    return current_user.get_notification_preferences()


@router.put("/notifications")
async def update_notification_preferences(
    request: NotificationPreferences,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update notification preferences."""
    preferences = request.model_dump()
    current_user.set_notification_preferences(preferences)
    db.commit()
    
    return {"message": "Notification preferences updated successfully"}


# API key management
@router.post("/api-key")
async def generate_api_key(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generate a new API key."""
    # Generate API key
    api_key = f"bcsv_{secrets.token_urlsafe(24)}"
    
    # Store API key
    current_user.api_key = api_key
    current_user.api_key_created_at = datetime.utcnow()
    db.commit()
    
    return {
        "api_key": api_key,
        "created_at": current_user.api_key_created_at,
        "message": "Save this key securely - it won't be shown again"
    }


@router.delete("/api-key")
async def revoke_api_key(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Revoke the current API key."""
    if not current_user.api_key:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No API key to revoke"
        )
    
    current_user.api_key = None
    current_user.api_key_created_at = None
    db.commit()
    
    return {"message": "API key revoked successfully"}


@router.get("/api-keys")
async def list_api_keys(
    current_user: User = Depends(get_current_user)
):
    """List API keys (shows only metadata)."""
    if not current_user.api_key:
        return {"api_keys": []}
    
    return {
        "api_keys": [{
            "preview": f"****{current_user.api_key[-4:]}",
            "created_at": current_user.api_key_created_at
        }]
    }


# Settings summary endpoint
@router.get("/settings")
async def get_all_settings(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all user settings in one call."""
    # Get subscription info
    subscription_info = None
    if current_user.stripe_customer_id:
        subscription_info = {
            "plan": current_user.subscription_plan,
            "status": current_user.subscription_status,
            "expires_at": current_user.subscription_expires_at
        }
    
    return {
        "profile": {
            "email": current_user.email,
            "full_name": current_user.full_name,
            "company_name": current_user.company_name,
            "timezone": current_user.timezone,
            "email_verified": current_user.email_verified
        },
        "security": {
            "two_factor_enabled": current_user.two_factor_enabled,
            "has_api_key": bool(current_user.api_key),
            "api_key_created_at": current_user.api_key_created_at
        },
        "notifications": current_user.get_notification_preferences(),
        "subscription": subscription_info,
        "account": {
            "created_at": current_user.created_at,
            "account_type": current_user.account_type,
            "daily_limit": current_user.get_daily_limit(),
            "daily_generations": current_user.daily_generations
        }
    }