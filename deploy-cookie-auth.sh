#!/bin/bash

# 🔐 DEPLOY SECURE COOKIE-BASED AUTH
echo "🔐 DEPLOYING SECURE COOKIE-BASED AUTHENTICATION"
echo "=============================================="
echo ""

SERVER_IP="3.235.19.83"
SERVER_USER="ubuntu"
SSH_KEY="/Users/MAC/Downloads/bank-statement-converter.pem"

# First backup and update backend
echo "1. Updating backend authentication..."
ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no "$SERVER_USER@$SERVER_IP" << 'ENDSSH'
cd /home/ubuntu/backend

# Backup current auth.py
cp api/auth.py api/auth.py.backup.$(date +%s)

# Update auth.py with cookie-based implementation
cat > api/auth_cookie.py << 'EOF'
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import secrets
import bcrypt
import jwt
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr

from ..database import get_db
from ..models import User
from ..config import settings

router = APIRouter(prefix="/api/auth", tags=["authentication"])

# Cookie configuration
COOKIE_NAME = "auth_token"
COOKIE_SECURE = True  # Always use secure cookies with HTTPS
COOKIE_HTTPONLY = True  # Prevent JavaScript access
COOKIE_SAMESITE = "lax"  # CSRF protection
COOKIE_MAX_AGE = 30 * 24 * 60 * 60  # 30 days for remember me
COOKIE_MAX_AGE_SHORT = 24 * 60 * 60  # 24 hours for regular login

class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    remember_me: bool = False

class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
    password: str

