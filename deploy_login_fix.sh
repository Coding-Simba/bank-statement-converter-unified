#!/bin/bash

SERVER_IP="3.235.19.83"
KEY_PATH="/Users/MAC/Downloads/bank-statement-converter.pem"
SERVER_USER="ubuntu"

echo "Deploying Login Redirect Fix"
echo "============================"

# Deploy auth-login-fix.js
echo "1. Deploying auth-login-fix.js..."
scp -i "$KEY_PATH" js/auth-login-fix.js "$SERVER_USER@$SERVER_IP:/home/ubuntu/bank-statement-converter/frontend/js/"

# Update login.html to add the fix AFTER auth.js
echo "2. Updating login.html..."
ssh -i "$KEY_PATH" "$SERVER_USER@$SERVER_IP" << 'EOF'
cd /home/ubuntu/bank-statement-converter/frontend

# Add auth-login-fix.js after auth.js to ensure it can override
if ! grep -q "auth-login-fix.js" login.html; then
    # Find where auth.js is loaded and add our fix after it
    sed -i '/<script src="\/js\/auth\.js"><\/script>/a\    <script src="/js/auth-login-fix.js"></script>' login.html
fi

echo "Login page updated with redirect fix"
EOF

echo -e "\n✅ Login redirect fix deployed!"
echo "==============================="
echo "This fix:"
echo "1. Intercepts the login process"
echo "2. Checks for saved redirect URL in sessionStorage"
echo "3. Redirects to pricing page instead of dashboard"
echo "4. Works even if auth.js tries to redirect to dashboard"
echo ""
echo "Try the flow again - you should now be redirected back to pricing after login!"