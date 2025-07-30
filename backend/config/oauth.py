"""OAuth configuration for Google and Microsoft authentication."""

import os
from typing import Optional
from pydantic_settings import BaseSettings

class OAuthSettings(BaseSettings):
    """OAuth provider settings."""
    
    # Google OAuth
    google_client_id: str = os.getenv("GOOGLE_CLIENT_ID", "")
    google_client_secret: str = os.getenv("GOOGLE_CLIENT_SECRET", "")
    google_redirect_uri: str = os.getenv("GOOGLE_REDIRECT_URI", "https://bankcsvconverter.com/api/auth/google/callback")
    
    # Microsoft OAuth
    microsoft_client_id: str = os.getenv("MICROSOFT_CLIENT_ID", "")
    microsoft_client_secret: str = os.getenv("MICROSOFT_CLIENT_SECRET", "")
    microsoft_redirect_uri: str = os.getenv("MICROSOFT_REDIRECT_URI", "https://bankcsvconverter.com/api/auth/microsoft/callback")
    microsoft_tenant: str = os.getenv("MICROSOFT_TENANT", "common")  # 'common' for multi-tenant
    
    # JWT Settings
    jwt_secret_key: str = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-this-in-production")
    jwt_algorithm: str = "HS256"
    jwt_expiration_minutes: int = 60 * 24 * 7  # 7 days
    
    # Email verification
    email_verification_expire_hours: int = 48
    password_reset_expire_hours: int = 2
    
    # Frontend URLs
    frontend_url: str = os.getenv("FRONTEND_URL", "https://bankcsvconverter.com")
    success_redirect_url: str = os.getenv("SUCCESS_REDIRECT_URL", "/oauth-callback.html")
    error_redirect_url: str = os.getenv("ERROR_REDIRECT_URL", "/oauth-callback.html?error=")
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"  # Ignore extra fields in .env

oauth_settings = OAuthSettings()

# OAuth URLs
GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USER_INFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"

MICROSOFT_AUTH_URL = f"https://login.microsoftonline.com/{oauth_settings.microsoft_tenant}/oauth2/v2.0/authorize"
MICROSOFT_TOKEN_URL = f"https://login.microsoftonline.com/{oauth_settings.microsoft_tenant}/oauth2/v2.0/token"
MICROSOFT_USER_INFO_URL = "https://graph.microsoft.com/v1.0/me"