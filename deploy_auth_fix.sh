#\!/bin/bash

# Deploy auth persistence fix

SERVER_IP="3.235.19.83"
KEY_PATH="/Users/MAC/Downloads/bank-statement-converter.pem"
SERVER_USER="ubuntu"

echo "Deploying Auth Persistence Fix"
echo "=============================="

# Deploy updated files
echo "1. Deploying updated auth files..."
scp -i "$KEY_PATH" js/auth-persistent.js "$SERVER_USER@$SERVER_IP:/home/ubuntu/bank-statement-converter/frontend/js/"
scp -i "$KEY_PATH" js/auth.js "$SERVER_USER@$SERVER_IP:/home/ubuntu/bank-statement-converter/frontend/js/"

echo -e "\n✅ Auth fix deployed\!"
echo "============================"
echo "Test instructions:"
echo "1. Clear your browser data (Application > Storage > Clear site data)"
echo "2. Log in at https://bankcsvconverter.com/login.html"
echo "3. Check localStorage - you should see both 'user' and 'user_data'"
echo "4. Visit https://bankcsvconverter.com/pricing.html"
echo "5. You should see your user menu now\!"
