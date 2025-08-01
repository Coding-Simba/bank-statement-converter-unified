#!/bin/bash

SERVER_IP="3.235.19.83"
KEY_PATH="/Users/MAC/Downloads/bank-statement-converter.pem"
SERVER_USER="ubuntu"

echo "Diagnosing backend crash"
echo "======================="

ssh -i "$KEY_PATH" "$SERVER_USER@$SERVER_IP" << 'EOF'
cd /home/ubuntu/bank-statement-converter/backend

echo "1. Checking if backend is running..."
if pgrep -f "uvicorn main:app" > /dev/null; then
    echo "✅ Backend process found"
    ps aux | grep "uvicorn main:app" | grep -v grep
else
    echo "❌ Backend is not running!"
fi

echo -e "\n2. Checking server.log for errors..."
echo "===================================="
tail -50 server.log

echo -e "\n3. Trying to start backend manually to see errors..."
echo "=================================================="
source venv/bin/activate

# Try to start and capture immediate errors
timeout 5 python3 -m uvicorn main:app --host 0.0.0.0 --port 5000 2>&1 || true

echo -e "\n4. Checking Python syntax..."
echo "=========================="
python3 -m py_compile main.py 2>&1 || echo "Syntax error in main.py"
python3 -m py_compile api/auth_cookie.py 2>&1 || echo "Syntax error in auth_cookie.py"

echo -e "\n5. Let's check if there's a port conflict..."
echo "==========================================="
sudo lsof -i :5000 || echo "Port 5000 is free"

echo -e "\n6. Starting backend with simple nohup..."
echo "======================================"
pkill -f "uvicorn" || true
sleep 2

nohup python3 -m uvicorn main:app --host 0.0.0.0 --port 5000 > backend.log 2>&1 &
sleep 5

if pgrep -f "uvicorn main:app" > /dev/null; then
    echo "✅ Backend started successfully"
    
    # Quick test
    curl -s http://localhost:5000/v2/api/auth/csrf | python3 -m json.tool || echo "Backend not responding"
else
    echo "❌ Backend failed to start"
    echo "Error log:"
    cat backend.log
fi

EOF