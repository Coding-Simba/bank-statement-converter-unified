"""CSRF protection middleware for FastAPI."""

from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
import logging

logger = logging.getLogger(__name__)


class CSRFMiddleware(BaseHTTPMiddleware):
    """Middleware to validate CSRF tokens on state-changing requests."""
    
    def __init__(self, app: ASGIApp, exclude_paths: list = None):
        super().__init__(app)
        self.exclude_paths = exclude_paths or [
            "/docs",
            "/redoc",
            "/openapi.json",
            "/api/auth/csrf",  # CSRF token endpoint itself
            "/v2/api/auth/csrf",  # v2 CSRF token endpoint
            "/v2/api/auth/login",  # v2 login endpoint
            "/v2/api/auth/register",  # v2 register endpoint  
            "/v2/api/auth/me",  # v2 auth check endpoint
            "/api/auth/login",  # Temporarily exclude login
            "/api/auth/register",  # Temporarily exclude register
            "/api/convert"  # Temporarily exclude PDF conversion
        ]
    
    async def dispatch(self, request: Request, call_next):
        """Process request and validate CSRF token if needed."""
        
        # Skip CSRF check for excluded paths
        if any(request.url.path.startswith(path) for path in self.exclude_paths):
            return await call_next(request)
        
        # Skip CSRF check for safe methods
        if request.method in ["GET", "HEAD", "OPTIONS"]:
            return await call_next(request)
        
        # Validate CSRF token for state-changing requests
        csrf_header = request.headers.get("X-CSRF-Token")
        csrf_cookie = request.cookies.get("csrf_token")
        
        # Log for debugging
        logger.debug(f"CSRF check - Path: {request.url.path}, Method: {request.method}")
        logger.debug(f"CSRF header: {csrf_header[:10] if csrf_header else None}...")
        logger.debug(f"CSRF cookie: {csrf_cookie[:10] if csrf_cookie else None}...")
        
        # Validate CSRF token
        if not csrf_header or not csrf_cookie:
            logger.warning(f"CSRF token missing for {request.method} {request.url.path}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="CSRF token missing"
            )
        
        if csrf_header != csrf_cookie:
            logger.warning(f"CSRF token mismatch for {request.method} {request.url.path}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="CSRF token validation failed"
            )
        
        # CSRF token is valid, proceed with request
        response = await call_next(request)
        return response


def validate_csrf_token(request: Request):
    """Standalone function to validate CSRF token for specific endpoints."""
    csrf_header = request.headers.get("X-CSRF-Token")
    csrf_cookie = request.cookies.get("csrf_token")
    
    if not csrf_header or csrf_header != csrf_cookie:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="CSRF token validation failed"
        )
    
    return True