#!/bin/bash

# 🧠 ULTRATHINK AUTH DEPLOYMENT SCRIPT
echo "🧠 DEPLOYING ULTRATHINK AUTHENTICATION SYSTEM"
echo "============================================="
echo ""

SERVER_IP="3.235.19.83"
SERVER_USER="ubuntu"
SSH_KEY="/Users/MAC/Downloads/bank-statement-converter.pem"

# First, upload the new auth script
echo "1. Uploading ULTRATHINK auth script..."
scp -i "$SSH_KEY" -o StrictHostKeyChecking=no \
    /Users/MAC/chrome/bank-statement-converter-unified/js/auth-unified-ultrathink.js \
    "$SERVER_USER@$SERVER_IP:/home/ubuntu/bank-statement-converter/js/"

# Now update all HTML files via SSH
ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no "$SERVER_USER@$SERVER_IP" << 'ENDSSH'
cd /home/ubuntu/bank-statement-converter

echo -e "\n2. Backing up current auth files..."
cp js/auth-unified.js js/auth-unified.backup.$(date +%s).js 2>/dev/null || true

echo -e "\n3. Updating all HTML files to use ULTRATHINK auth..."

# List of HTML files to update
HTML_FILES=(
    "index.html"
    "login.html"
    "signup.html"
    "dashboard-modern.html"
    "settings.html"
    "pricing.html"
    "convert-pdf.html"
    "merge-statements.html"
    "split-by-date.html"
    "analyze-transactions.html"
    "blog.html"
    "business.html"
    "about.html"
    "contact.html"
    "help.html"
    "faq.html"
    "privacy.html"
    "terms.html"
    "security.html"
)

for file in "${HTML_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "Updating $file..."
        
        # Remove all existing auth script references
        sed -i '/<script.*auth.*\.js.*<\/script>/d' "$file"
        
        # Remove inline auth scripts
        sed -i '/<script>.*UnifiedAuth.*<\/script>/d' "$file"
        
        # Add ULTRATHINK auth script before closing body tag
        sed -i '/<\/body>/i <script src="/js/auth-unified-ultrathink.js"></script>' "$file"
        
        echo "✅ Updated $file"
    fi
done

echo -e "\n4. Creating a test page to verify auth persistence..."
cat > ultrathink-auth-test.html << 'EOF'
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ULTRATHINK Auth Test</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #f5f7fa;
            padding: 40px;
            max-width: 800px;
            margin: 0 auto;
        }
        .test-container {
            background: white;
            border-radius: 12px;
            padding: 40px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.1);
        }
        h1 {
            color: #1a1a1a;
            margin-bottom: 30px;
        }
        .status-card {
            background: #f8f9fa;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 20px;
        }
        .status-card h3 {
            margin-top: 0;
            color: #333;
        }
        .success {
            color: #22c55e;
        }
        .error {
            color: #ef4444;
        }
        .info {
            color: #3b82f6;
        }
        .test-button {
            background: #4a90e2;
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 8px;
            font-size: 16px;
            cursor: pointer;
            margin-right: 10px;
            margin-top: 10px;
        }
        .test-button:hover {
            background: #357abd;
        }
        pre {
            background: #f1f5f9;
            padding: 12px;
            border-radius: 6px;
            overflow-x: auto;
        }
    </style>
