#!/bin/bash

SERVER_IP="3.235.19.83"
KEY_PATH="/Users/MAC/Downloads/bank-statement-converter.pem"
SERVER_USER="ubuntu"

echo "Deploying login redirect handler"
echo "================================"

# Deploy the handler
scp -i "$KEY_PATH" js/login-redirect-handler.js "$SERVER_USER@$SERVER_IP:/home/ubuntu/bank-statement-converter/frontend/js/"

# Update login.html
ssh -i "$KEY_PATH" "$SERVER_USER@$SERVER_IP" << 'EOF'
cd /home/ubuntu/bank-statement-converter/frontend

# Remove auth-redirect-fix.js as it's causing issues
sed -i '/<script src="\/js\/auth-redirect-fix\.js"><\/script>/d' login.html

# Add login-redirect-handler.js
if ! grep -q "login-redirect-handler.js" login.html; then
    sed -i '/<\/body>/i\    <script src="/js/login-redirect-handler.js"></script>' login.html
fi

echo "Login page updated with redirect handler"
EOF

echo -e "\n✅ Login redirect handler deployed!"