#!/bin/bash

# Debug JS Loading V2
echo "🔍 Debugging JavaScript Loading V2"
echo "================================="
echo ""

SERVER_IP="3.235.19.83"
SERVER_USER="ubuntu"
SSH_KEY="/Users/MAC/Downloads/bank-statement-converter.pem"

# Debug via SSH
ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no "$SERVER_USER@$SERVER_IP" << 'ENDSSH'
cd /home/ubuntu/bank-statement-converter

echo "1. Checking what auth script diagnostic.html is trying to load..."
grep -n "auth-unified" diagnostic.html

echo -e "\n2. Updating diagnostic.html to load the correct auth script..."
# Get the latest auth script
LATEST_AUTH=$(ls -t js/auth-unified-*.js | head -1 | xargs basename)
echo "Latest auth script: $LATEST_AUTH"

# Update diagnostic.html to include the auth script
if ! grep -q "auth-unified" diagnostic.html; then
    echo "Adding auth script to diagnostic.html..."
    sed -i '/<\/head>/i <script src="/js/'$LATEST_AUTH'"></script>' diagnostic.html
else
    echo "Updating existing auth script reference..."
    sed -i "s|/js/auth-unified-[0-9]*\.js|/js/$LATEST_AUTH|g" diagnostic.html
fi

echo -e "\n3. Creating a test page that explicitly loads and tests UnifiedAuth..."
cat > test-unified-auth.html << 'EOF'
<!DOCTYPE html>
<html>
<head>
    <title>Test UnifiedAuth Loading</title>
    <style>
        body { font-family: Arial, sans-serif; padding: 40px; }
        .status { padding: 20px; margin: 10px 0; border-radius: 8px; }
        .success { background: #d4edda; border: 1px solid #c3e6cb; }
        .error { background: #f8d7da; border: 1px solid #f5c6cb; }
        .info { background: #d1ecf1; border: 1px solid #bee5eb; }
    </style>
</head>
<body>
    <h1>UnifiedAuth Loading Test</h1>
    
    <div id="loading" class="status info">Loading UnifiedAuth...</div>
    
    <div id="results"></div>
    
    <!-- Load the latest auth script -->
    <script src="/js/auth-unified-1754076923.js"></script>
    
    <script>
        const resultsDiv = document.getElementById('results');
        const loadingDiv = document.getElementById('loading');
        
        function addResult(message, isSuccess) {
            const div = document.createElement('div');
            div.className = `status ${isSuccess ? 'success' : 'error'}`;
            div.textContent = message;
            resultsDiv.appendChild(div);
        }
        
        // Check immediately
        setTimeout(() => {
            loadingDiv.style.display = 'none';
            
            if (typeof UnifiedAuth !== 'undefined') {
                addResult('✅ UnifiedAuth is defined!', true);
                
                // Check properties
                if (UnifiedAuth.initialized !== undefined) {
                    addResult(`✅ UnifiedAuth.initialized = ${UnifiedAuth.initialized}`, true);
                }
                
                if (typeof UnifiedAuth.login === 'function') {
                    addResult('✅ UnifiedAuth.login is a function', true);
                }
                
                if (typeof UnifiedAuth.isAuthenticated === 'function') {
                    addResult(`✅ UnifiedAuth.isAuthenticated() = ${UnifiedAuth.isAuthenticated()}`, true);
                }
                
                // Try to get user
                const user = UnifiedAuth.getUser();
                if (user) {
                    addResult(`✅ User found: ${user.email}`, true);
                } else {
                    addResult('ℹ️ No user logged in', true);
                }
                
                // Add login test button
                const button = document.createElement('button');
                button.textContent = 'Test Login';
                button.style.margin = '20px 0';
                button.onclick = async () => {
                    const result = await UnifiedAuth.login('test@example.com', 'test123');
                    if (result.success) {
                        addResult('✅ Login successful!', true);
                        window.location.href = '/pricing.html';
                    } else {
                        addResult(`❌ Login failed: ${result.error}`, false);
                    }
                };
                resultsDiv.appendChild(button);
                
            } else {
                addResult('❌ UnifiedAuth is NOT defined', false);
                
                // Check for errors
                if (window.console && window.console.errors) {
                    addResult('Check browser console for errors', false);
                }
            }
        }, 1000);
        
        // Also listen for the ready event
        window.addEventListener('unifiedauth:ready', () => {
            addResult('✅ UnifiedAuth ready event fired!', true);
        });
    </script>
</body>
</html>
EOF

echo -e "\n4. Checking if there are any JavaScript errors in the auth file..."
# Use node to check syntax
if command -v node >/dev/null 2>&1; then
    node -c "js/$LATEST_AUTH" 2>&1 || echo "Node not available, skipping syntax check"
fi

echo -e "\n5. Making sure the file is accessible via HTTPS..."
echo "Testing: https://bankcsvconverter.com/js/$LATEST_AUTH"
curl -s -I "https://bankcsvconverter.com/js/$LATEST_AUTH" | grep -E "HTTP|Content-Type"

echo -e "\n6. Creating a minimal test to verify script execution..."
cat > minimal-auth-test.html << 'EOF'
<!DOCTYPE html>
<html>
<head><title>Minimal Auth Test</title></head>
<body>
    <h1>Minimal Auth Test</h1>
    <pre id="output"></pre>
    
    <script>
        console.log('Page loaded');
        document.getElementById('output').textContent = 'JavaScript is working\n';
    </script>
    
    <script src="/js/auth-unified-1754076923.js"></script>
    
    <script>
        setTimeout(() => {
            const output = document.getElementById('output');
            output.textContent += 'After script load:\n';
            output.textContent += 'UnifiedAuth exists: ' + (typeof UnifiedAuth !== 'undefined') + '\n';
            
            if (typeof UnifiedAuth !== 'undefined') {
                output.textContent += 'UnifiedAuth properties:\n';
                for (let prop in UnifiedAuth) {
                    output.textContent += '  - ' + prop + ': ' + typeof UnifiedAuth[prop] + '\n';
                }
            }
        }, 1500);
    </script>
</body>
</html>
EOF

echo -e "\nTest pages created:"
echo "1. https://bankcsvconverter.com/test-unified-auth.html"
echo "2. https://bankcsvconverter.com/minimal-auth-test.html"

ENDSSH

echo ""
echo "✅ Debug complete!"
echo ""
echo "Please try these test pages:"
echo "1. https://bankcsvconverter.com/test-unified-auth.html - Detailed UnifiedAuth test"
echo "2. https://bankcsvconverter.com/minimal-auth-test.html - Minimal test"
echo ""
echo "These will show exactly what's happening with the JavaScript loading."