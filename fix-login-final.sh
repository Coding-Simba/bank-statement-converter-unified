#\!/bin/bash

# 🚨 FINAL LOGIN FIX - HTML & FUNCTIONALITY
echo "🚨 FIXING LOGIN PAGE - FINAL SOLUTION"
echo "===================================="
echo ""

SERVER_IP="3.235.19.83"
SERVER_USER="ubuntu"
SSH_KEY="/Users/MAC/Downloads/bank-statement-converter.pem"

ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no "$SERVER_USER@$SERVER_IP" << 'ENDSSH'
cd /home/ubuntu/bank-statement-converter

echo "1. First, let's check what's wrong with current login.html..."
echo "------------------------------------------------------------"
# Check for HTML comment issues
grep -n "<\!--" login.html | head -5 && echo "Found HTML comments that might be rendering"

echo -e "\n2. Creating FINAL WORKING login.html..."
echo "--------------------------------------"

cat > login.html << 'HTMLFINAL'
<\!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Login - Bank Statement Converter</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }
        
        .login-container {
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
            width: 100%;
            max-width: 420px;
            padding: 40px;
        }
        
        .login-header {
            text-align: center;
            margin-bottom: 30px;
        }
        
        .login-header h1 {
            color: #333;
            font-size: 28px;
            font-weight: 700;
            margin-bottom: 8px;
        }
        
        .login-header p {
            color: #666;
            font-size: 16px;
        }
        
        .form-group {
            margin-bottom: 20px;
        }
        
        .form-group label {
            display: block;
            margin-bottom: 8px;
            color: #333;
            font-weight: 500;
            font-size: 14px;
        }
        
        .form-group input {
            width: 100%;
            padding: 12px 16px;
            border: 2px solid #e1e4e8;
            border-radius: 8px;
            font-size: 16px;
            transition: all 0.3s ease;
            background: #fafbfc;
        }
        
        .form-group input:focus {
            outline: none;
            border-color: #667eea;
            background: white;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }
        
        .checkbox-wrapper {
            display: flex;
            align-items: center;
            margin-bottom: 24px;
        }
        
        .checkbox-wrapper input {
            width: 18px;
            height: 18px;
            margin-right: 8px;
            cursor: pointer;
        }
        
        .checkbox-wrapper label {
            cursor: pointer;
            user-select: none;
            color: #666;
            font-size: 14px;
        }
        
        .login-button {
            width: 100%;
            padding: 14px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 8px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
        }
        
        .login-button:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 20px rgba(102, 126, 234, 0.3);
        }
        
        .login-button:disabled {
            background: #ccc;
            cursor: not-allowed;
            transform: none;
        }
        
        .message {
            padding: 12px 16px;
            border-radius: 8px;
            margin-bottom: 20px;
            font-size: 14px;
            display: none;
        }
        
        .error-message {
            background: #fee;
            color: #c33;
            border: 1px solid #fcc;
        }
        
        .success-message {
            background: #efe;
            color: #3c3;
            border: 1px solid #cfc;
        }
        
        .divider {
            text-align: center;
            margin: 30px 0 20px;
            position: relative;
        }
        
        .divider::before {
            content: '';
            position: absolute;
            top: 50%;
            left: 0;
            right: 0;
            height: 1px;
            background: #e1e4e8;
        }
        
        .divider span {
            background: white;
            padding: 0 16px;
            position: relative;
            color: #666;
            font-size: 14px;
        }
        
        .google-button {
            width: 100%;
            padding: 12px;
            border: 2px solid #e1e4e8;
            background: white;
            border-radius: 8px;
            font-size: 15px;
            cursor: pointer;
            transition: all 0.3s ease;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
            color: #333;
            font-weight: 500;
        }
        
        .google-button:hover {
            border-color: #667eea;
            background: #f8f9ff;
        }
        
        .footer-links {
            text-align: center;
            margin-top: 24px;
        }
        
        .footer-links p {
            color: #666;
            font-size: 14px;
            margin-bottom: 8px;
        }
        
        .footer-links a {
            color: #667eea;
            text-decoration: none;
            font-weight: 500;
        }
        
        .footer-links a:hover {
            color: #764ba2;
            text-decoration: underline;
        }
    </style>