</head>
<body>
    <div class="test-container">
        <h1>🧠 ULTRATHINK Auth System Test</h1>
        
        <div class="status-card">
            <h3>Authentication Status</h3>
            <p>Logged In: <span id="authStatus" class="info">Checking...</span></p>
            <p>User Email: <span id="userEmail" class="info">-</span></p>
            <p>Token Storage: <span id="tokenStorage" class="info">-</span></p>
        </div>
        
        <div class="status-card">
            <h3>Storage Contents</h3>
            <pre id="storageContents">Loading...</pre>
        </div>
        
        <div class="status-card">
            <h3>Test Actions</h3>
            <button class="test-button" onclick="checkAuth()">Check Auth Status</button>
            <button class="test-button" onclick="testLogin()">Test Login</button>
            <button class="test-button" onclick="testLogout()">Test Logout</button>
            <button class="test-button" onclick="navigatePages()">Test Page Navigation</button>
            <button class="test-button" onclick="clearAllStorage()">Clear All Storage</button>
        </div>
        
        <div class="status-card">
            <h3>Test Results</h3>
            <div id="testResults"></div>
        </div>
    </div>
    
    <script src="/js/auth-unified-ultrathink.js"></script>
    <script>
        function updateStatus() {
            const auth = window.UltraThinkAuth;
            const isAuth = auth && auth.isAuthenticated();
            const user = auth && auth.getUser();
            
            document.getElementById('authStatus').textContent = isAuth ? 'Yes ✅' : 'No ❌';
            document.getElementById('authStatus').className = isAuth ? 'success' : 'error';
            document.getElementById('userEmail').textContent = user ? user.email : '-';
            
            // Check token storage
            const hasLocalToken = !!localStorage.getItem('access_token');
            const hasSessionToken = !!sessionStorage.getItem('access_token');
            let storage = 'None';
            if (hasLocalToken) storage = 'localStorage';
            if (hasSessionToken) storage = 'sessionStorage';
            if (hasLocalToken && hasSessionToken) storage = 'Both';
            document.getElementById('tokenStorage').textContent = storage;
            
            // Show storage contents
            const storageData = {
                localStorage: {
                    access_token: localStorage.getItem('access_token') ? '***exists***' : null,
                    user: localStorage.getItem('user')
                },
                sessionStorage: {
                    access_token: sessionStorage.getItem('access_token') ? '***exists***' : null,
                    user: sessionStorage.getItem('user')
                }
            };
            document.getElementById('storageContents').textContent = JSON.stringify(storageData, null, 2);
        }
        
        function addResult(message, type = 'info') {
            const results = document.getElementById('testResults');
            const result = document.createElement('p');
            result.className = type;
            result.textContent = `[${new Date().toLocaleTimeString()}] ${message}`;
            results.appendChild(result);
        }
        
        async function checkAuth() {
            addResult('Checking authentication status...');
            updateStatus();
            
            if (window.UltraThinkAuth) {
                const verified = await window.UltraThinkAuth.verifyAuth();
                addResult(`Auth verification result: ${verified}`, verified ? 'success' : 'error');
            }
        }
        
        async function testLogin() {
            addResult('Testing login with test credentials...');
            
            try {
                const response = await fetch('/api/auth/login', {
                    method: 'POST',
                    credentials: 'include',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        email: 'test@example.com',
                        password: 'test123',
                        remember_me: true
                    })
                });
                
                const data = await response.json();
                
                if (response.ok && data.access_token) {
                    localStorage.setItem('access_token', data.access_token);
                    localStorage.setItem('user', JSON.stringify(data.user));
                    window.UltraThinkAuth.loadUserFromStorage();
                    window.UltraThinkAuth.updateNavbar();
                    addResult('Login successful!', 'success');
                    updateStatus();
                } else {
                    addResult(`Login failed: ${data.detail}`, 'error');
                }
            } catch (error) {
                addResult(`Login error: ${error.message}`, 'error');
            }
        }
        
        function testLogout() {
            addResult('Testing logout...');
            if (window.UltraThinkAuth) {
                window.UltraThinkAuth.logout();
                addResult('Logout initiated', 'success');
            }
        }
        
        function navigatePages() {
            addResult('Opening multiple pages to test auth persistence...');
            window.open('/', '_blank');
            window.open('/pricing.html', '_blank');
            window.open('/dashboard-modern.html', '_blank');
            addResult('Check if auth state persists across all pages', 'info');
        }
        
        function clearAllStorage() {
            localStorage.clear();
            sessionStorage.clear();
            addResult('All storage cleared', 'success');
            updateStatus();
        }
        
        // Listen for auth state changes
        window.addEventListener('ultrathink-auth-ready', (e) => {
            addResult('ULTRATHINK Auth ready!', 'success');
            updateStatus();
        });
        
        // Initial status update
        setTimeout(updateStatus, 100);
        setInterval(updateStatus, 5000);
    </script>
</body>
</html>
EOF

echo -e "\n5. Ensuring backend is running..."
if ! pgrep -f "uvicorn" > /dev/null; then
    cd /home/ubuntu/backend
    nohup python3 -m uvicorn main:app --host 0.0.0.0 --port 5000 > backend.log 2>&1 &
    sleep 3
    echo "✅ Backend started"
else
    echo "✅ Backend already running"
fi

echo -e "\n✅ ULTRATHINK AUTH SYSTEM DEPLOYED!"
echo "===================================="
echo ""
echo "The authentication system now:"
echo "- ✅ Persists login state across all pages"
echo "- ✅ Dynamically updates navbar to show logged-in state"
echo "- ✅ Handles cross-tab synchronization"
echo "- ✅ Automatically verifies auth status"
echo "- ✅ Shows user dropdown when logged in"
echo ""
echo "Test the system at:"
echo "https://bankcsvconverter.com/ultrathink-auth-test.html"

ENDSSH

echo ""
echo "🧠 ULTRATHINK deployment complete!"