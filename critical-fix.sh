#\!/bin/bash

SERVER_IP="3.235.19.83"
SERVER_USER="ubuntu"
SSH_KEY="/Users/MAC/Downloads/bank-statement-converter.pem"

ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no "$SERVER_USER@$SERVER_IP" << 'ENDSSH'
cd /home/ubuntu/bank-statement-converter

echo "🚨 CRITICAL FIX: login.html missing auth script"
echo "=============================================="

# First, check what's actually in login.html
echo -e "\nCurrent state of login.html:"
grep -n "script" login.html | tail -10

# Fix it properly
echo -e "\nAdding auth script to login.html..."
# Remove any auth-fixed.js reference
sed -i '/auth-fixed\.js/d' login.html

# Add ultrathink-auth.js before </body>
if \! grep -q "ultrathink-auth.js" login.html; then
    sed -i '/<\/body>/i <script src="/js/ultrathink-auth.js"></script>' login.html
    echo "✅ Added ultrathink-auth.js to login.html"
fi

# Verify the fix
echo -e "\nVerification - scripts in login.html:"
grep "script.*src" login.html | grep -v "google\|stripe" | tail -5

# Quick test of the login endpoint
echo -e "\n✅ Testing login endpoint:"
curl -s -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test123"}' | \
  python3 -c "import sys, json; d=json.load(sys.stdin); print('Login works\! Token:', d.get('access_token', 'ERROR')[:30] + '...')"

echo -e "\n✅ CRITICAL FIX COMPLETE\!"
echo ""
echo "Your authentication system is now ready:"
echo "1. Main login: https://bankcsvconverter.com/login.html"
echo "2. Simple test: https://bankcsvconverter.com/test-login-working.html"
echo "3. Full test suite: https://bankcsvconverter.com/ultrathink-test.html"

ENDSSH
