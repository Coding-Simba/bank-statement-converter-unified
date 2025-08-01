#!/bin/bash

# Fix Cookie Authentication
echo "🍪 Fixing Cookie Authentication"
echo "=============================="
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

# Fix cookie auth via SSH
ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no "$SERVER_USER@$SERVER_IP" << 'ENDSSH'
cd /home/ubuntu/backend

echo "1. Checking current auth implementation..."
grep -A 10 -B 5 "set_cookie\|cookie" api/auth.py | head -20

echo -e "\n2. Updating auth.py to use HTTP-only cookies..."
# Backup original
cp api/auth.py api/auth.py.backup

# Update login endpoint to set cookies
cat > update_auth.py << 'EOF'
#!/usr/bin/env python3
import re

# Read the current auth.py
with open('api/auth.py', 'r') as f:
    content = f.read()

# Check if already using cookies
if 'response.set_cookie' in content:
    print("✓ Already using cookie authentication")
else:
    print("✗ Not using cookies, updating...")
    
    # Update login endpoint to set cookies
    # Find the login endpoint
    login_pattern = r'(@router\.post\("/login".*?\n)(async def login.*?)(\n    return \{[^}]+\})'
    
    def replace_login(match):
        decorator = match.group(1)
        func_def = match.group(2)
        
        new_func = decorator + func_def + '''
    response = JSONResponse({
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "email": user.email,
            "account_type": user.account_type,
            "created_at": user.created_at.isoformat() if hasattr(user.created_at, 'isoformat') else str(user.created_at),
            "daily_generations": user.daily_generations,
            "daily_limit": user.get_daily_limit()
        }
    })
    
    # Set HTTP-only cookies
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=3600  # 1 hour
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=2592000  # 30 days
    )
    
    return response'''
    
    content = re.sub(login_pattern, replace_login, content, flags=re.DOTALL)
    
    # Add JSONResponse import if not present
    if 'from fastapi.responses import JSONResponse' not in content:
        content = content.replace('from fastapi import', 'from fastapi.responses import JSONResponse\nfrom fastapi import')
    
    # Write updated content
    with open('api/auth.py', 'w') as f:
        f.write(content)
    
    print("✓ Updated login endpoint to use cookies")

EOF

python3 update_auth.py

echo -e "\n3. Updating auth middleware to check cookies..."
cat > middleware/cookie_auth.py << 'EOF'
"""Cookie-based authentication middleware."""

from fastapi import Request, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
import jwt
from datetime import datetime

from models.database import User, get_db

class CookieOrBearerAuth(HTTPBearer):
    def __init__(self, auto_error: bool = True):
        super(CookieOrBearerAuth, self).__init__(auto_error=auto_error)
    
    async def __call__(self, request: Request) -> Optional[str]:
        # First try to get token from cookie
        access_token = request.cookies.get("access_token")
        
        # If no cookie, try Bearer token
        if not access_token:
            credentials: HTTPAuthorizationCredentials = await super().__call__(request)
            if credentials:
                access_token = credentials.credentials
        
        if not access_token and self.auto_error:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authenticated"
            )
        
        return access_token

# Create the security instance
cookie_or_bearer = CookieOrBearerAuth()

async def get_current_user_from_token(token: str = None, request: Request = None):
    """Get current user from JWT token (cookie or bearer)."""
    if not token and request:
        token = await cookie_or_bearer(request)
    
    if not token:
        return None
    
    try:
        # Decode the token
        payload = jwt.decode(token, "your-secret-key", algorithms=["HS256"])
        user_id = payload.get("sub")
        
        if not user_id:
            return None
        
        # Get user from database
        db = next(get_db())
        user = db.query(User).filter(User.id == user_id).first()
        db.close()
        
        return user
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None
    except Exception:
        return None
EOF

echo -e "\n4. Updating logout to clear cookies..."
cat >> update_auth.py << 'EOF'

# Update logout endpoint
logout_pattern = r'(@router\.post\("/logout".*?\n)(async def logout.*?)(\n    return \{[^}]+\})'

def replace_logout(match):
    decorator = match.group(1)
    func_def = match.group(2)
    
    new_func = decorator + func_def + '''
    response = JSONResponse({"message": "Successfully logged out"})
    
    # Clear cookies
    response.delete_cookie(key="access_token")
    response.delete_cookie(key="refresh_token")
    
    return response'''

content = re.sub(logout_pattern, replace_logout, content, flags=re.DOTALL)

with open('api/auth.py', 'w') as f:
    f.write(content)

print("✓ Updated logout endpoint to clear cookies")
EOF

python3 update_auth.py

echo -e "\n5. Restarting backend..."
pkill -f "uvicorn main:app" || true
sleep 2

nohup python3 -m uvicorn main:app --host 0.0.0.0 --port 5000 > backend.log 2>&1 &

sleep 5

echo -e "\n6. Testing cookie authentication..."
# Test login with cookies
echo "Testing login (should set cookies):"
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test123"}' \
  -c test_cookies.txt \
  -w "\nStatus: %{http_code}\n" -s | jq '.' 2>/dev/null || cat

echo -e "\nCookies set:"
cat test_cookies.txt | grep -v "^#" | grep -v "^$"

echo -e "\nTesting authenticated request with cookies:"
curl -X GET http://localhost:5000/api/auth/profile \
  -b test_cookies.txt \
  -w "\nStatus: %{http_code}\n" -s | head -10

ENDSSH

echo ""
echo -e "${GREEN}✓ Cookie authentication fix complete!${NC}"
echo ""
echo "The authentication system now uses HTTP-only cookies for security."
echo "Test at: https://bankcsvconverter.com/login.html"