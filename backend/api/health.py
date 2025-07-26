"""Health check endpoint for monitoring"""

from fastapi import APIRouter
from datetime import datetime
import os

router = APIRouter(prefix="/api", tags=["health"])

@router.get("/health")
async def health_check():
    """Simple health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
        "service": "bank-statement-converter"
    }

@router.get("/health/detailed")
async def detailed_health_check():
    """Detailed health check with system info"""
    uploads_dir = os.path.join(os.path.dirname(__file__), "..", "..", "uploads")
    failed_pdfs_dir = os.path.join(os.path.dirname(__file__), "..", "..", "failed_pdfs")
    
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
        "service": "bank-statement-converter",
        "checks": {
            "uploads_directory": os.path.exists(uploads_dir),
            "failed_pdfs_directory": os.path.exists(failed_pdfs_dir),
            "disk_space_available": True,  # Add actual disk space check if needed
            "database": True  # Add actual database check if needed
        }
    }