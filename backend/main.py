"""Main FastAPI application for the bank statement converter backend."""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import os
from datetime import datetime
import asyncio

# Import routers
from .api import auth, statements, feedback
from .models.database import init_db, engine, Base
from .utils.cleanup import cleanup_expired_statements

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
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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
app.include_router(auth.router)
app.include_router(statements.router)
app.include_router(feedback.router)


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
        "backend.main:app",
        host="0.0.0.0",
        port=5000,
        reload=True
    )