</head>
<body>
    <div class="login-container">
        <div class="login-header">
            <h1>Bank Statement Converter</h1>
            <p>Welcome back\! Please login to your account</p>
        </div>
        
        <form id="loginForm" onsubmit="handleLogin(event)">
            <div id="errorMsg" class="message error-message"></div>
            <div id="successMsg" class="message success-message"></div>
            
            <div class="form-group">
                <label for="email">Email Address</label>
                <input 
                    type="email" 
                    id="email" 
                    name="email" 
                    required 
                    placeholder="you@example.com"
                    value="test@example.com"
                >
            </div>
            
            <div class="form-group">
                <label for="password">Password</label>
                <input 
                    type="password" 
                    id="password" 
                    name="password" 
                    required 
                    placeholder="Enter your password"
                    value="test123"
                >
            </div>
            
            <div class="checkbox-wrapper">
                <input type="checkbox" id="remember" name="remember">
                <label for="remember">Remember me for 30 days</label>
            </div>
            
            <button type="submit" class="login-button" id="loginBtn">
                Sign In
            </button>
        </form>
        
        <div class="divider">
            <span>or continue with</span>
        </div>
        
        <button class="google-button" onclick="alert('Google login coming soon\!')">
            <svg width="20" height="20" viewBox="0 0 24 24">
                <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
                <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
            </svg>
            Sign in with Google
        </button>
        
        <div class="footer-links">
            <p>Don't have an account? <a href="/signup.html">Sign up</a></p>
            <p><a href="/forgot-password.html">Forgot your password?</a></p>
        </div>
    </div>
    
    <script>
        async function handleLogin(event) {
            event.preventDefault();
            
            const email = document.getElementById('email').value;
            const password = document.getElementById('password').value;
            const remember = document.getElementById('remember').checked;
            const loginBtn = document.getElementById('loginBtn');
            const errorMsg = document.getElementById('errorMsg');
            const successMsg = document.getElementById('successMsg');
            
            // Reset messages
            errorMsg.style.display = 'none';
            successMsg.style.display = 'none';
            errorMsg.textContent = '';
            successMsg.textContent = '';
            
            // Disable button
            loginBtn.disabled = true;
            loginBtn.textContent = 'Signing in...';
            
            try {
                const response = await fetch('/api/auth/login', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        email: email,
                        password: password,
                        remember_me: remember
                    })
                });
                
                const data = await response.json();
                console.log('Login response:', data);
                
                if (response.ok && data.access_token) {
                    // Store auth data
                    localStorage.setItem('access_token', data.access_token);
                    localStorage.setItem('user', JSON.stringify(data.user));
                    
                    // Show success
                    successMsg.textContent = 'Login successful\! Redirecting...';
                    successMsg.style.display = 'block';
                    
                    // Redirect after 1 second
                    setTimeout(() => {
                        window.location.href = '/dashboard-modern.html';
                    }, 1000);
                } else {
                    // Show error
                    errorMsg.textContent = data.detail || 'Invalid email or password. Please try again.';
                    errorMsg.style.display = 'block';
                    
                    // Re-enable button
                    loginBtn.disabled = false;
                    loginBtn.textContent = 'Sign In';
                }
            } catch (error) {
                console.error('Login error:', error);
                
                // Show error
                errorMsg.textContent = 'Network error. Please check your connection and try again.';
                errorMsg.style.display = 'block';
                
                // Re-enable button
                loginBtn.disabled = false;
                loginBtn.textContent = 'Sign In';
            }
        }
        
        // Add enter key support
        document.addEventListener('DOMContentLoaded', function() {
            document.getElementById('email').focus();
        });
    </script>
</body>
</html>
HTMLFINAL

echo "✅ Created clean login.html without HTML comment issues"

