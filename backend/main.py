"""Main FastAPI application for the bank statement converter backend."""

# Load environment variables first, before any other imports
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import os
from datetime import datetime
import asyncio

# Import routers
from api.auth import router as auth_router
from api.auth_cookie import router as auth_cookie_router
# from api.auth_verify import router as auth_verify_router  # Module not found
from api.statements import router as statements_router
from api.feedback import router as feedback_router
from api.oauth import router as oauth_router
from api.split_statement import router as split_statement_router
from api.analyze_transactions import router as analyze_transactions_router
from api.stripe_payments import router as stripe_router
# from api.user_statistics import router as user_statistics_router  # Module not found
# from api.statements_recent import router as statements_recent_router  # Module not found
# from api.statement_delete import router as statement_delete_router  # Module not found
# from api.user_export import router as user_export_router  # Module not found
# from api.user_settings import router as user_settings_router  # Commented out - requires aiosmtplib
from models.database import init_db, engine, Base
from utils.cleanup import cleanup_expired_statements
from middleware.csrf_middleware import CSRFMiddleware

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle."""
    # Startup
    print("Starting up...")
    init_db()
    
    # Start background task for cleaning up expired statements
    cleanup_task = asyncio.create_task(periodic_cleanup())
    
    yield
    
    # Shutdown
    print("Shutting down...")
    cleanup_task.cancel()
    try:
        await cleanup_task
    except asyncio.CancelledError:
        pass


# Create FastAPI app
app = FastAPI(
    title="Bank Statement Converter API",
    description="API for converting bank statement PDFs to CSV format",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8000", 
        "http://localhost:8080", 
        "http://127.0.0.1:8000", 
        "http://127.0.0.1:8080", 
        "http://localhost:5000", 
        "http://127.0.0.1:5000",
        "https://bankcsvconverter.com",
        "https://www.bankcsvconverter.com"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=3600,
)

# Add CSRF protection middleware
app.add_middleware(CSRFMiddleware)


async def periodic_cleanup():
    """Periodically clean up expired statements."""
    while True:
        try:
            await asyncio.sleep(3600)  # Run every hour
            cleanup_expired_statements()
        except asyncio.CancelledError:
            break
        except Exception as e:
            print(f"Error in cleanup task: {e}")


# Include routers
app.include_router(auth_router)  # Legacy JWT auth at /api/auth
app.include_router(auth_cookie_router, prefix="/v2")  # Cookie auth at /v2/api/auth
# app.include_router(auth_verify_router)  # Auth verification endpoints - module not found
app.include_router(oauth_router)
app.include_router(statements_router)
app.include_router(feedback_router)
app.include_router(split_statement_router)
app.include_router(analyze_transactions_router)
app.include_router(stripe_router)
# app.include_router(user_statistics_router)  # User statistics endpoints - module not found
# app.include_router(statements_recent_router)  # Recent statements endpoints - module not found
# app.include_router(statement_delete_router)  # Statement deletion endpoints - module not found

# User data export
try:
    from api.user_export import router as user_export_router
    app.include_router(user_export_router)
except ImportError as e:
    print(f"User export module error: {e}")

# User settings - simplified version without email
try:
    from api.user_settings_simple import router as user_settings_simple_router
    app.include_router(user_settings_simple_router)
    print("User settings endpoints loaded successfully")
except ImportError as e:
    print(f"User settings simple module error: {e}")

# Login sessions tracking
try:
    from api.login_sessions import router as login_sessions_router
    app.include_router(login_sessions_router)
    print("Login sessions endpoints loaded successfully")
except ImportError as e:
    print(f"Login sessions module error: {e}")


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Bank Statement Converter API",
        "version": "1.0.0",
        "endpoints": {
            "auth": "/api/auth",
            "statements": "/api",
            "feedback": "/api/feedback"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat()
    }


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler."""
    return JSONResponse(
        status_code=500,
        content={
            "detail": "An unexpected error occurred",
            "type": type(exc).__name__
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=5000,
        reload=True
    )