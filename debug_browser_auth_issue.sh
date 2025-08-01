#!/bin/bash

SERVER_IP="3.235.19.83"
KEY_PATH="/Users/MAC/Downloads/bank-statement-converter.pem"
SERVER_USER="ubuntu"

echo "Debugging browser authentication issues"
echo "======================================"

ssh -i "$KEY_PATH" "$SERVER_USER@$SERVER_IP" << 'EOF'

echo "1. Checking what auth scripts are actually being loaded..."
echo "======================================================"
cd /home/ubuntu/bank-statement-converter

# Check login.html
echo "Login page scripts:"
grep -E "\.js\"|auth" login.html | grep -v "cdn.jsdelivr" | head -10

echo -e "\nSignup page scripts:"
grep -E "\.js\"|auth" signup.html | grep -v "cdn.jsdelivr" | head -10

echo -e "\n2. Checking if auth-unified.js exists and is accessible..."
echo "========================================================"
ls -la js/auth-unified.js 2>/dev/null || echo "auth-unified.js not found in /js/"
ls -la frontend/js/auth-unified.js 2>/dev/null || echo "auth-unified.js not found in /frontend/js/"

echo -e "\n3. Checking what auth scripts are actually in use..."
echo "=================================================="
find . -name "*.html" -type f -exec grep -l "auth.*\.js" {} \; | grep -v node_modules | head -10

echo -e "\n4. Testing if JavaScript files are accessible via browser..."
echo "=========================================================="
curl -sI https://bankcsvconverter.com/js/auth-service.js | head -5
curl -sI https://bankcsvconverter.com/js/auth.js | head -5
curl -sI https://bankcsvconverter.com/js/auth-unified.js | head -5

echo -e "\n5. Checking the actual auth endpoint being called..."
echo "=================================================="
# Look for API calls in the JavaScript files
echo "Checking auth.js for API endpoints:"
grep -E "fetch.*auth|api.*auth" frontend/js/auth.js 2>/dev/null | head -5 || echo "No auth.js found"

echo -e "\nChecking auth-service.js for API endpoints:"
grep -E "fetch.*auth|api.*auth" frontend/js/auth-service.js 2>/dev/null | head -5

echo -e "\n6. Checking CORS configuration..."
echo "================================"
cd backend
grep -r "CORS\|cors\|allow_origin" --include="*.py" . | head -10

echo -e "\n7. Checking browser console errors by looking at nginx logs..."
echo "==========================================================="
echo "Recent 404 errors:"
sudo tail -50 /var/log/nginx/access.log | grep " 404 " | grep -v "favicon" | tail -10

echo -e "\n8. Checking if cookies are being set with correct domain..."
echo "========================================================"
grep -r "set_cookie\|domain=" --include="*.py" api/ | grep -v __pycache__ | head -10

echo -e "\n9. Testing the actual login form submission..."
echo "==========================================="
# Create a simple test HTML file to check
cat > /home/ubuntu/bank-statement-converter/test-auth.html << 'HTML'
<!DOCTYPE html>
<html>
<head>
    <title>Auth Test</title>
</head>
<body>
    <h1>Authentication Test</h1>
    <button onclick="testAuth()">Test Auth</button>
    <div id="result"></div>
    
    <script>
    async function testAuth() {
        const resultDiv = document.getElementById('result');
        
        // Test CSRF
        try {
            const csrfResp = await fetch('/v2/api/auth/csrf');
            const csrfData = await csrfResp.json();
            resultDiv.innerHTML += `<p>CSRF: ${JSON.stringify(csrfData)}</p>`;
            
            // Test login
            const loginResp = await fetch('/v2/api/auth/login', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRF-Token': csrfData.csrf_token
                },
                credentials: 'include',
                body: JSON.stringify({
                    email: 'test@example.com',
                    password: 'Test123!'
                })
            });
            const loginData = await loginResp.json();
            resultDiv.innerHTML += `<p>Login: ${JSON.stringify(loginData)}</p>`;
            
        } catch (err) {
            resultDiv.innerHTML += `<p>Error: ${err.message}</p>`;
        }
    }
    </script>
</body>
</html>
HTML

echo -e "\n10. Let's check the actual JavaScript being used on login page..."
echo "=============================================================="
# Get the actual content of the auth JavaScript
echo "First 50 lines of auth.js being used:"
head -50 frontend/js/auth.js 2>/dev/null | grep -E "function|fetch|api" || echo "auth.js not found"

EOF

echo -e "\n✅ Debug information collected!"
echo ""
echo "📝 To test in your browser:"
echo "1. Open Chrome DevTools (F12)"
echo "2. Go to Network tab"
echo "3. Try to log in"
echo "4. Look for any red (failed) requests"
echo "5. Check Console tab for JavaScript errors"
echo ""
echo "You can also test: https://bankcsvconverter.com/test-auth.html"