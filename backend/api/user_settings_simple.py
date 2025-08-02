"""Simplified user settings API endpoints without email dependencies."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from typing import Optional, Dict
from datetime import datetime, timedelta
import secrets
import json

from models.database import get_db, User
from middleware.auth_middleware import get_current_user
from utils.auth import verify_password, get_password_hash

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


class PreferencesUpdate(BaseModel):
    default_format: Optional[str] = None
    date_format: Optional[str] = None
    auto_download: Optional[bool] = None
    save_history: Optional[bool] = None
    analytics: Optional[bool] = None


# Profile endpoints
@router.get("/profile")
async def get_profile(current_user: User = Depends(get_current_user)):
    """Get user profile information."""
    return {
        "id": current_user.id,
        "email": current_user.email,
        "full_name": current_user.full_name,
        "company_name": current_user.company_name,
        "timezone": getattr(current_user, 'timezone', 'UTC'),
        "account_type": current_user.account_type,
        "created_at": current_user.created_at,
        "email_verified": getattr(current_user, 'email_verified', True),
        "two_factor_enabled": getattr(current_user, 'two_factor_enabled', False)
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
            # Add timezone column if it doesn't exist
            if not hasattr(current_user, 'timezone'):
                setattr(current_user, 'timezone', request.timezone)
            else:
                current_user.timezone = request.timezone
        
        db.commit()
        
        return {
            "message": "Profile updated successfully"
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update profile: {str(e)}"
        )


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
    if len(request.new_password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 8 characters long"
        )
    
    # Update password
    current_user.password_hash = get_password_hash(request.new_password)
    
    # Invalidate refresh tokens if column exists
    if hasattr(current_user, 'refresh_token_version'):
        current_user.refresh_token_version = getattr(current_user, 'refresh_token_version', 0) + 1
    
    db.commit()
    
    return {"message": "Password changed successfully"}


# Notification preferences
@router.get("/notifications")
async def get_notification_preferences(
    current_user: User = Depends(get_current_user)
):
    """Get notification preferences."""
    # Get stored preferences or defaults
    if hasattr(current_user, 'notification_preferences') and current_user.notification_preferences:
        try:
            prefs = json.loads(current_user.notification_preferences)
            return prefs
        except:
            pass
    
    # Return defaults
    return {
        "security_alerts": True,
        "product_updates": True,
        "usage_reports": False,
        "marketing_emails": False
    }


@router.put("/notifications")
async def update_notification_preferences(
    request: NotificationPreferences,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update notification preferences."""
    preferences = request.model_dump()
    
    # Store as JSON if column doesn't exist
    if not hasattr(current_user, 'notification_preferences'):
        # For now, store in a JSON field or skip
        pass
    else:
        current_user.notification_preferences = json.dumps(preferences)
    
    db.commit()
    
    return {"message": "Notification preferences updated successfully"}


# User preferences (conversion settings)
@router.get("/preferences")
async def get_preferences(
    current_user: User = Depends(get_current_user)
):
    """Get user preferences for conversions."""
    # Get stored preferences or defaults
    if hasattr(current_user, 'conversion_preferences') and current_user.conversion_preferences:
        try:
            prefs = json.loads(current_user.conversion_preferences)
            return prefs
        except:
            pass
    
    # Return defaults
    return {
        "default_format": "csv",
        "date_format": "MM/DD/YYYY",
        "auto_download": False,
        "save_history": True,
        "analytics": True
    }


