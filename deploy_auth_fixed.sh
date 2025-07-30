#!/bin/bash

# Deploy auth-fixed.js to resolve authentication persistence issues

SERVER_IP="3.235.19.83"
KEY_PATH="/Users/MAC/Downloads/bank-statement-converter.pem"
SERVER_USER="ubuntu"

echo "Deploying Authentication Fix (auth-fixed.js)"
echo "==========================================="

# Deploy auth-fixed.js
echo "1. Deploying auth-fixed.js..."
scp -i "$KEY_PATH" js/auth-fixed.js "$SERVER_USER@$SERVER_IP:/home/ubuntu/bank-statement-converter/frontend/js/"

# Update pricing.html to use auth-fixed.js
echo "2. Updating pricing.html..."
ssh -i "$KEY_PATH" "$SERVER_USER@$SERVER_IP" << 'EOF'
cd /home/ubuntu/bank-statement-converter/frontend
# Remove old auth scripts from pricing.html
sed -i '/<script src="\/js\/auth-global\.js"><\/script>/d' pricing.html
sed -i '/<script src="\/js\/auth-persistent\.js"><\/script>/d' pricing.html
sed -i '/<script src="\/js\/auth-universal\.js"><\/script>/d' pricing.html
# Add auth-fixed.js if not already present
if ! grep -q "auth-fixed.js" pricing.html; then
    sed -i '/<script src="\/js\/auth\.js"><\/script>/a\    <script src="/js/auth-fixed.js"></script>' pricing.html
fi
EOF

# Update dashboard-modern.html to use auth-fixed.js
echo "3. Updating dashboard-modern.html..."
ssh -i "$KEY_PATH" "$SERVER_USER@$SERVER_IP" << 'EOF'
cd /home/ubuntu/bank-statement-converter/frontend
# Remove old auth scripts from dashboard-modern.html
sed -i '/<script src="\/js\/auth-universal\.js"><\/script>/d' dashboard-modern.html
# Add auth-fixed.js if not already present
if ! grep -q "auth-fixed.js" dashboard-modern.html; then
    sed -i '/<script src="\/js\/auth\.js"><\/script>/a\    <script src="/js/auth-fixed.js"></script>' dashboard-modern.html
fi
EOF

# Update index.html (homepage)
echo "4. Updating index.html..."
ssh -i "$KEY_PATH" "$SERVER_USER@$SERVER_IP" << 'EOF'
cd /home/ubuntu/bank-statement-converter/frontend
# Remove old auth scripts
sed -i '/<script src="\/js\/auth-global\.js"><\/script>/d' index.html
sed -i '/<script src="\/js\/auth-persistent\.js"><\/script>/d' index.html
sed -i '/<script src="\/js\/auth-universal\.js"><\/script>/d' index.html
# Add auth-fixed.js if not already present
if ! grep -q "auth-fixed.js" index.html; then
    sed -i '/<script src="\/js\/auth\.js"><\/script>/a\    <script src="/js/auth-fixed.js"></script>' index.html
fi
EOF

# Update settings.html
echo "5. Updating settings.html..."
ssh -i "$KEY_PATH" "$SERVER_USER@$SERVER_IP" << 'EOF'
cd /home/ubuntu/bank-statement-converter/frontend
# Remove old auth scripts
sed -i '/<script src="\/js\/auth-global\.js"><\/script>/d' settings.html
sed -i '/<script src="\/js\/auth-persistent\.js"><\/script>/d' settings.html
sed -i '/<script src="\/js\/auth-universal\.js"><\/script>/d' settings.html
# Add auth-fixed.js if not already present
if ! grep -q "auth-fixed.js" settings.html; then
    sed -i '/<script src="\/js\/auth\.js"><\/script>/a\    <script src="/js/auth-fixed.js"></script>' settings.html
fi
EOF

echo -e "\n✅ Authentication fix deployed!"
echo "============================="
echo "What was fixed:"
echo "- auth-fixed.js doesn't clear tokens on API errors"
echo "- Removed conflicting auth scripts from all pages"
echo "- Added auth-fixed.js to all main pages"
echo ""
echo "Test instructions:"
echo "1. Clear browser cache/cookies"
echo "2. Log in at https://bankcsvconverter.com/login.html"
echo "3. Navigate to https://bankcsvconverter.com/pricing.html"
echo "4. You should remain logged in!"
echo "5. Check other pages - authentication should persist"