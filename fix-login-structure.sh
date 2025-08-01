#\!/bin/bash

# 🔧 FIX LOGIN.HTML STRUCTURE
echo "🔧 FIXING LOGIN.HTML STRUCTURE ISSUES"
echo "===================================="
echo ""

SERVER_IP="3.235.19.83"
SERVER_USER="ubuntu"
SSH_KEY="/Users/MAC/Downloads/bank-statement-converter.pem"

ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no "$SERVER_USER@$SERVER_IP" << 'ENDSSH'
cd /home/ubuntu/bank-statement-converter

echo "1. Analyzing login.html structure..."
echo "-----------------------------------"

# Check for basic HTML structure
echo "Checking HTML structure:"
grep -c "<html" login.html && echo "✓ Has <html> tag" || echo "✗ Missing <html> tag"
grep -c "<head" login.html && echo "✓ Has <head> tag" || echo "✗ Missing <head> tag"
grep -c "</head>" login.html && echo "✓ Has </head> tag" || echo "✗ Missing </head> tag"
grep -c "<body" login.html && echo "✓ Has <body> tag" || echo "✗ Missing <body> tag"
grep -c "</body>" login.html && echo "✓ Has </body> tag" || echo "✗ Missing </body> tag"
grep -c "</html>" login.html && echo "✓ Has </html> tag" || echo "✗ Missing </html> tag"

echo -e "\n2. Creating properly structured login.html..."
echo "--------------------------------------------"

# Backup current login.html
cp login.html login.html.broken
echo "✓ Backed up current login.html to login.html.broken"

# Create a new, properly structured login.html
cat > login.html << 'HTMLEOF'
<\!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="description" content="Log in to Bank Statement Converter - Access your account to convert bank statements to CSV/Excel.">
    <title>Login - Bank Statement Converter</title>
    
    <\!-- CSS -->
    <link rel="stylesheet" href="/css/unified-auth.css">
    <link rel="stylesheet" href="/css/styles.css">
    
    <style>
        .error-message {
            color: #dc3545;
            background: #f8d7da;
            border: 1px solid #f5c6cb;
            padding: 12px;
            border-radius: 4px;
            margin: 10px 0;
            display: none;
        }
        
        .success-message {
            color: #155724;
            background: #d4edda;
            border: 1px solid #c3e6cb;
            padding: 12px;
            border-radius: 4px;
            margin: 10px 0;
            display: none;
        }
        
        .login-btn {
            width: 100%;
            padding: 12px;
            background: #007bff;
            color: white;
            border: none;
            border-radius: 4px;
            font-size: 16px;
            cursor: pointer;
            transition: background 0.3s;
        }
        
        .login-btn:hover {
            background: #0056b3;
        }
        
        .login-btn:disabled {
            background: #6c757d;
            cursor: not-allowed;
        }
    </style>
