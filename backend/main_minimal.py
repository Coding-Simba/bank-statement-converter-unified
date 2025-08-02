"""Minimal FastAPI application for the bank statement converter backend."""

# Load environment variables first
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os

# Import only available routers
from api.auth import router as auth_router
from api.auth_cookie import router as auth_cookie_router
from api.statements import router as statements_router
from api.feedback import router as feedback_router
from api.oauth import router as oauth_router
from api.split_statement import router as split_statement_router
from api.analyze_transactions import router as analyze_transactions_router
from api.stripe_payments import router as stripe_router
from models.database import init_db

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan events."""
    # Startup
    print("Starting up...")
    init_db()
    yield
    # Shutdown
    print("Shutting down...")

# Create FastAPI app
app = FastAPI(
    title="Bank Statement Converter API",
    description="Convert bank statement PDFs to CSV/Excel format",
    version="2.0.0",
    lifespan=lifespan
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173", 
        "https://bankcsvconverter.com",
        "https://www.bankcsvconverter.com"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router)  # Legacy JWT auth at /api/auth
app.include_router(auth_cookie_router, prefix="/v2")  # Cookie auth at /v2/api/auth
app.include_router(oauth_router)
app.include_router(statements_router)
app.include_router(feedback_router)
app.include_router(split_statement_router)
app.include_router(analyze_transactions_router)
app.include_router(stripe_router)

@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Bank Statement Converter API",
        "version": "2.0.0",
        "docs": "/docs",
        "health": "/health"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)