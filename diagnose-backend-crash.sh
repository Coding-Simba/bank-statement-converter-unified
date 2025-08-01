#!/bin/bash

# Diagnose Backend Crash
echo "🔍 Diagnosing Backend Crash"
echo "==========================="
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

# Diagnose via SSH
ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no "$SERVER_USER@$SERVER_IP" << 'ENDSSH'
cd /home/ubuntu/backend

echo "1. Clearing log and starting fresh..."
> backend.log

echo -e "\n2. Starting backend with detailed error output..."
python3 -m uvicorn main:app --host 0.0.0.0 --port 5000 2>&1 | head -50 &
BACKEND_PID=$!

sleep 3

echo -e "\n3. Checking what went wrong..."
if ! ps -p $BACKEND_PID > /dev/null 2>&1; then
    echo "Backend crashed immediately. Error output:"
    cat backend.log
fi

echo -e "\n4. Checking Python imports directly..."
python3 -c "
import sys
print('Python path:', sys.path)
try:
    from main import app
    print('✓ Main app imported successfully')
except Exception as e:
    print(f'✗ Import error: {e}')
"

echo -e "\n5. Checking for missing dependencies..."
python3 -c "
required_modules = [
    'fastapi', 'uvicorn', 'sqlalchemy', 'jwt', 'passlib',
    'python-multipart', 'python-jose', 'bcrypt', 'aiosmtplib'
]
for module in required_modules:
    try:
        __import__(module)
        print(f'✓ {module} is installed')
    except ImportError:
        print(f'✗ {module} is NOT installed')
"

echo -e "\n6. Looking for syntax errors..."
python3 -m py_compile main.py 2>&1
python3 -m py_compile api/auth.py 2>&1
python3 -m py_compile models/database.py 2>&1

echo -e "\n7. Checking if there's already something on port 5000..."
lsof -i:5000 | head -5

echo -e "\n8. Trying to run backend directly..."
python3 main.py 2>&1 | head -20

ENDSSH

echo ""
echo -e "${GREEN}✓ Diagnosis complete!${NC}"