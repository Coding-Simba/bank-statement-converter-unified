#!/bin/bash

SERVER_IP="3.235.19.83"
KEY_PATH="/Users/MAC/Downloads/bank-statement-converter.pem"
SERVER_USER="ubuntu"

echo "Deploying Force Auth Storage Fix"
echo "================================"

# First, let's fix the permissions issue
echo "1. Fixing permissions..."
ssh -i "$KEY_PATH" "$SERVER_USER@$SERVER_IP" "sudo chown -R ubuntu:ubuntu /home/ubuntu/bank-statement-converter/frontend/js/"

# Deploy force-auth-storage.js
echo "2. Deploying force-auth-storage.js..."
scp -i "$KEY_PATH" js/force-auth-storage.js "$SERVER_USER@$SERVER_IP:/home/ubuntu/bank-statement-converter/frontend/js/"

# Update login.html to add this script FIRST (before other auth scripts)
echo "3. Updating login.html..."
ssh -i "$KEY_PATH" "$SERVER_USER@$SERVER_IP" << 'EOF'
cd /home/ubuntu/bank-statement-converter/frontend

# Add force-auth-storage.js as the first script after api-config
if ! grep -q "force-auth-storage.js" login.html; then
    # Insert after api-config.js
    sed -i '/<script src="\/js\/api-config\.js"><\/script>/a\    <script src="/js/force-auth-storage.js"></script>' login.html
fi

echo "Login page updated"
EOF

# Also add to pricing page for debugging
echo "4. Adding simple auth check to pricing..."
cat > /tmp/auth-check-inline.txt << 'SCRIPT'
    <script>
        // Quick auth check
        console.log('[Inline Check] Auth state on pricing page:');
        console.log('  access_token:', localStorage.getItem('access_token') ? 'EXISTS' : 'MISSING');
        console.log('  user_data:', localStorage.getItem('user_data') ? 'EXISTS' : 'MISSING');
    </script>
SCRIPT

scp -i "$KEY_PATH" /tmp/auth-check-inline.txt "$SERVER_USER@$SERVER_IP:/tmp/"

ssh -i "$KEY_PATH" "$SERVER_USER@$SERVER_IP" << 'EOF'
cd /home/ubuntu/bank-statement-converter/frontend

# Add inline script to pricing page for debugging
if ! grep -q "Inline Check" pricing.html; then
    sed -i '/<body>/r /tmp/auth-check-inline.txt' pricing.html
fi

rm /tmp/auth-check-inline.txt
echo "Pricing page updated with auth check"
EOF

rm /tmp/auth-check-inline.txt

echo -e "\n✅ Force auth storage deployed!"
echo "==============================="
echo "This fix:"
echo "1. Intercepts login API responses"
echo "2. Forces storage of tokens in localStorage"
echo "3. Checks for redirect URL after storing tokens"
echo "4. Adds auth state logging to pricing page"
echo ""
echo "Try the flow again and check console for [Force Auth] messages!"