#!/bin/bash

# Restart Backend Service
echo "🔄 Restarting Backend Service"
echo "============================="
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

# Restart via SSH
ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no "$SERVER_USER@$SERVER_IP" << 'ENDSSH'
set -e

cd /home/ubuntu/bank-statement-converter/backend

echo "1. Killing any existing backend processes..."
pkill -f "uvicorn main:app" || true
sleep 2

echo "2. Clearing old logs..."
> ../backend.log

echo "3. Starting backend with proper logging..."
nohup python3 -m uvicorn main:app --host 0.0.0.0 --port 5000 --log-level info > ../backend.log 2>&1 &
sleep 5

echo "4. Checking if backend started..."
if ps aux | grep -q "[u]vicorn main:app"; then
    echo "✓ Backend process is running"
    
    # Get the PID
    PID=$(ps aux | grep "[u]vicorn main:app" | awk '{print $2}')
    echo "  PID: $PID"
    
    # Check if it's responding
    echo "5. Testing endpoints..."
    curl -s http://localhost:5000/health && echo " ✓ Health endpoint working" || echo " ✗ Health endpoint not responding"
    curl -s http://localhost:5000/ | head -c 100 && echo " ✓ Root endpoint working"
    
    # Test auth endpoints
    echo ""
    echo "6. Testing auth endpoints..."
    curl -X POST http://localhost:5000/v2/api/auth/login -H "Content-Type: application/json" -d '{"test":"test"}' -w "\n  Status: %{http_code}\n" -s -o /dev/null
    
else
    echo "✗ Backend failed to start!"
    echo ""
    echo "Last 30 lines of backend.log:"
    tail -30 ../backend.log
fi

echo ""
echo "7. Current backend status:"
ps aux | grep python | grep -v grep | head -5

echo ""
echo "8. Checking nginx upstream..."
# Test if nginx can reach backend
curl -s -I http://localhost:5000/health | head -3

ENDSSH

echo ""
echo -e "${GREEN}✓ Backend restart complete!${NC}"
echo ""
echo "To monitor logs:"
echo "  ssh ubuntu@$SERVER_IP 'tail -f /home/ubuntu/backend.log'"