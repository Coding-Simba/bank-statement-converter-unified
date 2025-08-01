#!/bin/bash

# Check Stripe Status
echo "🔍 Checking Stripe Status"
echo "========================"
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

# Check via SSH
ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no "$SERVER_USER@$SERVER_IP" << 'ENDSSH'
cd /home/ubuntu/backend

echo "1. Checking if backend is running..."
ps aux | grep -E "uvicorn|python.*main" | grep -v grep | head -5

echo -e "\n2. Checking recent logs..."
echo "Last 30 lines of backend log:"
tail -30 backend_stripe_fixed.log 2>/dev/null || tail -30 backend_stripe.log 2>/dev/null || tail -30 backend.log

echo -e "\n3. Testing Stripe configuration directly..."
python3 -c "
import os
from dotenv import load_dotenv
load_dotenv()

stripe_key = os.getenv('STRIPE_SECRET_KEY')
if stripe_key:
    print(f'✓ Stripe key found: {stripe_key[:10]}...')
else:
    print('❌ Stripe key NOT found')

import stripe
stripe.api_key = stripe_key
print(f'✓ Stripe configured with key: {stripe.api_key[:10] if stripe.api_key else \"NONE\"}...')
"

echo -e "\n4. Checking if Stripe module is properly imported..."
python3 -c "
try:
    from api.stripe import router
    print('✓ Stripe router imported successfully')
except Exception as e:
    print(f'❌ Error importing Stripe router: {e}')
"

echo -e "\n5. Starting backend manually to see errors..."
# Kill existing
pkill -f "uvicorn main:app" || true
sleep 2

# Start in foreground briefly
timeout 10 python3 -m uvicorn main:app --host 0.0.0.0 --port 5000 2>&1 | head -50 &
PID=$!
sleep 5
kill $PID 2>/dev/null || true

echo -e "\n6. Starting backend in background again..."
nohup python3 -m uvicorn main:app --host 0.0.0.0 --port 5000 > backend_current.log 2>&1 &
sleep 5

echo -e "\n7. Final test of Stripe endpoint..."
# Get auth token
TOKEN=$(curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test123"}' \
  -s | python3 -c "import sys, json; print(json.load(sys.stdin).get('access_token', ''))" 2>/dev/null)

if [ -n "$TOKEN" ]; then
    echo "Testing checkout with real price ID:"
    curl -X POST http://localhost:5000/api/stripe/create-checkout-session \
      -H "Authorization: Bearer $TOKEN" \
      -H "Content-Type: application/json" \
      -d '{
        "price_id": "price_1RqZtaKwQLBjGTW9w20V3Hst"
      }' \
      -w "\nStatus: %{http_code}\n" -s | head -20
fi

ENDSSH

echo ""
echo -e "${GREEN}✓ Status check complete!${NC}"