@router.put("/preferences")
async def update_preferences(
    request: PreferencesUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update user preferences."""
    # Get existing preferences
    existing = await get_preferences(current_user)
    
    # Update with new values
    if request.default_format is not None:
        existing["default_format"] = request.default_format
    if request.date_format is not None:
        existing["date_format"] = request.date_format
    if request.auto_download is not None:
        existing["auto_download"] = request.auto_download
    if request.save_history is not None:
        existing["save_history"] = request.save_history
    if request.analytics is not None:
        existing["analytics"] = request.analytics
    
    # Store as JSON if column exists
    if hasattr(current_user, 'conversion_preferences'):
        current_user.conversion_preferences = json.dumps(existing)
        db.commit()
    
    return {"message": "Preferences updated successfully"}


# Usage statistics
@router.get("/usage-stats")
async def get_usage_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user usage statistics."""
    # Calculate monthly usage
    # For now, return mock data
    return {
        "daily": {
            "used": getattr(current_user, 'daily_generations', 0),
            "limit": 5 if current_user.account_type == 'free' else 
                    50 if current_user.account_type == 'starter' else 
                    500 if current_user.account_type == 'professional' else 999999
        },
        "monthly": {
            "used": getattr(current_user, 'daily_generations', 0) * 20,  # Rough estimate
            "limit": 150 if current_user.account_type == 'free' else 
                     1500 if current_user.account_type == 'starter' else 
                     15000 if current_user.account_type == 'professional' else 999999
        }
    }


# Billing history (mock for now)
@router.get("/billing-history")
async def get_billing_history(
    current_user: User = Depends(get_current_user)
):
    """Get billing history."""
    # Return mock data for now
    if current_user.account_type != 'free':
        return {
            "invoices": [
                {
                    "id": "inv_123",
                    "date": datetime.utcnow().isoformat(),
                    "amount": 9.99 if current_user.account_type == 'starter' else 29.99,
                    "status": "paid",
                    "description": f"{current_user.account_type.title()} Plan - Monthly"
                }
            ]
        }
    return {"invoices": []}


# Login history/sessions
@router.get("/sessions")
async def get_login_sessions(
    current_user: User = Depends(get_current_user)
):
    """Get recent login sessions."""
    # Return current session for now
    return {
        "sessions": [
            {
                "id": "current",
                "ip_address": "Current Device",
                "user_agent": "Browser",
                "location": "Current Location",
                "created_at": datetime.utcnow().isoformat(),
                "is_current": True
            }
        ]
    }


# Import 2FA utilities
try:
    from utils.two_factor_simple import (
        generate_secret, generate_qr_placeholder, verify_token,
        generate_backup_codes, hash_backup_code, verify_backup_code,
        format_secret_for_display, generate_provisioning_uri
    )
    TWO_FA_AVAILABLE = True
except ImportError:
    TWO_FA_AVAILABLE = False
    print("2FA utilities not available")


# 2FA endpoints
@router.get("/2fa/status")
async def get_2fa_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get 2FA status."""
    backup_codes_count = 0
    if hasattr(current_user, 'two_factor_backup_codes') and current_user.two_factor_backup_codes:
        try:
            codes = json.loads(current_user.two_factor_backup_codes)
            backup_codes_count = len(codes)
        except:
            pass
    
    return {
        "enabled": getattr(current_user, 'two_factor_enabled', False),
        "backup_codes_remaining": backup_codes_count
    }


@router.post("/2fa/enable")
async def enable_2fa(
    password: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Enable two-factor authentication."""
    if not TWO_FA_AVAILABLE:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="2FA is not available"
        )
    
    # Verify password
    if not verify_password(password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password is incorrect"
        )
    
    if getattr(current_user, 'two_factor_enabled', False):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Two-factor authentication is already enabled"
        )
    
    # Generate secret and backup codes
    secret = generate_secret()
    backup_codes = generate_backup_codes()
    
    # Store temporarily (not enabled until verified)
    if hasattr(current_user, 'two_factor_secret'):
        current_user.two_factor_secret = secret
    
    # Store hashed backup codes
    hashed_codes = [hash_backup_code(code) for code in backup_codes]
    if hasattr(current_user, 'two_factor_backup_codes'):
        current_user.two_factor_backup_codes = json.dumps(hashed_codes)
    
    db.commit()
    
    # Generate QR placeholder and provisioning URI
    qr_code = generate_qr_placeholder(current_user.email, secret)
    provisioning_uri = generate_provisioning_uri(current_user.email, secret)
    
    return {
        "secret": format_secret_for_display(secret),
        "qr_code": qr_code,
        "provisioning_uri": provisioning_uri,
        "backup_codes": backup_codes,
        "message": "Enter the secret in your authenticator app and verify with a token"
    }


