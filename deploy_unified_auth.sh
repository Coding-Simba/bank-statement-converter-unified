#!/bin/bash

SERVER_IP="3.235.19.83"
KEY_PATH="/Users/MAC/Downloads/bank-statement-converter.pem"
SERVER_USER="ubuntu"

echo "Deploying Unified Authentication System"
echo "======================================"

# Step 1: Deploy backend changes
echo "1. Deploying backend updates..."

# Copy updated auth files
scp -i "$KEY_PATH" backend/api/auth_cookie.py "$SERVER_USER@$SERVER_IP:/home/ubuntu/bank-statement-converter/backend/api/"
scp -i "$KEY_PATH" backend/models/session.py "$SERVER_USER@$SERVER_IP:/home/ubuntu/bank-statement-converter/backend/models/"
scp -i "$KEY_PATH" backend/models/database.py "$SERVER_USER@$SERVER_IP:/home/ubuntu/bank-statement-converter/backend/models/"
scp -i "$KEY_PATH" backend/migrations/add_sessions_table.py "$SERVER_USER@$SERVER_IP:/home/ubuntu/bank-statement-converter/backend/migrations/"

# Step 2: Run database migrations
echo "2. Running database migrations..."
ssh -i "$KEY_PATH" "$SERVER_USER@$SERVER_IP" << 'EOF'
cd /home/ubuntu/bank-statement-converter/backend
source venv/bin/activate

# Run sessions table migration
python3 migrations/add_sessions_table.py

# Import Session model in database.py __init__
cat >> models/__init__.py << 'PYTHON'
from .session import Session
PYTHON

echo "Database migrations completed"
EOF

# Step 3: Update backend main.py to use v2 auth
echo "3. Updating backend routes..."
ssh -i "$KEY_PATH" "$SERVER_USER@$SERVER_IP" << 'EOF'
cd /home/ubuntu/bank-statement-converter/backend

# Update main.py to include auth_cookie router with /v2 prefix
python3 << 'PYTHON'
import re

with open('main.py', 'r') as f:
    content = f.read()

# Add import if not exists
if 'from api.auth_cookie import router as auth_cookie_router' not in content:
    auth_import_line = 'from api.auth import router as auth_router'
    content = content.replace(
        auth_import_line,
        f'from api.auth_cookie import router as auth_cookie_router\n{auth_import_line}'
    )

# Add router with v2 prefix if not exists
if 'app.include_router(auth_cookie_router' not in content:
    auth_router_line = 'app.include_router(auth_router)'
    if auth_router_line in content:
        content = content.replace(
            auth_router_line,
            f'{auth_router_line}\napp.include_router(auth_cookie_router, prefix="/v2")'
        )

with open('main.py', 'w') as f:
    f.write(content)

print("Backend routes updated")
PYTHON

EOF

# Step 4: Deploy frontend auth script
echo "4. Deploying unified auth script..."
scp -i "$KEY_PATH" js/auth-unified.js "$SERVER_USER@$SERVER_IP:/home/ubuntu/bank-statement-converter/frontend/js/"

# Step 5: Clean up old auth scripts and update HTML files
echo "5. Cleaning up old auth scripts..."
ssh -i "$KEY_PATH" "$SERVER_USER@$SERVER_IP" << 'EOF'
cd /home/ubuntu/bank-statement-converter/frontend

# Create Python script to update all HTML files
cat > update_auth_scripts.py << 'PYTHON'
import os
import re
import glob

# List of old auth scripts to remove
OLD_AUTH_SCRIPTS = [
    'auth.js', 'auth-fixed.js', 'auth-persistent.js', 'auth-universal.js',
    'auth-global.js', 'debug-auth.js', 'auth-login-fix.js', 'auth-redirect-fix.js',
    'force-auth-storage.js', 'login-override-final.js', 'login-redirect-handler.js',
    'auth-service.js', 'login-cookie-auth.js', 'stripe-cookie-auth.js',
    'stripe-complete-fix.js', 'stripe-buy-fix.js', 'stripe-integration-fixed.js',
    'stripe-simple-fix.js', 'stripe-auth-fix.js', 'simple_stripe_handler.js'
]

def update_html_file(filepath):
    with open(filepath, 'r') as f:
        content = f.read()
    
    original_content = content
    
    # Remove all old script tags
    for script in OLD_AUTH_SCRIPTS:
        pattern = f'<script[^>]*src=["\'][^"\']*{script}["\'][^>]*></script>\s*\n?'
        content = re.sub(pattern, '', content, flags=re.IGNORECASE)
    
    # Check if auth-unified.js is already included
    if 'auth-unified.js' not in content:
        # Add auth-unified.js after </title> or before </head>
        if '</title>' in content:
            content = content.replace('</title>', '</title>\n    <script src="/js/auth-unified.js"></script>')
        elif '</head>' in content:
            content = content.replace('</head>', '    <script src="/js/auth-unified.js"></script>\n</head>')
    
    # Only write if content changed
    if content != original_content:
        with open(filepath, 'w') as f:
            f.write(content)
        print(f"Updated: {filepath}")
    else:
        print(f"No changes: {filepath}")

# Update all HTML files
for html_file in glob.glob('*.html'):
    update_html_file(html_file)

print("\nAll HTML files updated")
PYTHON

python3 update_auth_scripts.py
rm update_auth_scripts.py

# Show what's loaded on key pages
echo -e "\nVerifying auth scripts on key pages:"
echo "Login page scripts:"
grep -E "script.*src.*js" login.html | grep -E "(auth|login)" || echo "No auth scripts found"
echo -e "\nPricing page scripts:"
grep -E "script.*src.*js" pricing.html | grep -E "(auth|stripe)" || echo "No auth scripts found"

EOF

# Step 6: Update nginx configuration for v2 routes
echo "6. Updating nginx configuration..."
ssh -i "$KEY_PATH" "$SERVER_USER@$SERVER_IP" << 'EOF'
# Add v2 location block to nginx config
sudo tee -a /etc/nginx/sites-available/bank-converter << 'NGINX'

    # V2 API routes for cookie auth
    location /v2/ {
        proxy_pass http://localhost:5000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        
        # Important for cookies
        proxy_set_header Cookie $http_cookie;
        proxy_pass_header Set-Cookie;
    }
NGINX

# Test nginx config
sudo nginx -t

# Reload nginx
sudo systemctl reload nginx

echo "Nginx configuration updated"
EOF

# Step 7: Restart backend
echo "7. Restarting backend service..."
ssh -i "$KEY_PATH" "$SERVER_USER@$SERVER_IP" << 'EOF'
cd /home/ubuntu/bank-statement-converter/backend
pkill -f "uvicorn main:app" || true
sleep 2
nohup uvicorn main:app --host 0.0.0.0 --port 5000 > server.log 2>&1 &
echo "Backend restarted"
EOF

echo -e "\n✅ Unified Authentication System Deployed!"
echo "=========================================="
echo "Key features implemented:"
echo "1. HTTP-only cookies for JWT storage"
echo "2. Remember Me functionality (90 days vs 24 hours)"
echo "3. Session tracking with device info"
echo "4. Automatic token refresh every 10 minutes"
echo "5. Single unified auth script"
echo "6. Cookie domain set to .bankcsvconverter.com"
echo ""
echo "Test the new system:"
echo "1. Visit https://bankcsvconverter.com/login.html"
echo "2. Check 'Remember Me' checkbox"
echo "3. Login and verify persistence across pages"
echo "4. Check console for [UnifiedAuth] messages"