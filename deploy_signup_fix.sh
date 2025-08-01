#!/bin/bash

SERVER_IP="3.235.19.83"
KEY_PATH="/Users/MAC/Downloads/bank-statement-converter.pem"
SERVER_USER="ubuntu"

echo "Deploying signup registration fix"
echo "================================="

# Deploy updated auth-unified.js with register function
echo "1. Deploying updated auth-unified.js..."
scp -i "$KEY_PATH" js/auth-unified.js "$SERVER_USER@$SERVER_IP:/home/ubuntu/bank-statement-converter/frontend/js/"

# Deploy updated signup.html
echo "2. Deploying updated signup.html..."
scp -i "$KEY_PATH" signup.html "$SERVER_USER@$SERVER_IP:/home/ubuntu/bank-statement-converter/frontend/"

# Verify deployment
echo "3. Verifying deployment..."
ssh -i "$KEY_PATH" "$SERVER_USER@$SERVER_IP" << 'EOF'
cd /home/ubuntu/bank-statement-converter/frontend

echo "Checking register function in auth-unified.js:"
grep -n "async register" js/auth-unified.js | head -2

echo -e "\nChecking signup form handler:"
grep -n "signupForm" js/auth-unified.js | head -2

echo -e "\nChecking signup.html uses auth-unified.js:"
grep "auth-unified.js" signup.html
EOF

echo -e "\n✅ Signup registration fix deployed!"
echo "=================================="
echo "Test creating an account at: https://bankcsvconverter.com/signup.html"