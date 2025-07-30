#\!/bin/bash

# Deploy and test auth persistence

SERVER_IP="3.235.19.83"
KEY_PATH="/Users/MAC/Downloads/bank-statement-converter.pem"
SERVER_USER="ubuntu"

echo "Testing Auth Persistence"
echo "======================="

# 1. Deploy auth-persistent.js
echo "1. Deploying auth-persistent.js..."
scp -i "$KEY_PATH" js/auth-persistent.js "$SERVER_USER@$SERVER_IP:/home/ubuntu/bank-statement-converter/frontend/js/"

# 2. Update key pages
echo -e "\n2. Updating pages..."
scp -i "$KEY_PATH" index.html "$SERVER_USER@$SERVER_IP:/home/ubuntu/bank-statement-converter/frontend/"
scp -i "$KEY_PATH" pricing.html "$SERVER_USER@$SERVER_IP:/home/ubuntu/bank-statement-converter/frontend/"

# 3. Update all pages to use new auth
echo -e "\n3. Updating all pages on server..."
ssh -i "$KEY_PATH" "$SERVER_USER@$SERVER_IP" << 'SSH_SCRIPT'
cd /home/ubuntu/bank-statement-converter/frontend

# Replace auth-global.js with auth-persistent.js in all files
find . -name "*.html" -type f -exec sed -i 's/auth-global\.js/auth-persistent.js/g' {} \;

echo "✓ Updated all pages"
SSH_SCRIPT

# 4. Test auth script is accessible
echo -e "\n4. Testing auth script..."
AUTH_STATUS=$(curl -s -o /dev/null -w "%{http_code}" https://bankcsvconverter.com/js/auth-persistent.js)

if [ "$AUTH_STATUS" == "200" ]; then
    echo "✅ Auth script is accessible\!"
else
    echo "❌ Auth script returned HTTP $AUTH_STATUS"
fi

echo -e "\nDeployment complete\!"
echo "===================="
echo "Test by:"
echo "1. Log in at https://bankcsvconverter.com/login.html"
echo "2. Visit https://bankcsvconverter.com/pricing.html"
echo "3. You should see your user menu instead of login/signup buttons"
