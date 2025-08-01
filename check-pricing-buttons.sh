#!/bin/bash

# Check Pricing Buttons
echo "🔍 Checking Pricing Page Buttons"
echo "================================"
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
cd /home/ubuntu/bank-statement-converter

echo "1. Looking for buy buttons in pricing.html..."
echo "Searching for data-plan attributes:"
grep -n "data-plan" pricing.html | head -10

echo -e "\n2. Looking for button elements with class or id..."
grep -E "<button|<a.*button" pricing.html | grep -i "buy\|get\|start\|choose" | head -10

echo -e "\n3. Looking for onclick handlers..."
grep -n "onclick" pricing.html | grep -i "buy\|stripe\|checkout" | head -10

echo -e "\n4. Checking the actual button structure..."
# Look for the pricing cards
grep -A 5 -B 5 "Start Free\|Get Started\|Buy Now\|Choose Plan" pricing.html | head -50

echo -e "\n5. Looking for any Stripe-related elements..."
grep -E "stripe|checkout|payment|subscribe" pricing.html | grep -v "script" | head -20

echo -e "\n6. Let's check what the stripe-integration.js is looking for..."
grep -A 5 -B 5 "querySelectorAll.*data-plan" js/stripe-integration.js

echo -e "\n7. Checking if there's a different button selector we should use..."
grep -A 10 "pricing-card\|price-card\|plan-card" pricing.html | head -30

ENDSSH

echo ""
echo -e "${GREEN}✓ Check complete!${NC}"