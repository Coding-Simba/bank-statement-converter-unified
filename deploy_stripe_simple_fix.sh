#!/bin/bash

# Deploy simple Stripe fix that bypasses auth.js

SERVER_IP="3.235.19.83"
KEY_PATH="/Users/MAC/Downloads/bank-statement-converter.pem"
SERVER_USER="ubuntu"

echo "Deploying Simple Stripe Fix"
echo "==========================="

# Deploy stripe-simple-fix.js
echo "1. Deploying stripe-simple-fix.js..."
scp -i "$KEY_PATH" js/stripe-simple-fix.js "$SERVER_USER@$SERVER_IP:/home/ubuntu/bank-statement-converter/frontend/js/"

# Update pricing.html
echo "2. Updating pricing.html..."
ssh -i "$KEY_PATH" "$SERVER_USER@$SERVER_IP" << 'EOF'
cd /home/ubuntu/bank-statement-converter/frontend
# Remove the problematic auth.js that intercepts fetch
sed -i '/<script src="\/js\/auth\.js"><\/script>/d' pricing.html
# Add stripe-simple-fix.js at the end
if ! grep -q "stripe-simple-fix.js" pricing.html; then
    sed -i '/<\/body>/i\    <script src="/js/stripe-simple-fix.js"></script>' pricing.html
fi
echo "Pricing page updated"
EOF

echo -e "\n✅ Simple Stripe fix deployed!"
echo "=============================="
echo "What this does:"
echo "1. Bypasses auth.js fetch interception"
echo "2. Makes direct API calls to Stripe endpoint"
echo "3. Handles 401 errors by redirecting to login"
echo "4. No complex token refresh logic"
echo ""
echo "Try clicking a buy button now!"