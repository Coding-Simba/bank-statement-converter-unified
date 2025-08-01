#!/bin/bash

# Debug Auth Stripe
echo "🔍 Debugging Auth for Stripe"
echo "============================"
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

# Debug via SSH
ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no "$SERVER_USER@$SERVER_IP" << 'ENDSSH'

echo "1. Checking UnifiedAuth makeAuthenticatedRequest method..."
cd /home/ubuntu/bank-statement-converter
grep -A 20 "makeAuthenticatedRequest" js/auth-unified*.js | head -40

echo -e "\n2. Checking if auth middleware is properly configured in Stripe endpoints..."
cd /home/ubuntu/backend
grep -A 5 -B 5 "get_current_user\|Depends" api/stripe.py | head -30

echo -e "\n3. Looking at the auth middleware implementation..."
grep -A 10 "get_current_user" middleware/auth_middleware.py 2>/dev/null || \
grep -A 10 "get_current_user" utils/auth.py 2>/dev/null || \
echo "Auth middleware not found in expected locations"

echo -e "\n4. Checking backend logs for auth errors..."
tail -50 backend.log | grep -E "(403|Forbidden|Not authenticated|stripe)" | tail -20

echo -e "\n5. Let's test the auth flow manually..."
# First get a token
echo "Getting auth token..."
TOKEN=$(curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test123"}' \
  -s | python3 -c "import sys, json; print(json.load(sys.stdin).get('access_token', ''))" 2>/dev/null)

if [ -n "$TOKEN" ]; then
    echo "Got token: ${TOKEN:0:50}..."
    
    echo -e "\nTesting Stripe endpoint with Authorization header:"
    curl -X POST http://localhost:5000/api/stripe/create-checkout-session \
      -H "Authorization: Bearer $TOKEN" \
      -H "Content-Type: application/json" \
      -d '{"price_id": "price_1RqZtaKwQLBjGTW9w20V3Hst"}' \
      -w "\nStatus: %{http_code}\n" -s | head -10
else
    echo "Failed to get token"
fi

echo -e "\n6. Checking CORS configuration..."
grep -A 10 -B 5 "CORS\|cors" main.py | head -20

ENDSSH

echo ""
echo -e "${GREEN}✓ Debug complete!${NC}"