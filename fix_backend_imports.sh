#!/bin/bash

# Fix Backend Import Issues on AWS Server

SERVER_IP="3.235.19.83"
KEY_PATH="/Users/MAC/Downloads/bank-statement-converter.pem"
SERVER_USER="ubuntu"

echo "Fixing Backend Import Issues on AWS Server"
echo "=========================================="

# SSH to server and fix imports
ssh -i "$KEY_PATH" "$SERVER_USER@$SERVER_IP" << 'EOF'
cd /home/ubuntu/bank-statement-converter-unified/backend

# 1. Fix main.py imports
echo "Fixing main.py imports..."
cat > main_fixed.py << 'MAINPY'
"""Main FastAPI application for the bank statement converter backend."""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import os
from datetime import datetime
import asyncio

# Import routers
from api.auth import router as auth_router
from api.statements import router as statements_router
from api.feedback import router as feedback_router
from api.oauth import router as oauth_router
from api.split_statement import router as split_statement_router
from api.analyze_transactions import router as analyze_transactions_router
from models.database import init_db, engine, Base
from utils.cleanup import cleanup_expired_statements

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
    allow_origins=["http://localhost:8080", "http://127.0.0.1:8080", "http://localhost:*", "*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=3600,
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
app.include_router(auth_router)
app.include_router(oauth_router)
app.include_router(statements_router)
app.include_router(feedback_router)
app.include_router(split_statement_router)
app.include_router(analyze_transactions_router)


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
MAINPY

mv main.py main_backup.py
mv main_fixed.py main.py

# 2. Create run_backend.py to handle proper imports
echo "Creating run_backend.py..."
cat > run_backend.py << 'RUNPY'
#!/usr/bin/env python3
import sys
import os

# Add parent directory to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Now run the main app
from backend.main import app

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=5000,
        log_level="info"
    )
RUNPY

chmod +x run_backend.py

# 3. Update systemd service file
echo "Updating systemd service..."
sudo tee /etc/systemd/system/bank-converter-backend.service << 'SERVICE'
[Unit]
Description=Bank Statement Converter Backend API
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/bank-statement-converter-unified
Environment="PYTHONPATH=/home/ubuntu/bank-statement-converter-unified"
Environment="PATH=/usr/local/bin:/usr/bin:/bin"
ExecStart=/usr/bin/python3 /home/ubuntu/bank-statement-converter-unified/backend/run_backend.py
Restart=always
RestartSec=10
StandardOutput=append:/home/ubuntu/backend.log
StandardError=append:/home/ubuntu/backend-error.log

# Memory limits
MemoryMax=600M
MemoryHigh=500M

[Install]
WantedBy=multi-user.target
SERVICE

# 4. Test the import fix
echo "Testing imports..."
cd /home/ubuntu/bank-statement-converter-unified
export PYTHONPATH=/home/ubuntu/bank-statement-converter-unified

# Test if imports work
python3 -c "from backend.api.auth import router; print('✅ Import successful')" || echo "❌ Import failed"

# 5. Reload and restart service
echo "Restarting backend service..."
sudo systemctl daemon-reload
sudo systemctl restart bank-converter-backend
sleep 5

# 6. Check service status
echo "Checking service status..."
sudo systemctl status bank-converter-backend --no-pager

# 7. Check if API is responding
echo "Testing API endpoint..."
curl -s http://localhost:5000/health | python3 -m json.tool || echo "API not responding yet"

# 8. Show recent logs
echo "Recent logs:"
tail -20 /home/ubuntu/backend-error.log 2>/dev/null || echo "No error logs"

EOF

echo "Fix applied. Checking final status..."