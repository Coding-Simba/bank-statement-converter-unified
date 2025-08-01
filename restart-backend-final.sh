#!/bin/bash

# Restart Backend Final
echo "🔄 Restarting Backend (Final)"
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
cd /home/ubuntu/backend

echo "1. Killing all Python processes..."
pkill -9 -f python || true
sleep 3

echo -e "\n2. Clearing logs..."
> backend.log

echo -e "\n3. Starting backend with proper configuration..."
# Export environment variables
export $(cat .env | grep -v '^#' | xargs)

# Start backend
nohup python3 -m uvicorn main:app --host 0.0.0.0 --port 5000 --log-level info > backend.log 2>&1 &
BACKEND_PID=$!
echo "Started backend with PID: $BACKEND_PID"

sleep 7

echo -e "\n4. Checking if backend is running..."
if ps -p $BACKEND_PID > /dev/null; then
    echo "✓ Backend is running"
    
    # Check health
    curl -s http://localhost:5000/health | jq '.' 2>/dev/null || echo "Health check response received"
    
    echo -e "\n5. Testing authentication..."
    LOGIN=$(curl -X POST http://localhost:5000/api/auth/login \
      -H "Content-Type: application/json" \
      -d '{"email":"test@example.com","password":"test123"}' \
      -s)
    
    TOKEN=$(echo "$LOGIN" | python3 -c "import sys, json; print(json.load(sys.stdin).get('access_token', ''))" 2>/dev/null)
    
    if [ -n "$TOKEN" ]; then
        echo "✓ Authentication working"
        
        echo -e "\n6. Testing Stripe checkout..."
        curl -X POST http://localhost:5000/api/stripe/create-checkout-session \
          -H "Authorization: Bearer $TOKEN" \
          -H "Content-Type: application/json" \
          -d '{"price_id": "price_1RqZtaKwQLBjGTW9w20V3Hst"}' \
          -s | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    if 'checkout_url' in data:
        print(f'✓ Stripe checkout working!')
        print(f'  Checkout URL: {data[\"checkout_url\"][:50]}...')
    else:
        print('✗ No checkout URL in response:', data)
except Exception as e:
    print(f'✗ Error: {e}')
"
    else
        echo "✗ Authentication failed"
    fi
else
    echo "✗ Backend crashed!"
    echo "Last 30 lines of log:"
    tail -30 backend.log
fi

echo -e "\n7. Checking nginx upstream..."
curl -I http://localhost:5000/health 2>/dev/null | head -3

ENDSSH

echo ""
echo -e "${GREEN}✓ Backend restarted!${NC}"
echo ""
echo "You should now be able to:"
echo "1. Login at: https://bankcsvconverter.com/login.html"
echo "2. Purchase a subscription at: https://bankcsvconverter.com/pricing.html"