</head>
<body>
    <div class="auth-wrapper">
        <div class="auth-container">
            <div class="auth-box">
                <\!-- Logo/Header -->
                <div class="auth-header">
                    <h1>Welcome Back</h1>
                    <p>Log in to your account</p>
                </div>
                
                <\!-- Login Form -->
                <form id="loginForm" class="auth-form">
                    <div class="form-group">
                        <label for="email">Email</label>
                        <input 
                            type="email" 
                            id="email" 
                            name="email" 
                            required 
                            placeholder="Enter your email"
                            autocomplete="email"
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
                            autocomplete="current-password"
                        >
                    </div>
                    
                    <div class="form-group checkbox-group">
                        <label>
                            <input type="checkbox" id="rememberMe" name="rememberMe">
                            <span>Remember me</span>
                        </label>
                    </div>
                    
                    <\!-- Messages -->
                    <div id="errorMessage" class="error-message"></div>
                    <div id="successMessage" class="success-message"></div>
                    
                    <\!-- Submit Button -->
                    <button type="submit" class="login-btn" id="loginButton">
                        Log In
                    </button>
                </form>
                
                <\!-- Footer Links -->
                <div class="auth-footer">
                    <p>Don't have an account? <a href="/signup.html">Sign up</a></p>
                    <p><a href="/forgot-password.html">Forgot your password?</a></p>
                </div>
                
                <\!-- OAuth (optional) -->
                <div class="oauth-divider" style="margin: 20px 0;">
                    <span>Or continue with</span>
                </div>
                
                <div class="oauth-buttons">
                    <button class="oauth-btn google-btn" onclick="alert('Google login coming soon')">
                        <img src="/images/google-icon.svg" alt="Google"> Google
                    </button>
                </div>
            </div>
        </div>
    </div>
    
    <\!-- Scripts -->
    <script src="/js/api-config.js"></script>
    <script src="/js/ultrathink-auth.js"></script>
    <script src="/js/auth-fixed.js"></script>
    
    <\!-- Inline login handler as backup -->
    <script>
        // Backup login handler in case auth scripts fail
        document.addEventListener('DOMContentLoaded', function() {
            const loginForm = document.getElementById('loginForm');
            if (\!loginForm) return;
            
            // Check if UnifiedAuth/UltraAuth is available
            const authAvailable = typeof UnifiedAuth \!== 'undefined' || typeof UltraAuth \!== 'undefined';
            
            if (\!authAvailable) {
                console.log('[Backup] Using inline login handler');
                
                loginForm.addEventListener('submit', async function(e) {
                    e.preventDefault();
                    
                    const email = document.getElementById('email').value;
                    const password = document.getElementById('password').value;
                    const rememberMe = document.getElementById('rememberMe').checked;
                    const loginButton = document.getElementById('loginButton');
                    const errorDiv = document.getElementById('errorMessage');
                    const successDiv = document.getElementById('successMessage');
                    
                    // Reset messages
                    errorDiv.style.display = 'none';
                    successDiv.style.display = 'none';
                    
                    // Disable button
                    loginButton.disabled = true;
                    loginButton.textContent = 'Logging in...';
                    
                    try {
                        const response = await fetch('/api/auth/login', {
                            method: 'POST',
                            credentials: 'include',
                            headers: {
                                'Content-Type': 'application/json'
                            },
                            body: JSON.stringify({
                                email: email,
                                password: password,
                                remember_me: rememberMe
                            })
                        });
                        
                        const data = await response.json();
                        
                        if (response.ok && data.access_token) {
                            // Store auth data
                            localStorage.setItem('access_token', data.access_token);
                            localStorage.setItem('user', JSON.stringify(data.user));
                            
                            // Show success
                            successDiv.textContent = 'Login successful\! Redirecting...';
                            successDiv.style.display = 'block';
                            
                            // Redirect
                            setTimeout(() => {
                                window.location.href = '/dashboard-modern.html';
                            }, 1000);
                        } else {
                            throw new Error(data.detail || 'Invalid email or password');
                        }
                    } catch (error) {
                        // Show error
                        errorDiv.textContent = error.message;
                        errorDiv.style.display = 'block';
                        
                        // Re-enable button
                        loginButton.disabled = false;
                        loginButton.textContent = 'Log In';
                    }
                });
            } else {
                console.log('[Auth] Using UnifiedAuth/UltraAuth system');
            }
        });
    </script>
</body>
</html>
HTMLEOF

echo "✓ Created new properly structured login.html"

echo -e "\n3. Verifying the fix..."
echo "----------------------"

# Check structure again
echo "HTML Structure Check:"
grep -c "<html" login.html && echo "✓ Has <html> tag" || echo "✗ Missing <html> tag"
grep -c "</body>" login.html && echo "✓ Has </body> tag" || echo "✗ Missing </body> tag"
grep -c "</html>" login.html && echo "✓ Has </html> tag" || echo "✗ Missing </html> tag"

echo -e "\nScript tags:"
grep -n "script" login.html | grep "src" | grep -E "auth|ultra"

echo -e "\nForm check:"
grep -c "loginForm" login.html && echo "✓ Has login form" || echo "✗ Missing login form"
grep -c "loginButton" login.html && echo "✓ Has login button" || echo "✗ Missing login button"

echo -e "\n4. Setting permissions..."
chmod 644 login.html
echo "✓ Set proper permissions"

echo -e "\n5. Testing the login endpoint one more time..."
curl -s -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test123"}' | \
  python3 -c "import sys, json; d=json.load(sys.stdin); print('✓ API Working - Token received' if 'access_token' in d else '✗ API Error')"

echo -e "\n✅ LOGIN.HTML STRUCTURE FIXED\!"
echo "============================="
echo ""
echo "The main login page now has:"
echo "✓ Proper HTML5 structure"
echo "✓ Both auth scripts loaded (ultrathink + auth-fixed)"
echo "✓ Inline backup login handler"
echo "✓ Clean form with proper IDs"
echo "✓ Error/success message handling"
echo "✓ Remember me functionality"
echo ""
echo "🔗 Test it now: https://bankcsvconverter.com/login.html"
echo ""
echo "Login with:"
echo "Email: test@example.com"
echo "Password: test123"

ENDSSH
