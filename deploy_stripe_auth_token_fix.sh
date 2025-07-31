#!/bin/bash

# Deploy Stripe auth token fix

SERVER_IP="3.235.19.83"
KEY_PATH="/Users/MAC/Downloads/bank-statement-converter.pem"
SERVER_USER="ubuntu"

echo "Deploying Stripe Auth Token Fix"
echo "================================"

# Deploy stripe-auth-fix.js
echo "1. Deploying stripe-auth-fix.js..."
scp -i "$KEY_PATH" js/stripe-auth-fix.js "$SERVER_USER@$SERVER_IP:/home/ubuntu/bank-statement-converter/frontend/js/"

# Update pricing.html to include the fix
echo "2. Updating pricing.html..."
ssh -i "$KEY_PATH" "$SERVER_USER@$SERVER_IP" << 'EOF'
cd /home/ubuntu/bank-statement-converter/frontend
# Add stripe-auth-fix.js before stripe-integration-fixed.js
if ! grep -q "stripe-auth-fix.js" pricing.html; then
    sed -i '/<script src="\/js\/stripe-integration-fixed\.js"><\/script>/i\    <script src="/js/stripe-auth-fix.js"></script>' pricing.html
fi
echo "Pricing page updated with token fix"
EOF

echo -e "\n✅ Stripe auth token fix deployed!"
echo "===================================="
echo "What was fixed:"
echo "1. Automatic token refresh before Stripe API calls"
echo "2. Token expiry detection (refreshes if < 5 min left)"
echo "3. Graceful handling of expired tokens"
echo "4. Intercepts Stripe API calls to ensure fresh token"
echo ""
echo "The 401 Unauthorized errors should now be resolved!"