#!/bin/bash

# Test Stripe Integration
echo "💳 Testing Stripe Integration"
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

# Test via SSH
ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no "$SERVER_USER@$SERVER_IP" << 'ENDSSH'

echo "1. Checking Stripe environment configuration..."
cd /home/ubuntu/backend
if [ -f .env ]; then
    echo "Stripe configuration found:"
    grep -i stripe .env | grep -v SECRET | grep -v KEY | head -5
else
    echo "❌ No .env file found!"
fi

echo -e "\n2. Checking frontend Stripe integration..."
cd /home/ubuntu/bank-statement-converter
echo "Looking at stripe-integration.js:"
if [ -f js/stripe-integration.js ]; then
    grep -E "price_id|priceId|checkout|/api/stripe" js/stripe-integration.js | head -20
else
    echo "stripe-integration.js not found"
fi

echo -e "\n3. Testing with authentication..."
# First login to get a token
echo "Logging in to get auth token..."
LOGIN_RESPONSE=$(curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test123"}' \
  -s)

TOKEN=$(echo "$LOGIN_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('access_token', ''))" 2>/dev/null)

if [ -n "$TOKEN" ]; then
    echo "✓ Got auth token"
    
    echo -e "\nTesting subscription status with auth:"
    curl -X GET http://localhost:5000/api/stripe/subscription-status \
      -H "Authorization: Bearer $TOKEN" \
      -w "\nStatus: %{http_code}\n" -s | python3 -m json.tool 2>/dev/null || cat
    
    echo -e "\nTesting checkout session creation:"
    curl -X POST http://localhost:5000/api/stripe/create-checkout-session \
      -H "Authorization: Bearer $TOKEN" \
      -H "Content-Type: application/json" \
      -d '{
        "price_id": "price_test_123",
        "success_url": "https://bankcsvconverter.com/dashboard.html",
        "cancel_url": "https://bankcsvconverter.com/pricing.html"
      }' \
      -w "\nStatus: %{http_code}\n" -s | head -10
else
    echo "❌ Failed to get auth token"
fi

echo -e "\n4. Checking backend logs for Stripe errors..."
tail -30 backend_stripe.log | grep -E "(stripe|Stripe|ERROR|error)" | tail -10

echo -e "\n5. Verifying price IDs are configured..."
cd /home/ubuntu/backend
python3 -c "
import os
from dotenv import load_dotenv
load_dotenv()

print('Configured Price IDs:')
price_ids = [
    ('Starter Monthly', 'STRIPE_STARTER_MONTHLY_PRICE_ID'),
    ('Starter Yearly', 'STRIPE_STARTER_YEARLY_PRICE_ID'),
    ('Professional Monthly', 'STRIPE_PROFESSIONAL_MONTHLY_PRICE_ID'),
    ('Professional Yearly', 'STRIPE_PROFESSIONAL_YEARLY_PRICE_ID'),
    ('Business Monthly', 'STRIPE_BUSINESS_MONTHLY_PRICE_ID'),
    ('Business Yearly', 'STRIPE_BUSINESS_YEARLY_PRICE_ID'),
]

for name, key in price_ids:
    value = os.getenv(key)
    if value:
        print(f'  ✓ {name}: {value[:20]}...')
    else:
        print(f'  ❌ {name}: NOT SET')
"

ENDSSH

echo ""
echo -e "${GREEN}✓ Stripe integration test complete!${NC}"
echo ""
echo "To complete the setup:"
echo "1. Make sure you're logged in"
echo "2. Go to https://bankcsvconverter.com/pricing.html"
echo "3. Click on a plan to start checkout"