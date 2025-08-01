#\!/bin/bash

# Create JS Diagnostic
echo "🔍 Creating JavaScript Diagnostic"
echo "================================"
echo ""

SERVER_IP="3.235.19.83"
SERVER_USER="ubuntu"
SSH_KEY="/Users/MAC/Downloads/bank-statement-converter.pem"

# Create via SSH
ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no "$SERVER_USER@$SERVER_IP" << 'ENDSSH'
cd /home/ubuntu/bank-statement-converter

echo "1. Creating a diagnostic that checks script loading step by step..."
cat > js-diagnostic.html << 'EOFHTML'
<\!DOCTYPE html>
<html>
<head>
    <title>JS Loading Diagnostic</title>
    <style>
        body { font-family: monospace; padding: 20px; }
        .step { margin: 10px 0; padding: 10px; background: #f0f0f0; }
        .success { color: green; }
        .error { color: red; }
        .info { color: blue; }
    </style>
</head>
<body>
    <h1>JavaScript Loading Diagnostic</h1>
    
    <div id="output"></div>
    
    <script>
        const output = document.getElementById('output');
        
        function log(message, type = 'info') {
            const div = document.createElement('div');
            div.className = `step ${type}`;
            div.textContent = `[${new Date().toISOString()}] ${message}`;
            output.appendChild(div);
            console.log(message);
        }
        
        log('Starting diagnostic...');
        
        // Test 1: Check if script tag exists
        const scripts = document.getElementsByTagName('script');
        log(`Found ${scripts.length} script tags on page`);
        
        // Test 2: Load auth script dynamically
        log('Loading auth-unified-1754076923.js dynamically...');
        
        const script = document.createElement('script');
        script.src = '/js/auth-unified-1754076923.js';
        
        script.onload = () => {
            log('Script loaded successfully\!', 'success');
            
            // Wait a bit for execution
            setTimeout(() => {
                if (typeof UnifiedAuth \!== 'undefined') {
                    log('UnifiedAuth is defined\!', 'success');
                    log(`UnifiedAuth type: ${typeof UnifiedAuth}`);
                    log(`UnifiedAuth constructor: ${UnifiedAuth.constructor.name}`);
                    
                    if (UnifiedAuth.initialized \!== undefined) {
                        log(`UnifiedAuth.initialized: ${UnifiedAuth.initialized}`, 'info');
                    }
                    
                    // List all properties
                    const props = Object.getOwnPropertyNames(UnifiedAuth);
                    log(`UnifiedAuth properties: ${props.join(', ')}`, 'info');
                    
                } else {
                    log('UnifiedAuth is still undefined after script load', 'error');
                    
                    // Check window object
                    log('Checking window object for UnifiedAuth...');
                    for (let key in window) {
                        if (key.toLowerCase().includes('auth')) {
                            log(`Found window.${key}: ${typeof window[key]}`, 'info');
                        }
                    }
                }
            }, 500);
        };
        
        script.onerror = (error) => {
            log(`Script failed to load: ${error}`, 'error');
        };
        
        document.head.appendChild(script);
        
        // Test 3: Check for any global errors
        window.addEventListener('error', (event) => {
            log(`Global error: ${event.message} at ${event.filename}:${event.lineno}:${event.colno}`, 'error');
        });
        
        // Test 4: Try direct fetch
        log('Fetching script content directly...');
        fetch('/js/auth-unified-1754076923.js')
            .then(response => {
                log(`Direct fetch status: ${response.status}`, response.ok ? 'success' : 'error');
                return response.text();
            })
            .then(content => {
                log(`Script content length: ${content.length} characters`, 'info');
                
                // Check for obvious issues
                if (content.includes('UnifiedAuth')) {
                    log('Script contains UnifiedAuth reference', 'success');
                } else {
                    log('Script does NOT contain UnifiedAuth reference\!', 'error');
                }
                
                // Try to evaluate it manually (for diagnostic only)
                try {
                    log('Attempting manual evaluation...');
                    eval(content);
                    
                    setTimeout(() => {
                        if (typeof UnifiedAuth \!== 'undefined') {
                            log('Manual evaluation created UnifiedAuth\!', 'success');
                        } else {
                            log('Manual evaluation did not create UnifiedAuth', 'error');
                        }
                    }, 100);
                } catch (evalError) {
                    log(`Eval error: ${evalError.message}`, 'error');
                }
            })
            .catch(fetchError => {
                log(`Fetch error: ${fetchError.message}`, 'error');
            });
    </script>
</body>
</html>
EOFHTML

echo "2. Let's also check the actual content of the auth script for issues..."
echo "First 20 lines:"
head -20 js/auth-unified-1754076923.js

echo -e "\nLast 20 lines:"
tail -20 js/auth-unified-1754076923.js

echo -e "\n3. Checking for any syntax errors using node..."
if command -v node >/dev/null 2>&1; then
    node -c js/auth-unified-1754076923.js && echo "✅ No syntax errors found" || echo "❌ Syntax errors detected"
else
    echo "Node.js not installed, cannot check syntax"
fi

echo -e "\n4. Creating a version that definitely should work..."
cat > js/auth-unified-simple.js << 'EOFJS'
// Ultra simple version for testing
console.log('[UnifiedAuth] Simple version loading...');

window.UnifiedAuth = {
    initialized: true,
    login: async function(email, password) {
        console.log('Login called with:', email);
        return { success: false, error: 'Simple version - not implemented' };
    },
    isAuthenticated: function() {
        return false;
    },
    getUser: function() {
        return null;
    }
};

console.log('[UnifiedAuth] Simple version loaded\!');
EOFJS

echo -e "\n5. Creating test page for simple version..."
cat > test-simple-auth.html << 'EOFHTML'
<\!DOCTYPE html>
<html>
<head>
    <title>Test Simple Auth</title>
</head>
<body>
    <h1>Simple Auth Test</h1>
    <pre id="result">Loading...</pre>
    
    <script src="/js/auth-unified-simple.js"></script>
    
    <script>
        setTimeout(() => {
            const result = document.getElementById('result');
            if (typeof UnifiedAuth \!== 'undefined') {
                result.textContent = '✅ UnifiedAuth loaded\!\n';
                result.textContent += 'Properties: ' + Object.keys(UnifiedAuth).join(', ');
            } else {
                result.textContent = '❌ UnifiedAuth NOT loaded';
            }
        }, 500);
    </script>
</body>
</html>
EOFHTML

ENDSSH

echo ""
echo "✅ Diagnostics created\!"
echo ""
echo "Try these pages:"
echo "1. https://bankcsvconverter.com/js-diagnostic.html - Comprehensive diagnostic"
echo "2. https://bankcsvconverter.com/test-simple-auth.html - Simple version test"
