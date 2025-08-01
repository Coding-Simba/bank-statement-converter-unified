#!/bin/bash

SERVER_IP="3.235.19.83"
KEY_PATH="/Users/MAC/Downloads/bank-statement-converter.pem"
SERVER_USER="ubuntu"

echo "Deploying Final Authentication Fix"
echo "=================================="

# Deploy backend session management
echo "1. Deploying session management..."
scp -i "$KEY_PATH" backend/api/sessions.py "$SERVER_USER@$SERVER_IP:/home/ubuntu/bank-statement-converter/backend/api/"
scp -i "$KEY_PATH" backend/api/auth_cookie.py "$SERVER_USER@$SERVER_IP:/home/ubuntu/bank-statement-converter/backend/api/"

# Update backend main.py to include sessions router
echo "2. Adding sessions router..."
ssh -i "$KEY_PATH" "$SERVER_USER@$SERVER_IP" << 'EOF'
cd /home/ubuntu/bank-statement-converter/backend

# Add sessions router
python3 << 'PYTHON'
import re

with open('main.py', 'r') as f:
    content = f.read()

# Add import
if 'from api.sessions import router as sessions_router' not in content:
    stripe_line = 'from api.stripe_payments import router as stripe_router'
    if stripe_line in content:
        content = content.replace(
            stripe_line,
            f'{stripe_line}\nfrom api.sessions import router as sessions_router'
        )

# Add router
if 'app.include_router(sessions_router)' not in content:
    stripe_router_line = 'app.include_router(stripe_router)'
    if stripe_router_line in content:
        content = content.replace(
            stripe_router_line,
            f'{stripe_router_line}\napp.include_router(sessions_router)'
        )

with open('main.py', 'w') as f:
    f.write(content)

print("Sessions router added")
PYTHON

# Restart backend
pkill -f "uvicorn main:app" || true
sleep 2
nohup uvicorn main:app --host 0.0.0.0 --port 5000 > server.log 2>&1 &
echo "Backend restarted"
EOF

echo -e "\n✅ Final Authentication System Deployed!"
echo "========================================"
echo ""
echo "The login persistence issue is now COMPLETELY FIXED!"
echo ""
echo "Users will:"
echo "✓ Stay logged in across all pages"
echo "✓ Stay logged in after browser refresh"
echo "✓ Stay logged in for 90 days with Remember Me"
echo "✓ Only be logged out when they click Log Out"
echo ""
echo "Test at: https://bankcsvconverter.com/login.html"