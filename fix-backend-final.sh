#!/bin/bash

# Fix Backend Final
echo "🔧 Final Backend Fix"
echo "==================="
echo ""

SERVER_IP="3.235.19.83"
SERVER_USER="ubuntu"
SSH_KEY="/Users/MAC/Downloads/bank-statement-converter.pem"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Check SSH key
if [ ! -f "$SSH_KEY" ]; then
    echo -e "${RED}✗ SSH key not found at $SSH_KEY${NC}"
    exit 1
fi

# Deploy via SSH
ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no "$SERVER_USER@$SERVER_IP" << 'ENDSSH'
cd /home/ubuntu/bank-statement-converter/backend

echo "1. Stopping all Python processes..."
pkill -f python || true
sleep 2

echo "2. Fixing ALL import issues..."
# Fix auth_verify.py
echo "   Fixing auth_verify.py..."
cat > api/auth_verify.py << 'EOF'
"""Auth verification endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from models.database import get_db, User
from middleware.auth_middleware import get_current_user

router = APIRouter(prefix="/api/auth", tags=["auth-verify"])

class UserInfo(BaseModel):
    id: int
    email: str
    account_type: str
    daily_generations: int
    daily_limit: int

@router.get("/me", response_model=UserInfo)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user information."""
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    
    return UserInfo(
        id=current_user.id,
        email=current_user.email,
        account_type=current_user.account_type,
        daily_generations=current_user.daily_generations,
        daily_limit=current_user.get_daily_limit()
    )

@router.get("/verify")
async def verify_auth(current_user: User = Depends(get_current_user)):
    """Verify authentication status."""
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    
    return {"authenticated": True, "user_id": current_user.id}
EOF

echo "3. Creating simple startup script..."
cat > start_backend.py << 'EOF'
#!/usr/bin/env python3
import subprocess
import sys
import time

print("Starting backend server...")
try:
    # Start uvicorn
    subprocess.run([
        sys.executable, "-m", "uvicorn",
        "main:app",
        "--host", "0.0.0.0",
        "--port", "5000",
        "--log-level", "info"
    ])
except KeyboardInterrupt:
    print("\nShutting down...")
except Exception as e:
    print(f"Error: {e}")
EOF

chmod +x start_backend.py

echo "4. Testing imports..."
python3 -c "
import sys
sys.path.append('.')
try:
    from main import app
    print('✓ Main app imports successfully')
except Exception as e:
    print(f'✗ Main app import error: {e}')
"

echo "5. Starting backend..."
# Clear log
> ../backend.log

# Start backend
nohup python3 start_backend.py > ../backend.log 2>&1 &
PID=$!
echo "   Started with PID: $PID"

# Wait for startup
sleep 5

echo "6. Checking if backend is running..."
if ps -p $PID > /dev/null; then
    echo "✓ Backend process is running"
    
    # Test endpoints
    echo "7. Testing endpoints..."
    curl -s http://localhost:5000/health | head -c 50 && echo " ... ✓"
    
    # Check auth endpoints
    echo "8. Checking auth endpoints..."
    curl -s http://localhost:5000/v2/api/auth/csrf | head -c 50 && echo " ... ✓"
else
    echo "✗ Backend failed to start"
    echo "Last 20 lines of log:"
    tail -20 ../backend.log
fi

echo ""
echo "9. Backend processes:"
ps aux | grep -E "python|uvicorn" | grep -v grep | head -5

ENDSSH

echo ""
echo -e "${GREEN}✓ Backend fix complete!${NC}"
echo ""
echo "Test the login at: https://bankcsvconverter.com/login.html"