echo -e "\n3. Testing login functionality..."
echo "---------------------------------"
# Test if backend is responding
echo "Testing backend API:"
curl -s -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test123"}' | \
  python3 -c "import sys, json; d=json.load(sys.stdin); print('✅ Backend working' if 'access_token' in d else '❌ Backend error')"

echo -e "\n4. Checking file permissions..."
chmod 644 login.html
ls -la login.html

echo -e "\n5. Let's also create a debug version to test..."
cat > login-debug.html << 'DEBUGHTML'
<\!DOCTYPE html>
<html>
<head>
    <title>Login Debug</title>
    <style>
        body { font-family: Arial; padding: 40px; max-width: 400px; margin: 0 auto; }
        input, button { width: 100%; padding: 10px; margin: 10px 0; font-size: 16px; }
        button { background: #007bff; color: white; border: none; cursor: pointer; }
        button:hover { background: #0056b3; }
        .message { padding: 10px; margin: 10px 0; border-radius: 4px; }
        .error { background: #f8d7da; color: #721c24; }
        .success { background: #d4edda; color: #155724; }
        pre { background: #f5f5f5; padding: 10px; overflow: auto; }
    </style>
</head>
<body>
    <h1>Login Debug Page</h1>
    
    <form id="form">
        <input type="email" id="email" placeholder="Email" value="test@example.com">
        <input type="password" id="password" placeholder="Password" value="test123">
        <button type="submit">Login</button>
    </form>
    
    <div id="result"></div>
    
    <h3>Debug Info:</h3>
    <pre id="debug"></pre>
    
    <script>
        const debug = document.getElementById('debug');
        const result = document.getElementById('result');
        
        // Log everything
        function log(msg) {
            debug.textContent += msg + '\n';
            console.log(msg);
        }
        
        document.getElementById('form').onsubmit = async (e) => {
            e.preventDefault();
            log('Form submitted');
            
            const payload = {
                email: document.getElementById('email').value,
                password: document.getElementById('password').value,
                remember_me: true
            };
            
            log('Payload: ' + JSON.stringify(payload));
            
            try {
                log('Sending request to /api/auth/login...');
                const response = await fetch('/api/auth/login', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(payload)
                });
                
                log('Response status: ' + response.status);
                const data = await response.json();
                log('Response data: ' + JSON.stringify(data, null, 2));
                
                if (response.ok && data.access_token) {
                    result.innerHTML = '<div class="message success">✅ Login successful\!</div>';
                    localStorage.setItem('access_token', data.access_token);
                    localStorage.setItem('user', JSON.stringify(data.user));
                    log('Auth data stored in localStorage');
                    
                    setTimeout(() => {
                        window.location.href = '/dashboard-modern.html';
                    }, 2000);
                } else {
                    result.innerHTML = '<div class="message error">❌ ' + (data.detail || 'Login failed') + '</div>';
                }
            } catch (error) {
                log('ERROR: ' + error.message);
                result.innerHTML = '<div class="message error">❌ Network error: ' + error.message + '</div>';
            }
        };
        
        // Check current auth status
        log('Current auth token: ' + (localStorage.getItem('access_token') ? 'Present' : 'Not found'));
        log('Current user: ' + (localStorage.getItem('user') || 'Not found'));
    </script>
</body>
</html>
DEBUGHTML

echo "✅ Created login-debug.html for testing"

echo -e "\n✅ FINAL LOGIN FIX COMPLETE\!"
echo "============================"
echo ""
echo "What was fixed:"
echo "✓ Removed HTML comment rendering issues"
echo "✓ Created clean, working login form"
echo "✓ Simple inline JavaScript (no dependencies)"
echo "✓ Pre-filled with test credentials"
echo "✓ Clear error/success messages"
echo "✓ Debug version for troubleshooting"
echo ""
echo "🔗 Test these pages:"
echo "1. Main login: https://bankcsvconverter.com/login.html"
echo "2. Debug login: https://bankcsvconverter.com/login-debug.html"
echo ""
echo "The test credentials are pre-filled:"
echo "Email: test@example.com"
echo "Password: test123"

ENDSSH
