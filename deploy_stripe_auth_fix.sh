#!/bin/bash

# Deploy Stripe and Auth redirect fixes

SERVER_IP="3.235.19.83"
KEY_PATH="/Users/MAC/Downloads/bank-statement-converter.pem"
SERVER_USER="ubuntu"

echo "Deploying Stripe and Auth Redirect Fixes"
echo "========================================"

# Deploy new JavaScript files
echo "1. Deploying JavaScript files..."
scp -i "$KEY_PATH" js/stripe-integration-fixed.js "$SERVER_USER@$SERVER_IP:/home/ubuntu/bank-statement-converter/frontend/js/"
scp -i "$KEY_PATH" js/auth-redirect-fix.js "$SERVER_USER@$SERVER_IP:/home/ubuntu/bank-statement-converter/frontend/js/"

# Update pricing.html
echo "2. Updating pricing.html..."
ssh -i "$KEY_PATH" "$SERVER_USER@$SERVER_IP" << 'EOF'
cd /home/ubuntu/bank-statement-converter/frontend
# Replace auth-persistent.js with auth-fixed.js
sed -i 's|<script src="/js/auth-persistent.js"></script>|<script src="/js/auth-fixed.js"></script>|g' pricing.html
# Replace stripe-integration.js with stripe-integration-fixed.js
sed -i 's|<script src="/js/stripe-integration.js"></script>|<script src="/js/stripe-integration-fixed.js"></script>|g' pricing.html
echo "Pricing page updated"
EOF

# Update login.html
echo "3. Updating login.html..."
ssh -i "$KEY_PATH" "$SERVER_USER@$SERVER_IP" << 'EOF'
cd /home/ubuntu/bank-statement-converter/frontend
# Add auth-redirect-fix.js after auth.js
if ! grep -q "auth-redirect-fix.js" login.html; then
    sed -i '/<script src="\/js\/auth\.js"><\/script>/a\    <script src="/js/auth-redirect-fix.js"></script>' login.html
fi
echo "Login page updated"
EOF

# Update signup.html
echo "4. Updating signup.html..."
ssh -i "$KEY_PATH" "$SERVER_USER@$SERVER_IP" << 'EOF'
cd /home/ubuntu/bank-statement-converter/frontend
# Add auth-redirect-fix.js after auth.js
if ! grep -q "auth-redirect-fix.js" signup.html; then
    sed -i '/<script src="\/js\/auth\.js"><\/script>/a\    <script src="/js/auth-redirect-fix.js"></script>' signup.html
fi
echo "Signup page updated"
EOF

echo -e "\n✅ Stripe and Auth fixes deployed!"
echo "============================="
echo "What was fixed:"
echo "1. Buy buttons now check auth status properly"
echo "2. Unauthenticated users redirect to login (not signup)"
echo "3. After login, users go to Stripe checkout (not dashboard)"
echo "4. Pricing page uses auth-fixed.js for persistent auth"
echo ""
echo "Test instructions:"
echo "1. Log out if currently logged in"
echo "2. Go to https://bankcsvconverter.com/pricing.html"
echo "3. Click any 'Buy' button"
echo "4. You should be redirected to login"
echo "5. After login, you should go directly to Stripe checkout"