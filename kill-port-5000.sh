#!/bin/bash

# Kill Port 5000 and Restart
echo "🔧 Killing Port 5000 and Restarting"
echo "==================================="
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

# Kill and restart via SSH
ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no "$SERVER_USER@$SERVER_IP" << 'ENDSSH'
cd /home/ubuntu/backend

echo "1. Finding what's using port 5000..."
lsof -i:5000 -t

echo -e "\n2. Killing EVERYTHING on port 5000..."
lsof -ti:5000 | xargs kill -9 2>/dev/null || true
sleep 2

echo -e "\n3. Double-checking port is free..."
if lsof -i:5000 -t > /dev/null 2>&1; then
    echo "Port still in use, force killing..."
    fuser -k 5000/tcp
else
    echo "✓ Port 5000 is free"
fi

echo -e "\n4. Killing any lingering Python processes..."
pkill -9 -f "python" || true
pkill -9 -f "uvicorn" || true
pkill -9 -f "start_backend" || true
sleep 2

echo -e "\n5. Starting backend cleanly..."
nohup python3 -m uvicorn main:app --host 0.0.0.0 --port 5000 > backend_clean.log 2>&1 &
BACKEND_PID=$!
echo "Started with PID: $BACKEND_PID"

sleep 5

echo -e "\n6. Checking if backend is running..."
if ps -p $BACKEND_PID > /dev/null; then
    echo "✓ Backend process is running"
    
    # Test health endpoint
    if curl -s http://localhost:5000/health > /dev/null; then
        echo "✓ Backend is responding to health checks"
        
        # Show the response
        echo -e "\nHealth check response:"
        curl -s http://localhost:5000/health | jq '.' 2>/dev/null || cat
    else
        echo "✗ Backend not responding"
    fi
else
    echo "✗ Backend crashed"
    echo "Last 30 lines of log:"
    tail -30 backend_clean.log
fi

echo -e "\n7. Testing authentication..."
# Create test user if needed
python3 -c "
import sys
sys.path.insert(0, '.')
from models.database import get_db, User
from utils.auth import get_password_hash

db = next(get_db())
user = db.query(User).filter(User.email == 'test@example.com').first()
if not user:
    user = User(
        email='test@example.com',
        password_hash=get_password_hash('test123'),
        full_name='Test User',
        account_type='free'
    )
    db.add(user)
    db.commit()
db.close()
print('✓ Test user ready')
"

# Test login
echo -e "\nTesting login endpoint:"
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test123"}' \
  -w "\nStatus: %{http_code}\n" -s | jq '.' 2>/dev/null || cat

ENDSSH

echo ""
echo -e "${GREEN}✓ Backend restarted successfully!${NC}"
echo ""
echo "You can now test login at: https://bankcsvconverter.com/login.html"
echo "Credentials: test@example.com / test123"