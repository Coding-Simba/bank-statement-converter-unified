"""User settings API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional, Dict, List
from datetime import datetime, timedelta
import secrets
import logging
import os

from models.database import get_db, User
from middleware.auth_middleware import get_current_user
from utils.auth import verify_password, get_password_hash, validate_password
from utils.email import email_service
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
    email: Optional[EmailStr] = None
    
    @field_validator('timezone')
    def validate_timezone(cls, v):
        if v:
            valid_timezones = [
                "UTC", "America/New_York", "America/Chicago", 
                "America/Denver", "America/Los_Angeles", "Europe/London",
                "Europe/Paris", "Asia/Tokyo", "Australia/Sydney"
            ]
            if v not in valid_timezones:
                raise ValueError("Invalid timezone")
        return v


class PasswordChange(BaseModel):
    current_password: str
    new_password: str


class NotificationPreferences(BaseModel):
    security_alerts: bool = True
    product_updates: bool = True
    usage_reports: bool = False
    marketing_emails: bool = False


class TwoFactorEnable(BaseModel):
    password: str


class TwoFactorVerify(BaseModel):
    token: str


class TwoFactorDisable(BaseModel):
    password: str
    token: str  # Current 2FA token required to disable


class AccountDelete(BaseModel):
    password: str


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
        
        # Handle email change
        if request.email and request.email != current_user.email:
            # Check if email already exists
            existing_user = db.query(User).filter(User.email == request.email).first()
            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already in use"
                )
            
            # Generate verification token
            verification_token = secrets.token_urlsafe(32)
            current_user.pending_email = request.email
            current_user.pending_email_token = verification_token
            current_user.pending_email_expires = datetime.utcnow() + timedelta(hours=24)
            
            # Send verification email
            verification_url = f"https://bankcsvconverter.com/api/user/verify-email?token={verification_token}"
            await email_service.send_email_verification(request.email, verification_url)
        
        db.commit()
        
        return {
            "message": "Profile updated successfully",
            "email_verification_sent": request.email and request.email != current_user.email
        }
        
    except Exception as e:
        db.rollback()
        logger.error(f"Profile update error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update profile"
        )


@router.get("/verify-email")
async def verify_email_change(
    token: str,
    db: Session = Depends(get_db)
):
    """Verify email change token."""
    user = db.query(User).filter(
        User.pending_email_token == token,
        User.pending_email_expires > datetime.utcnow()
    ).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification token"
        )
    
    # Update email
    user.email = user.pending_email
    user.email_verified = True
    user.pending_email = None
    user.pending_email_token = None
    user.pending_email_expires = None
    
    db.commit()
    
    # Redirect to success page
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/settings.html?email_verified=true")


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
    # Invalidate refresh tokens to force re-login
    current_user.refresh_token_version += 1
    
    db.commit()
    
    # Send notification email
    await email_service.send_password_changed_email(
        current_user.email,
        current_user.full_name
    )
    
    return {"message": "Password changed successfully"}


# 2FA endpoints
@router.post("/2fa/enable")
async def enable_2fa(
    request: TwoFactorEnable,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Enable two-factor authentication."""
    # Verify password
    if not verify_password(request.password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password is incorrect"
        )
    
    if current_user.two_factor_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Two-factor authentication is already enabled"
        )
    
    # Generate secret and backup codes
    secret = generate_secret()
    backup_codes = generate_backup_codes()
    
    # Store hashed backup codes
    hashed_codes = [hash_backup_code(code) for code in backup_codes]
    current_user.two_factor_secret = secret
    current_user.set_backup_codes(hashed_codes)
    
    db.commit()
    
    # Generate QR code
    qr_code = generate_qr_code(current_user.email, secret)
    
    return {
        "secret": format_secret_for_display(secret),
        "qr_code": qr_code,
        "backup_codes": backup_codes,
        "message": "Scan the QR code with your authenticator app and verify with a token"
    }


@router.post("/2fa/verify")
async def verify_2fa_setup(
    request: TwoFactorVerify,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Verify 2FA setup with initial token."""
    if current_user.two_factor_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Two-factor authentication is already enabled"
        )
    
    if not current_user.two_factor_secret:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please enable 2FA first"
        )
    
    # Verify token
    if not verify_token(current_user.two_factor_secret, request.token):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid verification code"
        )
    
    # Enable 2FA
    current_user.two_factor_enabled = True
    db.commit()
    
    # Send notification
    await email_service.send_2fa_enabled_email(
        current_user.email,
        current_user.full_name
    )
    
    return {"message": "Two-factor authentication enabled successfully"}


@router.post("/2fa/disable")
async def disable_2fa(
    request: TwoFactorDisable,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Disable two-factor authentication."""
    if not current_user.two_factor_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Two-factor authentication is not enabled"
        )
    
    # Verify password
    if not verify_password(request.password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password is incorrect"
        )
    
    # Verify 2FA token
    if not verify_token(current_user.two_factor_secret, request.token):
        # Try backup code
        backup_codes = current_user.get_backup_codes()
        is_valid, matched_hash = verify_backup_code(request.token, backup_codes)
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid verification code"
            )
    
    # Disable 2FA
    current_user.two_factor_enabled = False
    current_user.two_factor_secret = None
    current_user.two_factor_backup_codes = None
    db.commit()
    
    # Send notification
    await email_service.send_2fa_disabled_email(
        current_user.email,
        current_user.full_name
    )
    
    return {"message": "Two-factor authentication disabled successfully"}


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
    
    # Store API key (in production, hash it)
    current_user.api_key = api_key
    current_user.api_key_created_at = datetime.utcnow()
    db.commit()
    
    # Send notification
    api_key_preview = f"****{api_key[-4:]}"
    await email_service.send_api_key_generated_email(
        current_user.email,
        api_key_preview,
        current_user.full_name
    )
    
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


# Account deletion
@router.delete("/account")
async def delete_account_request(
    request: AccountDelete,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Request account deletion."""
    # Verify password
    if not verify_password(request.password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password is incorrect"
        )
    
    # Generate deletion token
    deletion_token = secrets.token_urlsafe(32)
    current_user.password_reset_token = deletion_token  # Reuse this field
    current_user.password_reset_expires = datetime.utcnow() + timedelta(hours=1)
    db.commit()
    
    # Send confirmation email
    deletion_url = f"https://bankcsvconverter.com/api/user/account/confirm-delete?token={deletion_token}"
    await email_service.send_account_deletion_confirmation(
        current_user.email,
        deletion_url,
        current_user.full_name
    )
    
    return {"message": "Account deletion confirmation sent to your email"}


@router.get("/account/confirm-delete")
async def confirm_account_deletion(
    token: str,
    db: Session = Depends(get_db)
):
    """Confirm account deletion."""
    user = db.query(User).filter(
        User.password_reset_token == token,
        User.password_reset_expires > datetime.utcnow()
    ).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired deletion token"
        )
    
    # Cancel Stripe subscription if exists
    if user.stripe_customer_id:
        try:
            import stripe
            stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
            
            # Cancel all subscriptions
            subscriptions = stripe.Subscription.list(
                customer=user.stripe_customer_id,
                status='active'
            )
            
            for sub in subscriptions:
                stripe.Subscription.delete(sub.id)
        except Exception as e:
            logger.error(f"Failed to cancel Stripe subscription: {str(e)}")
    
    # Delete user and cascade will handle related records
    db.delete(user)
    db.commit()
    
    # Redirect to goodbye page
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/goodbye.html")


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
        # TODO: Fetch from Stripe
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