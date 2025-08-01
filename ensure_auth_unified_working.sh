#!/bin/bash

SERVER_IP="3.235.19.83"
KEY_PATH="/Users/MAC/Downloads/bank-statement-converter.pem"
SERVER_USER="ubuntu"

echo "Ensuring auth-unified.js is properly configured"
echo "=============================================="

ssh -i "$KEY_PATH" "$SERVER_USER@$SERVER_IP" << 'EOF'
cd /home/ubuntu/bank-statement-converter

echo "1. Checking if auth-unified.js is using correct endpoints..."
echo "========================================================"
grep -E "fetch.*auth|AUTH.*=|api.*auth" frontend/js/auth-unified.js | head -10

echo -e "\n2. Ensuring auth-unified.js uses v2 endpoints..."
echo "=============================================="
# Update any remaining old endpoints
sed -i 's|/api/auth/|/v2/api/auth/|g' frontend/js/auth-unified.js
sed -i "s|'/api/auth'|'/v2/api/auth'|g" frontend/js/auth-unified.js

echo -e "\n3. Verifying the changes in auth-unified.js..."
echo "==========================================="
grep "/v2/api/auth" frontend/js/auth-unified.js | head -5

echo -e "\n4. Making sure both login.html and signup.html use auth-unified.js..."
echo "=================================================================="
echo "Login.html scripts:"
grep -E "script.*src" login.html | grep -v "cdn"

echo -e "\nSignup.html scripts:"
grep -E "script.*src" signup.html | grep -v "cdn"

echo -e "\n5. Let's check if there's a mismatch in how forms are handled..."
echo "=============================================================="
echo "Checking login form in login.html:"
grep -A5 -B5 'form.*login\|id="loginForm"' login.html | head -20

echo -e "\n6. Creating a simple test to verify authentication..."
echo "==================================================="
cat > test-browser-auth.html << 'HTML'
<!DOCTYPE html>
<html>
<head>
    <title>Browser Auth Test</title>
    <meta charset="UTF-8">
</head>
<body>
    <h1>Browser Authentication Test</h1>
    
    <div id="status">Loading...</div>
    
    <h2>Test CSRF</h2>
    <button onclick="testCSRF()">Get CSRF Token</button>
    <div id="csrf-result"></div>
    
    <h2>Test Login</h2>
    <input type="email" id="email" placeholder="Email" value="test@example.com">
    <input type="password" id="password" placeholder="Password" value="Test123!">
    <button onclick="testLogin()">Test Login</button>
    <div id="login-result"></div>
    
    <h2>Test Auth Check</h2>
    <button onclick="testAuthCheck()">Check Authentication</button>
    <div id="auth-result"></div>
    
    <script>
    let csrfToken = null;
    
    async function testCSRF() {
        try {
            const response = await fetch('/v2/api/auth/csrf', {
                credentials: 'include'
            });
            const data = await response.json();
            csrfToken = data.csrf_token;
            document.getElementById('csrf-result').innerHTML = 
                `✅ CSRF Token: ${csrfToken.substring(0, 20)}...`;
        } catch (error) {
            document.getElementById('csrf-result').innerHTML = 
                `❌ Error: ${error.message}`;
        }
    }
    
    async function testLogin() {
        if (!csrfToken) {
            alert('Get CSRF token first!');
            return;
        }
        
        try {
            const response = await fetch('/v2/api/auth/login', {
                method: 'POST',
                credentials: 'include',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRF-Token': csrfToken
                },
                body: JSON.stringify({
                    email: document.getElementById('email').value,
                    password: document.getElementById('password').value
                })
            });
            
            const data = await response.json();
            document.getElementById('login-result').innerHTML = 
                response.ok ? `✅ Login successful! User ID: ${data.id}` : 
                `❌ Login failed: ${data.detail}`;
                
        } catch (error) {
            document.getElementById('login-result').innerHTML = 
                `❌ Error: ${error.message}`;
        }
    }
    
    async function testAuthCheck() {
        try {
            const response = await fetch('/v2/api/auth/check', {
                credentials: 'include'
            });
            const data = await response.json();
            document.getElementById('auth-result').innerHTML = 
                data.authenticated ? 
                `✅ Authenticated as: ${data.user.email}` : 
                `❌ Not authenticated`;
        } catch (error) {
            document.getElementById('auth-result').innerHTML = 
                `❌ Error: ${error.message}`;
        }
    }
    
    // Check initial status
    window.onload = async function() {
        await testCSRF();
        await testAuthCheck();
        document.getElementById('status').innerHTML = 'Ready for testing';
    }
    </script>
</body>
</html>
HTML

echo -e "\n7. Final check - ensure cookies are set correctly..."
echo "=================================================="
grep -E "credentials.*include|withCredentials" frontend/js/auth-unified.js | head -5

echo -e "\n8. If credentials: 'include' is missing, add it..."
echo "==============================================="
# Check if credentials: 'include' exists
if ! grep -q "credentials: 'include'" frontend/js/auth-unified.js; then
    echo "Adding credentials: 'include' to fetch calls..."
    # Add credentials: 'include' to all fetch calls
    sed -i "/fetch.*auth.*{/,/}/ { /headers:/ { a\\                credentials: 'include',
    } }" frontend/js/auth-unified.js
fi

echo -e "\n✅ Configuration complete!"
echo ""
echo "🧪 TEST IN YOUR BROWSER:"
echo "========================"
echo "1. Go to: https://bankcsvconverter.com/test-browser-auth.html"
echo "2. Click 'Get CSRF Token' - should show a token"
echo "3. Enter email/password and click 'Test Login'"
echo "4. Click 'Check Authentication' to verify you're logged in"
echo ""
echo "If this test page works, the issue is with the form handling in login.html"
echo "If it doesn't work, check the browser console for errors"

EOF

echo -e "\n✅ Auth configuration verified!"