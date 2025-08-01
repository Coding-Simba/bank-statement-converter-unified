#!/bin/bash

# Find Pricing Structure
echo "🔍 Finding Pricing Structure"
echo "==========================="
echo ""

SERVER_IP="3.235.19.83"
SERVER_USER="ubuntu"
SSH_KEY="/Users/MAC/Downloads/bank-statement-converter.pem"

# Check SSH key
if [ ! -f "$SSH_KEY" ]; then
    echo -e "${RED}✗ SSH key not found at $SSH_KEY${NC}"
    exit 1
fi

# Find via SSH
ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no "$SERVER_USER@$SERVER_IP" << 'ENDSSH'
cd /home/ubuntu/bank-statement-converter

echo "1. Looking for the pricing cards section..."
grep -A 100 "pricing-cards\|pricing-grid" pricing.html | grep -B 5 -A 15 "Starter\|Professional\|Business" | head -100

echo -e "\n2. Looking for any pricing-related buttons or links..."
grep -A 10 -B 10 "plan-price\|price-amount\|/month\|/year" pricing.html | grep -A 5 -B 5 "button\|btn\|cta" | head -50

echo -e "\n3. Checking if pricing is dynamically generated..."
grep -E "id=.*pricing|class=.*pricing" pricing.html | head -20

echo -e "\n4. Looking for the actual pricing section..."
sed -n '/<div class="pricing-grid">/,/<\/section>/p' pricing.html | head -100

ENDSSH

echo ""
echo "✓ Check complete!"