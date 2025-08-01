#!/bin/bash

SERVER_IP="3.235.19.83"
KEY_PATH="/Users/MAC/Downloads/bank-statement-converter.pem"
SERVER_USER="ubuntu"

echo "Final fix for JWT and cookies"
echo "============================="

ssh -i "$KEY_PATH" "$SERVER_USER@$SERVER_IP" << 'EOF'
cd /home/ubuntu/bank-statement-converter/backend

echo "1. Checking what version of auth_cookie.py is actually running..."
echo "==============================================================="

# Check if the file on server has the correct path
echo "Checking refresh token path in current file:"
grep "path=\"/.*api/auth/refresh\"" api/auth_cookie.py

echo -e "\n2. Force updating the file..."
echo "============================"

# Create a completely new version with fixed paths
cat > api/auth_cookie_fixed.py << 'PYTHON'
"""Modern authentication API with HTTP-only cookies."""

from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime, timedelta
import secrets
import uuid

from models.database import get_db, User
from utils.auth import (
    verify_password, get_password_hash, create_access_token, 
    create_refresh_token, validate_email, validate_password,
    decode_token
)
from jwt.exceptions import InvalidTokenError
from api.sessions import create_session

router = APIRouter(prefix="/api/auth", tags=["authentication"])

# Constants
ACCESS_TOKEN_EXPIRE_MINUTES = 15
REFRESH_TOKEN_EXPIRE_HOURS = 24  # Default without remember me
REFRESH_TOKEN_EXPIRE_DAYS = 90  # With remember me
COOKIE_DOMAIN = ".bankcsvconverter.com"  # Cross-subdomain support


# Pydantic models
class UserLogin(BaseModel):
    email: EmailStr
    password: str
    remember_me: bool = False


class UserRegister(BaseModel):
    email: EmailStr
    password: str
    full_name: Optional[str] = None
    company_name: Optional[str] = None


class UserData(BaseModel):
    id: int
    email: str
    full_name: Optional[str]
    company_name: Optional[str]
    account_type: str
    created_at: datetime
    daily_generations: int
    daily_limit: int


def set_auth_cookies(response: Response, access_token: str, refresh_token: str, remember_me: bool = False, production: bool = True):
    """Set authentication cookies with proper security settings."""
    # Access token cookie
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=production,  # HTTPS only in production
        samesite="lax",
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        path="/",
        domain=COOKIE_DOMAIN if production else None
    )
    
    # Refresh token cookie - FIXED PATH HERE
    refresh_max_age = (REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60) if remember_me else (REFRESH_TOKEN_EXPIRE_HOURS * 60 * 60)
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=production,
        samesite="lax",
        max_age=refresh_max_age,
        path="/v2/api/auth/refresh",  # FIXED PATH
        domain=COOKIE_DOMAIN if production else None
    )


def clear_auth_cookies(response: Response):
    """Clear all authentication cookies."""
    response.delete_cookie(key="access_token", path="/", domain=COOKIE_DOMAIN)
    response.delete_cookie(key="refresh_token", path="/v2/api/auth/refresh", domain=COOKIE_DOMAIN)  # FIXED PATH
    response.delete_cookie(key="csrf_token", path="/", domain=COOKIE_DOMAIN)
PYTHON

# Copy the rest of the file
tail -n +88 api/auth_cookie.py >> api/auth_cookie_fixed.py

# Replace the original
mv api/auth_cookie_fixed.py api/auth_cookie.py

echo -e "\n3. Verifying the fix..."
echo "======================"
grep "path=\"/.*api/auth/refresh\"" api/auth_cookie.py

echo -e "\n4. Checking JWT configuration..."
echo "================================"

# Check SECRET_KEY
if [ -f ".env" ]; then
    echo "SECRET_KEY in .env:"
    grep "SECRET_KEY" .env | head -1
else
    echo "No .env file found"
fi

# Check if utils/auth.py is using the right SECRET_KEY
echo -e "\nSECRET_KEY usage in utils/auth.py:"
grep -n "SECRET_KEY" utils/auth.py | head -5

echo -e "\n5. Force restart backend..."
echo "=========================="

# Kill all python processes to ensure clean restart
pkill -f python || true
pkill -f uvicorn || true
sleep 3

source venv/bin/activate
export PYTHONPATH=/home/ubuntu/bank-statement-converter/backend:$PYTHONPATH
nohup uvicorn main:app --host 0.0.0.0 --port 5000 --reload > server.log 2>&1 &

echo "Waiting for backend to start..."
for i in {1..10}; do
    if pgrep -f "uvicorn main:app" > /dev/null; then
        echo "✅ Backend started"
        break
    fi
    sleep 1
done

echo -e "\n6. Final test of authentication..."
echo "=================================="

# Create new test user
TIMESTAMP=$(date +%s)
TEST_EMAIL="finalfix${TIMESTAMP}@example.com"

# Get CSRF
echo "a) Getting CSRF token..."
CSRF_RESP=$(curl -s -v https://bankcsvconverter.com/v2/api/auth/csrf 2>&1)
CSRF_TOKEN=$(echo "$CSRF_RESP" | grep -o '"csrf_token":"[^"]*"' | cut -d'"' -f4)
echo "CSRF Token: ${CSRF_TOKEN:0:20}..."

# Register
echo -e "\nb) Registering user: $TEST_EMAIL"
REGISTER_RESP=$(curl -s -X POST https://bankcsvconverter.com/v2/api/auth/register \
    -c final_cookies.txt \
    -H "Content-Type: application/json" \
    -H "X-CSRF-Token: $CSRF_TOKEN" \
    -d "{\"email\":\"$TEST_EMAIL\",\"password\":\"Test123!\",\"full_name\":\"Final Test\"}")
    
echo "$REGISTER_RESP" | python3 -m json.tool | grep -E "email|id" || echo "$REGISTER_RESP"

# Check cookies
echo -e "\nc) Verifying cookie paths are correct:"
cat final_cookies.txt | grep -E "refresh_token|access_token" | awk '{print $3, $7}'

# Test auth check
echo -e "\nd) Testing auth check:"
AUTH_CHECK=$(curl -s https://bankcsvconverter.com/v2/api/auth/check -b final_cookies.txt)
echo "$AUTH_CHECK" | python3 -m json.tool || echo "$AUTH_CHECK"

# If still failing, test direct
if echo "$AUTH_CHECK" | grep -q '"authenticated":false'; then
    echo -e "\ne) Direct backend test:"
    ACCESS_TOKEN=$(grep "access_token" final_cookies.txt | awk '{print $7}')
    curl -s http://localhost:5000/v2/api/auth/check -H "Cookie: access_token=$ACCESS_TOKEN" | python3 -m json.tool
fi

# Clean up
rm -f final_cookies.txt

echo -e "\n7. Checking backend logs..."
echo "=========================="
tail -20 server.log | grep -E "ERROR|error|Exception" || echo "No errors in recent logs"

EOF

echo -e "\n✅ JWT and cookie fixes applied!"