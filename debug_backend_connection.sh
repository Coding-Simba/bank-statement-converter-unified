#!/bin/bash

SERVER_IP="3.235.19.83"
KEY_PATH="/Users/MAC/Downloads/bank-statement-converter.pem"
SERVER_USER="ubuntu"

echo "Debugging backend connection issues"
echo "=================================="

ssh -i "$KEY_PATH" "$SERVER_USER@$SERVER_IP" << 'EOF'

echo "1. Checking what's listening on port 5000..."
echo "=========================================="
sudo netstat -tlnp | grep :5000 || echo "Nothing listening on port 5000"

echo -e "\n2. Checking if backend process exists..."
echo "======================================"
ps aux | grep -E "uvicorn|python.*main:app" | grep -v grep || echo "No uvicorn process found"

echo -e "\n3. Starting backend with explicit output..."
echo "========================================"
cd /home/ubuntu/bank-statement-converter/backend

# Kill any existing processes
pkill -f uvicorn || true
pkill -f "python.*main:app" || true
sleep 3

# Start with explicit output to see what happens
echo "Starting backend..."
source venv/bin/activate
python3 -m uvicorn main:app --host 0.0.0.0 --port 5000 &
BACKEND_PID=$!

# Wait and check
sleep 5

if kill -0 $BACKEND_PID 2>/dev/null; then
    echo "✅ Backend started with PID $BACKEND_PID"
    
    # Check if it's actually listening
    if sudo netstat -tlnp | grep :5000; then
        echo "✅ Backend is listening on port 5000"
        
        # Test locally
        echo -e "\nLocal test:"
        curl -s http://localhost:5000/v2/api/auth/csrf | python3 -m json.tool || echo "Local test failed"
    else
        echo "❌ Backend process exists but not listening on port 5000"
    fi
else
    echo "❌ Backend process died"
    echo "Checking for errors in output..."
fi

echo -e "\n4. Checking firewall rules..."
echo "============================"
sudo ufw status | grep 5000 || echo "No specific rule for port 5000"

echo -e "\n5. Testing connection from nginx to backend..."
echo "==========================================="
# Test if nginx can reach backend
curl -s http://localhost:5000/v2/api/auth/csrf -H "Host: localhost" | python3 -m json.tool && echo "✅ Direct connection works" || echo "❌ Direct connection failed"

echo -e "\n6. Checking nginx user permissions..."
echo "==================================="
ps aux | grep nginx | grep -v grep

echo -e "\n7. Last attempt - checking SELinux/AppArmor..."
echo "==========================================="
if command -v getenforce &> /dev/null; then
    getenforce
else
    echo "SELinux not installed"
fi

if command -v aa-status &> /dev/null; then
    sudo aa-status | grep nginx || echo "No AppArmor profile for nginx"
else
    echo "AppArmor not active"
fi

EOF