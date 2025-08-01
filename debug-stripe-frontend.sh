#!/bin/bash

# Debug Stripe Frontend
echo "🔍 Debugging Stripe Frontend Integration"
echo "======================================="
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
cd /home/ubuntu/bank-statement-converter

echo "1. Checking stripe-integration.js..."
echo "Looking for the checkout request logic:"
grep -A 20 -B 5 "create-checkout-session" js/stripe-integration.js | head -40

echo -e "\n2. Looking for price_id mapping..."
grep -A 10 -B 5 "price_id\|priceId\|plan.*billing" js/stripe-integration.js | head -30

echo -e "\n3. Checking if stripe-integration.js sends the correct payload..."
sed -n '/makeAuthenticatedRequest.*create-checkout-session/,/catch/p' js/stripe-integration.js | head -50

echo -e "\n4. Let's check the actual request format expected by backend..."
cd /home/ubuntu/backend
grep -A 10 "class CheckoutSessionRequest" api/stripe.py

echo -e "\n5. Looking for the price ID configuration in frontend..."
cd /home/ubuntu/bank-statement-converter
grep -r "price_.*BUSINESS\|PROFESSIONAL\|STARTER" js/*.js | head -20

echo -e "\n6. Checking recent nginx error logs..."
sudo tail -20 /var/log/nginx/error.log | grep -E "(stripe|checkout)" || echo "No stripe errors in nginx logs"

echo -e "\n7. Checking recent backend logs for checkout attempts..."
cd /home/ubuntu/backend
tail -50 backend.log | grep -E "(checkout|stripe|create-checkout)" | tail -10

ENDSSH

echo ""
echo -e "${GREEN}✓ Debug complete!${NC}"