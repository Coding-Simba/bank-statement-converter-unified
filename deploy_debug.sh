#!/bin/bash

SERVER_IP="3.235.19.83"
KEY_PATH="/Users/MAC/Downloads/bank-statement-converter.pem"
SERVER_USER="ubuntu"

echo "Deploying Debug Script"
echo "====================="

# Deploy debug script
scp -i "$KEY_PATH" js/debug-auth.js "$SERVER_USER@$SERVER_IP:/home/ubuntu/bank-statement-converter/frontend/js/"

# Add to both login and pricing pages
ssh -i "$KEY_PATH" "$SERVER_USER@$SERVER_IP" << 'EOF'
cd /home/ubuntu/bank-statement-converter/frontend

# Add to login page
if ! grep -q "debug-auth.js" login.html; then
    sed -i '/<script src="\/js\/api-config\.js"><\/script>/a\    <script src="/js/debug-auth.js"></script>' login.html
fi

# Add to pricing page
if ! grep -q "debug-auth.js" pricing.html; then
    sed -i '/<script src="\/js\/api-config\.js"><\/script>/a\    <script src="/js/debug-auth.js"></script>' pricing.html
fi

echo "Debug script added to both pages"
EOF

echo -e "\n✅ Debug script deployed!"
echo "Now when you test the flow, check the console for:"
echo "- [Debug Auth] messages showing localStorage operations"
echo "- What tokens are being set/removed"
echo "- API call responses"