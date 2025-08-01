#!/bin/bash

# Create Diagnostic Page
echo "🔍 Creating Diagnostic Page"
echo "=========================="
echo ""

SERVER_IP="3.235.19.83"
SERVER_USER="ubuntu"
SSH_KEY="/Users/MAC/Downloads/bank-statement-converter.pem"

# Create via SSH
ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no "$SERVER_USER@$SERVER_IP" << 'ENDSSH'
cd /home/ubuntu/bank-statement-converter

cat > diagnostic.html << 'EOF'
<!DOCTYPE html>
<html>
<head>
    <title>System Diagnostic</title>
    <style>
        body { font-family: Arial, sans-serif; padding: 20px; max-width: 1200px; margin: 0 auto; }
        .test { margin: 20px 0; padding: 20px; border: 1px solid #ddd; border-radius: 8px; }
        .success { background: #d4edda; border-color: #c3e6cb; }
        .error { background: #f8d7da; border-color: #f5c6cb; }
        .info { background: #d1ecf1; border-color: #bee5eb; }
        pre { background: #f4f4f4; padding: 10px; overflow-x: auto; }
        button { padding: 10px 20px; margin: 5px; cursor: pointer; }
    </style>
</head>
<body>
    <h1>🔍 Bank CSV Converter - System Diagnostic</h1>
    
    <div id="diagnostics"></div>
    
    <script>
        const API_BASE = 'https://bankcsvconverter.com';
        const diagnostics = document.getElementById('diagnostics');
        
        function addTest(title, status, details) {
            const div = document.createElement('div');
            div.className = `test ${status}`;
            div.innerHTML = `
                <h3>${title}</h3>
                <pre>${details}</pre>
            `;
            diagnostics.appendChild(div);
        }
        
        async function runDiagnostics() {
            diagnostics.innerHTML = '';
            
            // Test 1: Check if we can reach the API
            try {
                const start = Date.now();
                const response = await fetch(`${API_BASE}/health`);
                const time = Date.now() - start;
                
                if (response.ok) {
                    addTest('API Health Check', 'success', `✅ API is reachable\nResponse time: ${time}ms\nStatus: ${response.status}`);
                } else {
                    addTest('API Health Check', 'error', `❌ API returned error\nStatus: ${response.status}\nResponse time: ${time}ms`);
                }
            } catch (error) {
                addTest('API Health Check', 'error', `❌ Cannot reach API\nError: ${error.message}`);
            }
            
            // Test 2: Check authentication endpoint
            try {
                const response = await fetch(`${API_BASE}/api/auth/login`, {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({email: 'test@example.com', password: 'test123'})
                });
                
                const data = await response.json();
                
                if (response.ok && data.access_token) {
                    addTest('Authentication API', 'success', `✅ Login endpoint working\nToken received: ${data.access_token.substring(0, 50)}...\nUser: ${data.user.email}`);
                    
                    // Store for next tests
                    window.testToken = data.access_token;
                } else {
                    addTest('Authentication API', 'error', `❌ Login failed\nStatus: ${response.status}\nResponse: ${JSON.stringify(data, null, 2)}`);
                }
            } catch (error) {
                addTest('Authentication API', 'error', `❌ Login request failed\nError: ${error.message}`);
            }
            
            // Test 3: Check Stripe endpoint with auth
            if (window.testToken) {
                try {
                    const response = await fetch(`${API_BASE}/api/stripe/create-checkout-session`, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'Authorization': `Bearer ${window.testToken}`
                        },
                        body: JSON.stringify({price_id: 'price_1RqZtaKwQLBjGTW9w20V3Hst'})
                    });
                    
                    const data = await response.json();
                    
                    if (response.ok && data.checkout_url) {
                        addTest('Stripe Integration', 'success', `✅ Stripe endpoint working\nCheckout URL: ${data.checkout_url.substring(0, 80)}...`);
                    } else {
                        addTest('Stripe Integration', 'error', `❌ Stripe request failed\nStatus: ${response.status}\nResponse: ${JSON.stringify(data, null, 2)}`);
                    }
                } catch (error) {
                    addTest('Stripe Integration', 'error', `❌ Stripe request error\nError: ${error.message}`);
                }
            }
            
            // Test 4: Check JavaScript environment
            addTest('JavaScript Environment', 'info', `
Browser: ${navigator.userAgent}
Current URL: ${window.location.href}
LocalStorage available: ${typeof(Storage) !== "undefined" ? "Yes" : "No"}
Cookies enabled: ${navigator.cookieEnabled ? "Yes" : "No"}
            `.trim());
            
            // Test 5: Check for UnifiedAuth
            setTimeout(() => {
                if (typeof UnifiedAuth !== 'undefined') {
                    addTest('UnifiedAuth Module', 'success', '✅ UnifiedAuth is loaded');
                } else {
                    addTest('UnifiedAuth Module', 'error', '❌ UnifiedAuth is NOT loaded\nThis means the auth JavaScript file is not loading properly');
                }
            }, 1000);
        }
        
        // Run diagnostics on load
        window.onload = runDiagnostics;
    </script>
    
    <hr>
    <button onclick="runDiagnostics()">🔄 Run Diagnostics Again</button>
    <button onclick="window.location.href='/simple-login.html'">Go to Simple Login</button>
    <button onclick="window.location.href='/login.html'">Go to Main Login</button>
</body>
</html>
EOF

echo "Diagnostic page created!"

ENDSSH

echo ""
echo "✅ Diagnostic page created!"
echo ""
echo "Please go to: https://bankcsvconverter.com/diagnostic.html"
echo ""
echo "This will show you:"
echo "- If the API is reachable"
echo "- If authentication is working"
echo "- If Stripe integration is working"
echo "- Browser environment details"
echo "- Whether JavaScript modules are loading"