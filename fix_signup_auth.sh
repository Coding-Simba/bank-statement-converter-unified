#!/bin/bash

SERVER_IP="3.235.19.83"
KEY_PATH="/Users/MAC/Downloads/bank-statement-converter.pem"
SERVER_USER="ubuntu"

echo "Fixing signup page authentication"
echo "================================"

# Deploy updated signup.html
echo "1. Deploying updated signup.html..."
scp -i "$KEY_PATH" signup.html "$SERVER_USER@$SERVER_IP:/home/ubuntu/bank-statement-converter/frontend/"

# Verify the auth script is correct
echo "2. Verifying auth script..."
ssh -i "$KEY_PATH" "$SERVER_USER@$SERVER_IP" << 'EOF'
cd /home/ubuntu/bank-statement-converter/frontend

echo "Checking signup.html uses auth-unified.js:"
grep -E "script.*auth" signup.html

echo -e "\nVerifying auth-unified.js exists:"
ls -la js/auth-unified.js || echo "WARNING: auth-unified.js not found!"

# Also ensure the register endpoint is correct in auth-unified.js
echo -e "\nChecking register endpoint in auth-unified.js:"
grep -A5 "async register" js/auth-unified.js | head -10
EOF

echo -e "\n✅ Signup page fix deployed!"
echo "================================"
echo "Test at: https://bankcsvconverter.com/signup.html"