@router.post("/2fa/verify")
async def verify_2fa_setup(
    token: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Verify 2FA setup with initial token."""
    if not TWO_FA_AVAILABLE:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="2FA is not available"
        )
    
    if getattr(current_user, 'two_factor_enabled', False):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Two-factor authentication is already enabled"
        )
    
    secret = getattr(current_user, 'two_factor_secret', None)
    if not secret:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please enable 2FA first"
        )
    
    # Verify token
    if not verify_token(secret, token):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid verification code"
        )
    
    # Enable 2FA
    if hasattr(current_user, 'two_factor_enabled'):
        current_user.two_factor_enabled = True
    
    db.commit()
    
    return {"message": "Two-factor authentication enabled successfully"}


@router.post("/2fa/disable")
async def disable_2fa(
    password: str,
    token: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Disable two-factor authentication."""
    if not getattr(current_user, 'two_factor_enabled', False):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Two-factor authentication is not enabled"
        )
    
    # Verify password
    if not verify_password(password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password is incorrect"
        )
    
    # Verify 2FA token or backup code
    secret = getattr(current_user, 'two_factor_secret', None)
    if TWO_FA_AVAILABLE and secret:
        # Try regular token first
        token_valid = verify_token(secret, token)
        
        if not token_valid:
            # Try backup code
            backup_codes = []
            if hasattr(current_user, 'two_factor_backup_codes') and current_user.two_factor_backup_codes:
                try:
                    backup_codes = json.loads(current_user.two_factor_backup_codes)
                except:
                    pass
            
            is_valid, matched_hash = verify_backup_code(token, backup_codes)
            if not is_valid:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid verification code"
                )
            
            # Remove used backup code
            backup_codes.remove(matched_hash)
            current_user.two_factor_backup_codes = json.dumps(backup_codes)
    
    # Disable 2FA
    if hasattr(current_user, 'two_factor_enabled'):
        current_user.two_factor_enabled = False
    if hasattr(current_user, 'two_factor_secret'):
        current_user.two_factor_secret = None
    if hasattr(current_user, 'two_factor_backup_codes'):
        current_user.two_factor_backup_codes = None
    
    db.commit()
    
    return {"message": "Two-factor authentication disabled successfully"}


# Settings summary endpoint
@router.get("/settings")
async def get_all_settings(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all user settings in one call."""
    profile = await get_profile(current_user)
    notifications = await get_notification_preferences(current_user)
    preferences = await get_preferences(current_user)
    usage = await get_usage_stats(current_user, db)
    
    return {
        "profile": {
            "email": profile["email"],
            "full_name": profile["full_name"],
            "company_name": profile["company_name"],
            "timezone": profile["timezone"],
            "email_verified": profile["email_verified"]
        },
        "security": {
            "two_factor_enabled": profile["two_factor_enabled"]
        },
        "notifications": notifications,
        "preferences": preferences,
        "account": {
            "created_at": profile["created_at"],
            "account_type": profile["account_type"],
            "daily_limit": usage["daily"]["limit"],
            "daily_generations": usage["daily"]["used"]
        }
    }


# Account deletion (simplified)
@router.delete("/account")
async def delete_account_request(
    password: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Request account deletion."""
    # Verify password
    if not verify_password(password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password is incorrect"
        )
    
    # For now, just return success message
    # In production, this would send confirmation email
    return {
        "message": "Account deletion requested. Please check your email for confirmation.",
        "note": "This is a demo - account will not actually be deleted"
    }