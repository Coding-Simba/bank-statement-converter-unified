#!/bin/bash

# Debug Frontend Issue
echo "🔍 Debugging Frontend Issue"
echo "=========================="
echo ""

SERVER_IP="3.235.19.83"
SERVER_USER="ubuntu"
SSH_KEY="/Users/MAC/Downloads/bank-statement-converter.pem"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Check SSH key
if [ ! -f "$SSH_KEY" ]; then
    echo -e "${RED}✗ SSH key not found at $SSH_KEY${NC}"
    exit 1
fi

# Debug via SSH
ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no "$SERVER_USER@$SERVER_IP" << 'ENDSSH'

echo "1. Checking which auth script is actually being served..."
cd /home/ubuntu/bank-statement-converter
echo "In login.html:"
grep -n "auth-unified" login.html | head -5

echo -e "\nIn pricing.html:"
grep -n "auth-unified" pricing.html | head -5

echo -e "\n2. Checking if the auth script exists..."
ls -la js/auth-unified-*.js | tail -5

echo -e "\n3. Checking for JavaScript syntax errors in the auth file..."
# Get the latest auth file
LATEST_AUTH=$(ls -t js/auth-unified-*.js | head -1)
echo "Checking $LATEST_AUTH for syntax issues..."

# Check for common syntax errors
echo -e "\nChecking for duplicate headers declarations:"
grep -n "headers:" "$LATEST_AUTH" | head -10

echo -e "\nChecking makeAuthenticatedRequest method:"
sed -n '/makeAuthenticatedRequest/,/^[[:space:]]*}/p' "$LATEST_AUTH" | head -50

echo -e "\n4. Checking if there are any console errors in nginx logs..."
sudo tail -20 /var/log/nginx/error.log

echo -e "\n5. Creating a simple test page..."
cat > test-auth.html << 'EOF'
<!DOCTYPE html>
<html>
<head>
    <title>Auth Test</title>
</head>
<body>
    <h1>Auth System Test</h1>
    <div id="status">Loading...</div>
    <button onclick="testLogin()">Test Login</button>
    <div id="result"></div>
    
    <script>
        const API_BASE = 'https://bankcsvconverter.com';
        
        async function testLogin() {
            const statusEl = document.getElementById('status');
            const resultEl = document.getElementById('result');
            
            try {
                statusEl.textContent = 'Testing login...';
                
                const response = await fetch(`${API_BASE}/api/auth/login`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        email: 'test@example.com',
                        password: 'test123'
                    })
                });
                
                const data = await response.json();
                
                if (response.ok) {
                    statusEl.textContent = '✅ Login successful!';
                    resultEl.textContent = JSON.stringify(data, null, 2);
                    
                    // Test Stripe
                    testStripe(data.access_token);
                } else {
                    statusEl.textContent = '❌ Login failed';
                    resultEl.textContent = JSON.stringify(data, null, 2);
                }
            } catch (error) {
                statusEl.textContent = '❌ Error occurred';
                resultEl.textContent = error.toString();
            }
        }
        
        async function testStripe(token) {
            try {
                const response = await fetch(`${API_BASE}/api/stripe/create-checkout-session`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${token}`
                    },
                    body: JSON.stringify({
                        price_id: 'price_1RqZtaKwQLBjGTW9w20V3Hst'
                    })
                });
                
                const data = await response.json();
                console.log('Stripe response:', data);
                
                if (data.checkout_url) {
                    const link = document.createElement('a');
                    link.href = data.checkout_url;
                    link.textContent = 'Go to Stripe Checkout';
                    link.target = '_blank';
                    document.getElementById('result').appendChild(link);
                }
            } catch (error) {
                console.error('Stripe error:', error);
            }
        }
        
        // Check if auth script loaded
        setTimeout(() => {
            const status = document.getElementById('status');
            if (typeof UnifiedAuth === 'undefined') {
                status.textContent = '⚠️ UnifiedAuth not loaded';
            } else {
                status.textContent = '✅ UnifiedAuth loaded';
            }
        }, 1000);
    </script>
</body>
</html>
EOF

echo -e "\n6. Checking recent access patterns..."
echo "Recent requests to auth endpoints:"
sudo tail -50 /var/log/nginx/access.log | grep -E "(auth|stripe)" | tail -10

ENDSSH

echo ""
echo -e "${GREEN}✓ Debug complete!${NC}"
echo ""
echo "Test page created at: https://bankcsvconverter.com/test-auth.html"
echo "This simple page will help identify if the issue is with the auth script or something else."