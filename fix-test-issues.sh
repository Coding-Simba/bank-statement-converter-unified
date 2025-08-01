#\!/bin/bash

# 🔧 FIX TEST ISSUES
echo "🔧 FIXING IDENTIFIED ISSUES"
echo "=========================="
echo ""

SERVER_IP="3.235.19.83"
SERVER_USER="ubuntu"
SSH_KEY="/Users/MAC/Downloads/bank-statement-converter.pem"

ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no "$SERVER_USER@$SERVER_IP" << 'ENDSSH'
cd /home/ubuntu/bank-statement-converter

echo "1. Fixing login.html - auth script not included"
echo "----------------------------------------------"
# Check current state
echo "Current scripts in login.html:"
grep -E "\.js" login.html | grep -v "google\|recaptcha" | tail -5

# Add ultrathink-auth.js if missing
if \! grep -q "ultrathink-auth.js" login.html; then
    echo "Adding ultrathink-auth.js to login.html..."
    # Add before closing body tag
    sed -i '/<\/body>/i <script src="/js/ultrathink-auth.js"></script>' login.html
    echo "✅ Added ultrathink-auth.js"
else
    echo "✅ ultrathink-auth.js already present"
fi

echo -e "\n2. Checking backend health endpoint"
echo "-----------------------------------"
# Test locally first
curl -s http://localhost:5000/health && echo "✅ Backend responding locally" || echo "❌ Backend not responding"

# Check if it's accessible via domain
curl -s https://bankcsvconverter.com/api/health && echo "✅ API health endpoint working" || echo "⚠️  Using /health instead of /api/health"

echo -e "\n3. Testing login functionality directly"
echo "--------------------------------------"
# Test login with correct endpoint
LOGIN_TEST=$(curl -s -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test123"}')

if echo "$LOGIN_TEST" | grep -q "access_token"; then
    echo "✅ Backend login working"
    TOKEN=$(echo "$LOGIN_TEST" | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'][:50])...")
    echo "Token received: $TOKEN"
else
    echo "❌ Backend login failed"
    echo "$LOGIN_TEST"
fi

echo -e "\n4. Verifying all pages have auth script"
echo "---------------------------------------"
for page in login.html signup.html dashboard-modern.html pricing.html settings.html; do
    if [ -f "$page" ]; then
        echo -n "$page: "
        grep -q "ultrathink-auth.js\|auth-fixed.js" "$page" && echo "✅ Has auth script" || echo "❌ Missing auth script"
    fi
done

echo -e "\n5. Creating a simple working login page for testing"
echo "--------------------------------------------------"
cat > test-login-working.html << 'EOHTML'
<\!DOCTYPE html>
<html>
<head>
    <title>Working Login Test</title>
    <meta charset="UTF-8">
    <style>
        body { font-family: Arial, sans-serif; max-width: 400px; margin: 50px auto; padding: 20px; }
        input { width: 100%; padding: 10px; margin: 10px 0; box-sizing: border-box; }
        button { width: 100%; padding: 12px; background: #007bff; color: white; border: none; cursor: pointer; }
        button:hover { background: #0056b3; }
        button:disabled { background: #ccc; cursor: not-allowed; }
        .message { padding: 10px; margin: 10px 0; border-radius: 4px; }
        .error { background: #f8d7da; color: #721c24; }
        .success { background: #d4edda; color: #155724; }
    </style>
</head>
<body>
    <h1>Simple Working Login</h1>
    
    <form id="loginForm">
        <input type="email" id="email" placeholder="Email" value="test@example.com" required>
        <input type="password" id="password" placeholder="Password" value="test123" required>
        <button type="submit" id="loginBtn">Login</button>
    </form>
    
    <div id="message"></div>
    
    <script>
        // Direct login implementation - no dependencies
        document.getElementById('loginForm').onsubmit = async function(e) {
            e.preventDefault();
            
            const btn = document.getElementById('loginBtn');
            const msg = document.getElementById('message');
            
            btn.disabled = true;
            btn.textContent = 'Logging in...';
            msg.className = '';
            msg.textContent = '';
            
            try {
                const response = await fetch('/api/auth/login', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        email: document.getElementById('email').value,
                        password: document.getElementById('password').value,
                        remember_me: true
                    })
                });
                
                const data = await response.json();
                
                if (response.ok && data.access_token) {
                    // Store auth data
                    localStorage.setItem('access_token', data.access_token);
                    localStorage.setItem('user', JSON.stringify(data.user));
                    
                    msg.className = 'message success';
                    msg.textContent = 'Login successful\! Redirecting...';
                    
                    setTimeout(() => {
                        window.location.href = '/dashboard-modern.html';
                    }, 1000);
                } else {
                    throw new Error(data.detail || 'Login failed');
                }
            } catch (error) {
                msg.className = 'message error';
                msg.textContent = 'Error: ' + error.message;
                
                btn.disabled = false;
                btn.textContent = 'Login';
            }
        };
    </script>
</body>
</html>
EOHTML

echo "✅ Created test-login-working.html"

echo -e "\n6. Final verification"
echo "--------------------"
echo "Auth scripts available:"
ls -la js/*.js | grep -E "auth|ultra" | grep -v "[0-9]{10}" | awk '{print $9}'

echo -e "\n✅ FIXES APPLIED\!"
echo ""
echo "Test these URLs:"
echo "1. Simple working login: https://bankcsvconverter.com/test-login-working.html"
echo "2. Main login page: https://bankcsvconverter.com/login.html"
echo "3. Test suite: https://bankcsvconverter.com/ultrathink-test.html"

ENDSSH
