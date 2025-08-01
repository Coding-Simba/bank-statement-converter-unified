#!/bin/bash

SERVER_IP="3.235.19.83"
KEY_PATH="/Users/MAC/Downloads/bank-statement-converter.pem"
SERVER_USER="ubuntu"

echo "Installing all backend dependencies"
echo "=================================="

ssh -i "$KEY_PATH" "$SERVER_USER@$SERVER_IP" << 'EOF'
cd /home/ubuntu/bank-statement-converter/backend

echo "1. Activating virtual environment..."
source venv/bin/activate

echo -e "\n2. Installing all required packages..."
pip install stripe PyJWT python-jose passlib bcrypt python-multipart

echo -e "\n3. Checking imports one by one..."
python3 -c "import stripe; print('✅ stripe imported successfully')" 2>&1
python3 -c "import jwt; print('✅ jwt imported successfully')" 2>&1
python3 -c "import passlib; print('✅ passlib imported successfully')" 2>&1
python3 -c "import user_agents; print('✅ user_agents imported successfully')" 2>&1

echo -e "\n4. Starting backend with full output..."
pkill -f "uvicorn main:app" || true
sleep 2

# Start with full output to see what happens
echo "Starting uvicorn..."
timeout 10 uvicorn main:app --host 0.0.0.0 --port 5000 2>&1 | tee startup.log || true

# Check if it's running after timeout
if pgrep -f "uvicorn main:app" > /dev/null; then
    echo -e "\n✅ Backend is running!"
    
    # Start it properly in background
    pkill -f "uvicorn main:app"
    nohup uvicorn main:app --host 0.0.0.0 --port 5000 > server.log 2>&1 &
    sleep 3
    
    echo -e "\nTesting endpoints:"
    echo "1. Health check:"
    curl -s http://localhost:5000/ || echo "No root endpoint"
    
    echo -e "\n2. CSRF token:"
    curl -s http://localhost:5000/v2/api/auth/csrf
    
    echo -e "\n\n3. Available routes:"
    curl -s http://localhost:5000/openapi.json | python3 -m json.tool | grep -E '"path":|"summary":' | head -20 || echo "Could not get routes"
else
    echo -e "\n❌ Backend failed to start. Checking error:"
    tail -50 startup.log
fi

EOF