#!/bin/bash

SERVER_IP="3.235.19.83"
KEY_PATH="/Users/MAC/Downloads/bank-statement-converter.pem"
SERVER_USER="ubuntu"

echo "Deploying Complete Stripe Fix"
echo "============================="

# Deploy the complete fix
echo "1. Deploying stripe-complete-fix.js..."
scp -i "$KEY_PATH" js/stripe-complete-fix.js "$SERVER_USER@$SERVER_IP:/home/ubuntu/bank-statement-converter/frontend/js/"

# Clean up pricing.html
echo "2. Cleaning up pricing.html..."
ssh -i "$KEY_PATH" "$SERVER_USER@$SERVER_IP" << 'EOF'
cd /home/ubuntu/bank-statement-converter/frontend

# Remove ALL old stripe scripts
sed -i '/<script src="\/js\/stripe-.*\.js"><\/script>/d' pricing.html

# Keep only essential scripts and add the complete fix
grep -v "stripe-" pricing.html > pricing.html.tmp
mv pricing.html.tmp pricing.html

# Ensure we have the basic scripts before </body>
if ! grep -q "api-config.js" pricing.html; then
    sed -i '/<\/body>/i\    <script src="/js/api-config.js"></script>' pricing.html
fi

if ! grep -q "auth-fixed.js" pricing.html; then
    sed -i '/<\/body>/i\    <script src="/js/auth-fixed.js"></script>' pricing.html
fi

# Add the complete fix
sed -i '/<\/body>/i\    <script src="/js/stripe-complete-fix.js"></script>' pricing.html

echo "Pricing page cleaned and updated"
EOF

# Clean up login.html
echo "3. Cleaning up login.html..."
ssh -i "$KEY_PATH" "$SERVER_USER@$SERVER_IP" << 'EOF'
cd /home/ubuntu/bank-statement-converter/frontend

# Remove old redirect handlers
sed -i '/<script src="\/js\/auth-redirect-fix\.js"><\/script>/d' login.html
sed -i '/<script src="\/js\/login-redirect-handler\.js"><\/script>/d' login.html

# Add the complete fix to login page too
if ! grep -q "stripe-complete-fix.js" login.html; then
    sed -i '/<\/body>/i\    <script src="/js/stripe-complete-fix.js"></script>' login.html
fi

echo "Login page cleaned and updated"
EOF

echo -e "\n✅ Complete fix deployed!"
echo "========================="
echo "This fix handles:"
echo "1. Authentication checking"
echo "2. Login redirect with saved state"
echo "3. Auto-clicking after login redirect"
echo "4. Direct API calls (bypasses auth.js)"
echo "5. Proper error handling"
echo ""
echo "Please clear your browser cache and test again!"