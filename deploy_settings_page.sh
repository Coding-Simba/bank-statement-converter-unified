#\!/bin/bash

# Deploy Settings Page to Production

SERVER_IP="3.235.19.83"
KEY_PATH="/Users/MAC/Downloads/bank-statement-converter.pem"
SERVER_USER="ubuntu"

echo "Deploying Settings Page"
echo "======================"

# Copy files
echo "1. Copying settings page files..."
scp -i "$KEY_PATH" settings.html "$SERVER_USER@$SERVER_IP:/home/ubuntu/bank-statement-converter/frontend/"
scp -i "$KEY_PATH" css/settings.css "$SERVER_USER@$SERVER_IP:/home/ubuntu/bank-statement-converter/frontend/css/"
scp -i "$KEY_PATH" js/settings.js "$SERVER_USER@$SERVER_IP:/home/ubuntu/bank-statement-converter/frontend/js/"

echo -e "\n2. Setting permissions..."
ssh -i "$KEY_PATH" "$SERVER_USER@$SERVER_IP" << 'PERMS'
cd /home/ubuntu/bank-statement-converter/frontend
chmod 644 settings.html
chmod 644 css/settings.css
chmod 644 js/settings.js
echo "✓ Permissions set"
PERMS

echo -e "\n3. Testing deployment..."
SETTINGS_STATUS=$(curl -s -o /dev/null -w "%{http_code}" https://bankcsvconverter.com/settings.html)

if [ "$SETTINGS_STATUS" == "200" ]; then
    echo "✅ Settings page deployed successfully\!"
    echo "View at: https://bankcsvconverter.com/settings.html"
else
    echo "❌ Settings page returned HTTP $SETTINGS_STATUS"
fi

echo -e "\nDeployment complete\!"
