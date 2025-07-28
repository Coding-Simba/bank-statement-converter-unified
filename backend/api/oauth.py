"""OAuth authentication endpoints for Google and Microsoft."""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
import httpx
import secrets
import urllib.parse
from datetime import datetime, timedelta
from typing import Optional

from models.database import get_db, User
from config.oauth import (
    oauth_settings, 
    GOOGLE_AUTH_URL, GOOGLE_TOKEN_URL, GOOGLE_USER_INFO_URL,
    MICROSOFT_AUTH_URL, MICROSOFT_TOKEN_URL, MICROSOFT_USER_INFO_URL
)
from utils.auth import create_access_token

router = APIRouter(prefix="/api/auth", tags=["oauth"])

# Store state tokens temporarily (in production, use Redis or similar)
oauth_states = {}

@router.get("/google")
async def google_login():
    """Initiate Google OAuth login."""
    state = secrets.token_urlsafe(32)
    oauth_states[state] = {"provider": "google", "created_at": datetime.utcnow()}
    
    params = {
        "client_id": oauth_settings.google_client_id,
        "redirect_uri": oauth_settings.google_redirect_uri,
        "response_type": "code",
        "scope": "openid email profile",
        "state": state,
        "access_type": "offline",
        "prompt": "consent"
    }
    
    auth_url = f"{GOOGLE_AUTH_URL}?{urllib.parse.urlencode(params)}"
    return RedirectResponse(url=auth_url)

@router.get("/google/callback")
async def google_callback(
    code: str,
    state: str,
    db: Session = Depends(get_db)
):
    """Handle Google OAuth callback."""
    # Verify state
    if state not in oauth_states or oauth_states[state]["provider"] != "google":
        return RedirectResponse(
            url=f"{oauth_settings.frontend_url}{oauth_settings.error_redirect_url}invalid_state"
        )
    
    # Clean up state
    del oauth_states[state]
    
    try:
        # Exchange code for token
        async with httpx.AsyncClient() as client:
            token_response = await client.post(
                GOOGLE_TOKEN_URL,
                data={
                    "client_id": oauth_settings.google_client_id,
                    "client_secret": oauth_settings.google_client_secret,
                    "code": code,
                    "redirect_uri": oauth_settings.google_redirect_uri,
                    "grant_type": "authorization_code"
                }
            )
            
            if token_response.status_code != 200:
                raise HTTPException(status_code=400, detail="Failed to get access token")
            
            token_data = token_response.json()
            access_token = token_data["access_token"]
            
            # Get user info
            user_response = await client.get(
                GOOGLE_USER_INFO_URL,
                headers={"Authorization": f"Bearer {access_token}"}
            )
            
            if user_response.status_code != 200:
                raise HTTPException(status_code=400, detail="Failed to get user info")
            
            user_data = user_response.json()
            
        # Check if user exists
        user = db.query(User).filter(User.email == user_data["email"]).first()
        
        if not user:
            # Create new user
            user = User(
                email=user_data["email"],
                full_name=user_data.get("name"),
                auth_provider="google",
                provider_user_id=user_data["id"],
                email_verified=user_data.get("verified_email", False),
                account_type="free",
                subscription_status="free"
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        else:
            # Update existing user if needed
            if user.auth_provider == "email":
                # User previously signed up with email, link Google account
                user.auth_provider = "google"
                user.provider_user_id = user_data["id"]
                user.email_verified = True
                db.commit()
        
        # Create JWT token
        access_token = create_access_token(data={"sub": str(user.id), "email": user.email})
        
        # Redirect to frontend with token
        redirect_url = f"{oauth_settings.frontend_url}{oauth_settings.success_redirect_url}?token={access_token}"
        return RedirectResponse(url=redirect_url)
        
    except Exception as e:
        return RedirectResponse(
            url=f"{oauth_settings.frontend_url}{oauth_settings.error_redirect_url}authentication_failed"
        )

@router.get("/microsoft")
async def microsoft_login():
    """Initiate Microsoft OAuth login."""
    state = secrets.token_urlsafe(32)
    oauth_states[state] = {"provider": "microsoft", "created_at": datetime.utcnow()}
    
    params = {
        "client_id": oauth_settings.microsoft_client_id,
        "redirect_uri": oauth_settings.microsoft_redirect_uri,
        "response_type": "code",
        "scope": "openid email profile User.Read",
        "state": state,
        "response_mode": "query"
    }
    
    auth_url = f"{MICROSOFT_AUTH_URL}?{urllib.parse.urlencode(params)}"
    return RedirectResponse(url=auth_url)

@router.get("/microsoft/callback")
async def microsoft_callback(
    code: str,
    state: str,
    db: Session = Depends(get_db)
):
    """Handle Microsoft OAuth callback."""
    # Verify state
    if state not in oauth_states or oauth_states[state]["provider"] != "microsoft":
        return RedirectResponse(
            url=f"{oauth_settings.frontend_url}{oauth_settings.error_redirect_url}invalid_state"
        )
    
    # Clean up state
    del oauth_states[state]
    
    try:
        # Exchange code for token
        async with httpx.AsyncClient() as client:
            token_response = await client.post(
                MICROSOFT_TOKEN_URL,
                data={
                    "client_id": oauth_settings.microsoft_client_id,
                    "client_secret": oauth_settings.microsoft_client_secret,
                    "code": code,
                    "redirect_uri": oauth_settings.microsoft_redirect_uri,
                    "grant_type": "authorization_code"
                }
            )
            
            if token_response.status_code != 200:
                raise HTTPException(status_code=400, detail="Failed to get access token")
            
            token_data = token_response.json()
            access_token = token_data["access_token"]
            
            # Get user info from Microsoft Graph
            user_response = await client.get(
                MICROSOFT_USER_INFO_URL,
                headers={"Authorization": f"Bearer {access_token}"}
            )
            
            if user_response.status_code != 200:
                raise HTTPException(status_code=400, detail="Failed to get user info")
            
            user_data = user_response.json()
            
        # Check if user exists
        email = user_data.get("mail") or user_data.get("userPrincipalName")
        user = db.query(User).filter(User.email == email).first()
        
        if not user:
            # Create new user
            user = User(
                email=email,
                full_name=user_data.get("displayName"),
                auth_provider="microsoft",
                provider_user_id=user_data["id"],
                email_verified=True,  # Microsoft accounts are verified
                account_type="free",
                subscription_status="free"
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        else:
            # Update existing user if needed
            if user.auth_provider == "email":
                # User previously signed up with email, link Microsoft account
                user.auth_provider = "microsoft"
                user.provider_user_id = user_data["id"]
                user.email_verified = True
                db.commit()
        
        # Create JWT token
        access_token = create_access_token(data={"sub": str(user.id), "email": user.email})
        
        # Redirect to frontend with token
        redirect_url = f"{oauth_settings.frontend_url}{oauth_settings.success_redirect_url}?token={access_token}"
        return RedirectResponse(url=redirect_url)
        
    except Exception as e:
        return RedirectResponse(
            url=f"{oauth_settings.frontend_url}{oauth_settings.error_redirect_url}authentication_failed"
        )

# Clean up old states periodically (in production, use a background task)
async def cleanup_old_states():
    """Remove OAuth states older than 10 minutes."""
    current_time = datetime.utcnow()
    expired_states = []
    
    for state, data in oauth_states.items():
        if current_time - data["created_at"] > timedelta(minutes=10):
            expired_states.append(state)
    
    for state in expired_states:
        del oauth_states[state]