def create_access_token(user_id: int, email: str) -> str:
    """Create JWT token for user"""
    expire = datetime.utcnow() + timedelta(days=30)
    payload = {
        "sub": str(user_id),
        "email": email,
        "exp": expire,
        "iat": datetime.utcnow()
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")

def verify_token(token: str) -> Optional[Dict[str, Any]]:
    """Verify and decode JWT token"""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        return payload
    except jwt.ExpiredTokenError:
        return None
    except jwt.InvalidTokenError:
        return None

def get_current_user_from_cookie(request: Request, db: Session = Depends(get_db)) -> Optional[User]:
    """Get current user from auth cookie"""
    token = request.cookies.get(COOKIE_NAME)
    
    if not token:
        return None
    
    payload = verify_token(token)
    if not payload:
        return None
    
    user = db.query(User).filter(User.id == int(payload["sub"])).first()
    return user

def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    """Get current user or raise 401"""
    user = get_current_user_from_cookie(request, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    return user

@router.post("/register")
async def register(
    request: RegisterRequest,
    response: Response,
    db: Session = Depends(get_db)
):
    """Register new user with secure cookie auth"""
    # Check if user exists
    existing_user = db.query(User).filter(User.email == request.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Hash password
    hashed_password = bcrypt.hashpw(request.password.encode('utf-8'), bcrypt.gensalt())
    
    # Create user
    user = User(
        name=request.name,
        email=request.email,
        password_hash=hashed_password.decode('utf-8')
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    # Create token
    token = create_access_token(user.id, user.email)
    
    # Set secure cookie
    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        max_age=COOKIE_MAX_AGE,
        secure=COOKIE_SECURE,
        httponly=COOKIE_HTTPONLY,
        samesite=COOKIE_SAMESITE,
        path="/"
    )
    
    return {
        "message": "Registration successful",
        "user": {
            "id": user.id,
            "email": user.email,
            "name": user.name
        }
    }

@router.post("/login")
async def login(
    request: LoginRequest,
    response: Response,
    db: Session = Depends(get_db)
):
    """Login with secure cookie auth"""
    # Find user
    user = db.query(User).filter(User.email == request.email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    # Verify password
    if not bcrypt.checkpw(request.password.encode('utf-8'), user.password_hash.encode('utf-8')):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    # Create token
    token = create_access_token(user.id, user.email)
    
    # Set secure cookie
    max_age = COOKIE_MAX_AGE if request.remember_me else COOKIE_MAX_AGE_SHORT
    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        max_age=max_age,
        secure=COOKIE_SECURE,
        httponly=COOKIE_HTTPONLY,
        samesite=COOKIE_SAMESITE,
        path="/"
    )
    
    return {
        "message": "Login successful",
        "user": {
            "id": user.id,
            "email": user.email,
            "name": user.name
        }
    }

@router.post("/logout")
async def logout(response: Response):
    """Logout by clearing cookie"""
    response.delete_cookie(
        key=COOKIE_NAME,
        secure=COOKIE_SECURE,
        httponly=COOKIE_HTTPONLY,
        samesite=COOKIE_SAMESITE,
        path="/"
    )
    return {"message": "Logged out successfully"}

@router.get("/check")
async def check_auth(request: Request, db: Session = Depends(get_db)):
    """Check if user is authenticated"""
    user = get_current_user_from_cookie(request, db)
    
    if user:
        return {
            "authenticated": True,
            "user": {
                "id": user.id,
                "email": user.email,
                "name": user.name
            }
        }
    
    return {"authenticated": False}

@router.get("/me")
async def get_me(current_user: User = Depends(get_current_user)):
    """Get current user info"""
    return {
        "id": current_user.id,
        "email": current_user.email,
        "name": current_user.name
    }

# CSRF Token endpoint (optional but recommended)
@router.get("/csrf")
async def get_csrf_token(response: Response):
    """Generate CSRF token"""
    csrf_token = secrets.token_urlsafe(32)
    response.set_cookie(
        key="csrf_token",
        value=csrf_token,
        secure=COOKIE_SECURE,
        httponly=False,  # JavaScript needs to read this
        samesite=COOKIE_SAMESITE,
        path="/"
    )
    return {"csrf_token": csrf_token}
EOF

# Import the new get_current_user for other modules
echo "
# Export the cookie-based auth dependency
from .auth_cookie import get_current_user, get_current_user_from_cookie
" >> api/auth_cookie.py

# Update main.py to use the new auth
sed -i 's/from api.auth import router as auth_router/from api.auth_cookie import router as auth_router/' main.py 2>/dev/null || \
sed -i 's/from \.api\.auth import router as auth_router/from .api.auth_cookie import router as auth_router/' main.py

# Update stripe.py to use new auth
sed -i 's/from \.auth import get_current_user/from .auth_cookie import get_current_user/' api/stripe.py 2>/dev/null || true

# Restart backend
pkill -f uvicorn
sleep 2
cd /home/ubuntu/backend
nohup python3 -m uvicorn main:app --host 0.0.0.0 --port 5000 > backend.log 2>&1 &
sleep 3

echo "✅ Backend updated with cookie-based auth"
ENDSSH

# Upload new frontend auth
echo -e "\n2. Uploading cookie-based auth frontend..."
scp -i "$SSH_KEY" -o StrictHostKeyChecking=no \
    /Users/MAC/chrome/bank-statement-converter-unified/js/auth-cookie-based.js \
    "$SERVER_USER@$SERVER_IP:/home/ubuntu/bank-statement-converter/js/"

# Update all HTML files
echo -e "\n3. Updating all pages to use cookie auth..."
ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no "$SERVER_USER@$SERVER_IP" << 'ENDSSH'
cd /home/ubuntu/bank-statement-converter

# Update all HTML files
HTML_FILES=(
    "index.html"
    "login.html"
    "signup.html"
    "dashboard-modern.html"
    "settings.html"
    "pricing.html"
    "convert-pdf.html"
    "merge-statements.html"
    "split-by-date.html"
    "analyze-transactions.html"
    "blog.html"
    "business.html"
)

for file in "${HTML_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "Updating $file..."
        # Remove old auth scripts
        sed -i '/<script.*auth.*\.js.*<\/script>/d' "$file"
        # Add cookie-based auth
        sed -i '/<\/body>/i <script src="/js/auth-cookie-based.js"></script>' "$file"
    fi
done

# Create test page
cat > cookie-auth-test.html << 'EOF'
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Cookie Auth Test</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    <style>
        body { font-family: Arial; padding: 40px; background: #f5f5f5; }
        .container { max-width: 800px; margin: 0 auto; background: white; padding: 40px; border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.1); }
        .status { margin: 20px 0; padding: 20px; background: #f8f9fa; border-radius: 8px; }
        .success { color: #22c55e; }
        .error { color: #ef4444; }
        button { background: #4a90e2; color: white; border: none; padding: 12px 24px; border-radius: 6px; cursor: pointer; margin: 5px; }
        button:hover { background: #357abd; }
        pre { background: #f1f5f9; padding: 12px; border-radius: 6px; overflow-x: auto; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🔐 Cookie-Based Auth Test</h1>
        
        <div class="status">
            <h3>Current Status</h3>
            <p>Authenticated: <span id="authStatus">Checking...</span></p>
            <p>User: <span id="userInfo">-</span></p>
            <p>Cookie Present: <span id="cookieStatus">-</span></p>
        </div>
        
        <div class="actions">
            <h3>Test Actions</h3>
            <button onclick="checkAuth()">Check Auth</button>
            <button onclick="testLogin()">Login Test User</button>
            <button onclick="testLogout()">Logout</button>
            <button onclick="testNavigation()">Test Navigation</button>
        </div>
        
        <div class="results">
            <h3>Results</h3>
            <pre id="results">Ready for testing...</pre>
        </div>
    </div>
    
    <script src="/js/auth-cookie-based.js"></script>
    <script>
        function log(msg, type = 'info') {
            const results = document.getElementById('results');
            const time = new Date().toLocaleTimeString();
            results.textContent += `\n[${time}] ${msg}`;
        }
        
        async function checkAuth() {
            log('Checking authentication...');
            const response = await fetch('/api/auth/check', {
                credentials: 'include'
            });
            const data = await response.json();
            
            document.getElementById('authStatus').textContent = data.authenticated ? 'Yes ✅' : 'No ❌';
            document.getElementById('authStatus').className = data.authenticated ? 'success' : 'error';
            document.getElementById('userInfo').textContent = data.user ? data.user.email : '-';
            
            // Check for auth cookie
            const hasCookie = document.cookie.includes('auth_token');
            document.getElementById('cookieStatus').textContent = hasCookie ? 'Yes (HTTP-only)' : 'No';
            
            log(`Auth check: ${data.authenticated ? 'Authenticated' : 'Not authenticated'}`);
        }
        
        async function testLogin() {
            log('Attempting login...');
            const response = await fetch('/api/auth/login', {
                method: 'POST',
                credentials: 'include',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    email: 'test@example.com',
                    password: 'test123',
                    remember_me: true
                })
            });
            
            const data = await response.json();
            log(response.ok ? 'Login successful!' : `Login failed: ${data.detail}`);
            
            if (response.ok) {
                await checkAuth();
            }
        }
        
        async function testLogout() {
            log('Logging out...');
            await window.CookieAuth.logout();
        }
        
        function testNavigation() {
            log('Opening pages to test persistence...');
            window.open('/', '_blank');
            window.open('/pricing.html', '_blank');
            window.open('/dashboard-modern.html', '_blank');
            log('Check if you stay logged in across all pages');
        }
        
        // Listen for auth ready
        window.addEventListener('cookie-auth-ready', (e) => {
            log('Cookie Auth System Ready!');
            checkAuth();
        });
        
        // Initial check
        setTimeout(checkAuth, 500);
    </script>
</body>
</html>
EOF

echo -e "\n✅ COOKIE-BASED AUTH DEPLOYED!"
ENDSSH

echo ""
echo "🔐 SECURE COOKIE AUTHENTICATION DEPLOYED!"
echo "========================================"
echo ""
echo "The new system:"
echo "✅ Uses HTTP-only secure cookies (like Google/Facebook)"
echo "✅ No client-side token storage"
echo "✅ Automatic auth persistence across all pages"
echo "✅ CSRF protection with SameSite=lax"
echo "✅ Secure flag for HTTPS only"
echo ""
echo "Test it at:"
echo "https://bankcsvconverter.com/cookie-auth-test.html"