#!/bin/bash

SERVER_IP="3.235.19.83"
KEY_PATH="/Users/MAC/Downloads/bank-statement-converter.pem"
SERVER_USER="ubuntu"

echo "Deploying Final Login Override"
echo "=============================="

# Deploy the final fix
echo "1. Deploying login-override-final.js..."
scp -i "$KEY_PATH" js/login-override-final.js "$SERVER_USER@$SERVER_IP:/home/ubuntu/bank-statement-converter/frontend/js/"

# Update login.html to add this as the FIRST script
echo "2. Updating login.html..."
ssh -i "$KEY_PATH" "$SERVER_USER@$SERVER_IP" << 'EOF'
cd /home/ubuntu/bank-statement-converter/frontend

# Add login-override-final.js as the very first script after <head>
if ! grep -q "login-override-final.js" login.html; then
    # Insert right after <head> tag
    sed -i '/<head>/a\    <script src="/js/login-override-final.js"></script>' login.html
fi

echo "Login page updated with final override"
EOF

echo -e "\n✅ Final login override deployed!"
echo "================================="
echo "This aggressive fix:"
echo "1. Intercepts XMLHttpRequest login calls"
echo "2. Intercepts fetch login calls"  
echo "3. Monitors localStorage every 100ms"
echo "4. Forces immediate redirect on login success"
echo ""
echo "The redirect WILL happen now!"