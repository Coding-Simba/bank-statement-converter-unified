#\!/bin/bash

# Debug Login Button
echo "🔍 Debugging Login Button"
echo "========================"
echo ""

SERVER_IP="3.235.19.83"
SERVER_USER="ubuntu"
SSH_KEY="/Users/MAC/Downloads/bank-statement-converter.pem"

# Debug via SSH
ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no "$SERVER_USER@$SERVER_IP" << 'ENDSSH'
cd /home/ubuntu/bank-statement-converter

echo "1. Checking what JavaScript is handling the login form..."
grep -n "submit\|login-btn\|Login" login.html | grep -E "addEventListener|onclick|submit" | head -20

echo -e "\n2. Let's check the inline script in login.html..."
sed -n '/<script>/,/<\/script>/p' login.html | grep -v "^[[:space:]]*$" | head -50

echo -e "\n3. Let's add explicit logging and error handling to the login page..."
# Create a backup first
cp login.html login.html.backup

# Add debugging to the login form
cat > login-debug.js << 'EOFJS'
console.log('[Login Debug] Script starting...');

document.addEventListener('DOMContentLoaded', function() {
    console.log('[Login Debug] DOM loaded');
    
    // Find the login form
    const loginForm = document.getElementById('loginForm');
    const loginButton = document.querySelector('.login-btn');
    
    console.log('[Login Debug] Form found:', \!\!loginForm);
    console.log('[Login Debug] Button found:', \!\!loginButton);
    
    if (loginForm) {
        // Remove any existing listeners
        const newForm = loginForm.cloneNode(true);
        loginForm.parentNode.replaceChild(newForm, loginForm);
        
        // Add new submit handler
        newForm.addEventListener('submit', async function(e) {
            console.log('[Login Debug] Form submitted');
            e.preventDefault();
            
            const email = document.getElementById('email').value;
            const password = document.getElementById('password').value;
            const submitButton = newForm.querySelector('.login-btn');
            
            console.log('[Login Debug] Email:', email);
            console.log('[Login Debug] Password length:', password.length);
            
            if (\!email || \!password) {
                alert('Please enter both email and password');
                return;
            }
            
            // Disable button and show loading
            if (submitButton) {
                submitButton.disabled = true;
                submitButton.textContent = 'Logging in...';
            }
            
            try {
                console.log('[Login Debug] Sending login request...');
                
                // Direct API call
                const response = await fetch('/api/auth/login', {
                    method: 'POST',
                    credentials: 'include',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        email: email,
                        password: password,
                        remember_me: false
                    })
                });
                
                console.log('[Login Debug] Response status:', response.status);
                const data = await response.json();
                console.log('[Login Debug] Response data:', data);
                
                if (response.ok && data.access_token) {
                    console.log('[Login Debug] Login successful');
                    
                    // Store auth data
                    localStorage.setItem('access_token', data.access_token);
                    localStorage.setItem('user', JSON.stringify(data.user));
                    
                    // Show success message
                    alert('Login successful\! Redirecting...');
                    
                    // Redirect
                    window.location.href = '/dashboard-modern.html';
                } else {
                    console.error('[Login Debug] Login failed:', data);
                    alert(data.detail || 'Login failed. Please check your credentials.');
                }
                
            } catch (error) {
                console.error('[Login Debug] Error:', error);
                alert('Network error: ' + error.message);
            } finally {
                // Re-enable button
                if (submitButton) {
                    submitButton.disabled = false;
                    submitButton.textContent = 'Log In';
                }
            }
        });
        
        console.log('[Login Debug] Submit handler attached');
    }
    
    // Also add click handler to button as backup
    if (loginButton) {
        loginButton.addEventListener('click', function(e) {
            console.log('[Login Debug] Button clicked');
            if (loginForm && \!e.defaultPrevented) {
                loginForm.dispatchEvent(new Event('submit'));
            }
        });
    }
});

console.log('[Login Debug] Script loaded');
EOFJS

echo -e "\n4. Inject the debug script into login.html..."
# Add the debug script right before </body>
sed -i '/<\/body>/i <script src="/login-debug.js"></script>' login.html

echo -e "\n5. Let's also create a simple test login page..."
cat > test-login-simple.html << 'EOFHTML'
<\!DOCTYPE html>
<html>
<head>
    <title>Simple Login Test</title>
    <style>
        body { font-family: Arial, sans-serif; padding: 40px; max-width: 400px; margin: 0 auto; }
        input { width: 100%; padding: 10px; margin: 10px 0; }
        button { width: 100%; padding: 10px; background: #007bff; color: white; border: none; cursor: pointer; }
        button:hover { background: #0056b3; }
        #result { margin-top: 20px; padding: 10px; }
        .success { background: #d4edda; color: #155724; }
        .error { background: #f8d7da; color: #721c24; }
    </style>
</head>
<body>
    <h1>Simple Login Test</h1>
    
    <form id="loginForm">
        <input type="email" id="email" placeholder="Email" value="test@example.com">
        <input type="password" id="password" placeholder="Password" value="test123">
        <button type="submit">Test Login</button>
    </form>
    
    <div id="result"></div>
    
    <script>
        document.getElementById('loginForm').onsubmit = async function(e) {
            e.preventDefault();
            
            const result = document.getElementById('result');
            result.textContent = 'Logging in...';
            result.className = '';
            
            try {
                const response = await fetch('/api/auth/login', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        email: document.getElementById('email').value,
                        password: document.getElementById('password').value,
                        remember_me: false
                    })
                });
                
                const data = await response.json();
                
                if (response.ok) {
                    result.textContent = 'Success\! Token: ' + data.access_token.substring(0, 20) + '...';
                    result.className = 'success';
                    
                    setTimeout(() => {
                        window.location.href = '/dashboard-modern.html';
                    }, 2000);
                } else {
                    result.textContent = 'Error: ' + (data.detail || 'Login failed');
                    result.className = 'error';
                }
            } catch (error) {
                result.textContent = 'Network error: ' + error.message;
                result.className = 'error';
            }
        };
    </script>
</body>
</html>
EOFHTML

echo -e "\n6. Check if the backend is still running..."
curl -s http://localhost:5000/health || echo "Backend not responding\!"

echo -e "\nDebug script added to login.html"
echo "Test pages:"
echo "1. https://bankcsvconverter.com/login.html (with debug logging)"
echo "2. https://bankcsvconverter.com/test-login-simple.html (simple test)"

ENDSSH

echo ""
echo "✅ Login button debugging added\!"
echo ""
echo "Open the browser console and try clicking the login button."
echo "You should see detailed debug messages showing what's happening."
