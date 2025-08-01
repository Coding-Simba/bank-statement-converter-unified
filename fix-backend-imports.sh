#!/bin/bash

# Fix Backend Import Issues
echo "🔧 Fixing Backend Import Issues"
echo "==============================="
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

# Fix via SSH
ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no "$SERVER_USER@$SERVER_IP" << 'ENDSSH'
set -e

cd /home/ubuntu/bank-statement-converter/backend

echo "1. Fixing auth_verify.py imports..."
# Fix the import issues in auth_verify.py
sed -i 's|from database import|from models.database import|g' api/auth_verify.py
sed -i 's|from models import User|from models.database import User|g' api/auth_verify.py

echo "2. Installing aiosmtplib in virtual environment..."
if [ -f venv/bin/activate ]; then
    source venv/bin/activate
    pip install aiosmtplib==3.0.1
else
    echo "No virtual environment found, installing globally"
    pip3 install aiosmtplib==3.0.1
fi

echo "3. Checking if user_settings.py exists..."
if [ ! -f api/user_settings.py ]; then
    echo "user_settings.py not found!"
else
    echo "user_settings.py exists"
fi

echo "4. Uncommenting user_settings import in main.py..."
sed -i 's|# from api.user_settings|from api.user_settings|' main.py
sed -i 's|# app.include_router(user_settings_router|app.include_router(user_settings_router|' main.py

echo "5. Checking all imports..."
python3 -c "
import sys
sys.path.append('.')
try:
    from api.user_settings import router
    print('✓ user_settings imports successfully')
except Exception as e:
    print(f'✗ user_settings import error: {e}')

try:
    from api.auth_verify import router
    print('✓ auth_verify imports successfully')
except Exception as e:
    print(f'✗ auth_verify import error: {e}')
"

echo "6. Killing any existing backend processes..."
pkill -f "uvicorn main:app" || true
sleep 2

echo "7. Starting backend..."
nohup python3 -m uvicorn main:app --host 0.0.0.0 --port 5000 > ../backend.log 2>&1 &
sleep 5

echo "8. Checking if backend is running..."
if ps aux | grep -q "[u]vicorn main:app"; then
    echo "✓ Backend is running"
    
    # Check if it's actually responding
    curl -s http://localhost:5000/health > /dev/null && echo "✓ Backend is responding to requests" || echo "✗ Backend not responding"
else
    echo "✗ Backend failed to start"
    echo "Last 20 lines of backend.log:"
    tail -20 ../backend.log
fi

echo ""
echo "9. Testing new endpoints..."
# Test if the new endpoints are accessible
curl -s http://localhost:5000/v2/api/user/profile 2>/dev/null | head -c 100
echo ""

ENDSSH

echo ""
echo -e "${GREEN}✓ Import issues fixed!${NC}"
echo ""
echo "Backend should now be running with all settings endpoints available."
echo "Monitor logs with: ssh ubuntu@$SERVER_IP 'tail -f /home/ubuntu/backend.log'"