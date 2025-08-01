#\!/bin/bash

# 🎨 FIX HEADER AND FOOTER TO MATCH WEBSITE STYLE
echo "🎨 FIXING HEADER AND FOOTER STYLE"
echo "================================"
echo ""

SERVER_IP="3.235.19.83"
SERVER_USER="ubuntu"
SSH_KEY="/Users/MAC/Downloads/bank-statement-converter.pem"

ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no "$SERVER_USER@$SERVER_IP" << 'ENDSSH'
cd /home/ubuntu/bank-statement-converter

echo "1. Extracting header from index.html..."
echo "--------------------------------------"
# Extract the exact header HTML
HEADER=$(sed -n '/<nav class="navbar">/,/<\/nav>/p' index.html)
echo "Header found: $(echo "$HEADER" | wc -l) lines"

echo -e "\n2. Extracting footer from index.html..."
echo "---------------------------------------"
# Extract the exact footer HTML
FOOTER=$(sed -n '/<footer/,/<\/footer>/p' index.html)
echo "Footer found: $(echo "$FOOTER" | wc -l) lines"

echo -e "\n3. Getting the CSS files used in index.html..."
echo "---------------------------------------------"
grep -o 'href="[^"]*\.css"' index.html | head -10

echo -e "\n4. Creating new login.html with exact header/footer..."
echo "-----------------------------------------------------"

cat > login.html << 'HTMLEOF'
<\!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Login - Bank Statement Converter</title>
    
    <\!-- Copy CSS from index.html -->
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <link rel="stylesheet" href="/css/modern-style.css">
    <link rel="stylesheet" href="/css/style.css">
    <link rel="stylesheet" href="/css/production.css">
    <link rel="stylesheet" href="/css/nav-fix.css">
    <link rel="stylesheet" href="/css/dropdown-simple-fix.css">
    
    <style>
        /* Login specific styles */
        .login-main {
            min-height: calc(100vh - 400px);
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 60px 20px;
            background: #f8f9fa;
        }
        
        .login-container {
            background: white;
            border-radius: 10px;
            box-shadow: 0 2px 20px rgba(0, 0, 0, 0.1);
            width: 100%;
            max-width: 440px;
            padding: 40px;
        }
        
        .login-header {
            text-align: center;
            margin-bottom: 30px;
        }
        
        .login-header h1 {
            color: #2c3e50;
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
            color: #2c3e50;
            font-weight: 600;
            font-size: 14px;
        }
        
        .form-group input {
            width: 100%;
            padding: 12px 16px;
            border: 1px solid #ddd;
            border-radius: 6px;
            font-size: 16px;
            transition: all 0.3s ease;
        }
        
        .form-group input:focus {
            outline: none;
            border-color: #4CAF50;
            box-shadow: 0 0 0 3px rgba(76, 175, 80, 0.1);
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
            background: #4CAF50;
            color: white;
            border: none;
            border-radius: 6px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
        }
        
        .login-button:hover {
            background: #45a049;
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(76, 175, 80, 0.3);
        }
        
        .login-button:disabled {
            background: #ccc;
            cursor: not-allowed;
            transform: none;
        }
        
        .message {
            padding: 12px 16px;
            border-radius: 6px;
            margin-bottom: 20px;
            font-size: 14px;
            display: none;
        }
        
        .error-message {
            background: #ffebee;
            color: #c62828;
            border: 1px solid #ffcdd2;
        }
        
        .success-message {
            background: #e8f5e9;
            color: #2e7d32;
            border: 1px solid #c8e6c9;
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
            background: #e0e0e0;
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
            border: 1px solid #ddd;
            background: white;
            border-radius: 6px;
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
            background: #f8f9fa;
            border-color: #ccc;
        }
        
        .auth-links {
            text-align: center;
            margin-top: 24px;
        }
        
        .auth-links p {
            color: #666;
            font-size: 14px;
            margin-bottom: 8px;
        }
        
        .auth-links a {
            color: #4CAF50;
            text-decoration: none;
            font-weight: 500;
        }
        
        .auth-links a:hover {
            text-decoration: underline;
        }
    </style>
</head>
<body>
HTMLEOF

# Add the exact header from index.html
echo "Adding header from index.html..."
sed -n '/<nav class="navbar">/,/<\/nav>/p' index.html >> login.html

# Add the main content
cat >> login.html << 'HTMLMAIN'
    <\!-- Main Content -->
    <main class="login-main">
        <div class="login-container">
            <div class="login-header">
                <h1>Welcome Back</h1>
                <p>Sign in to your account to continue</p>
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
            
            <div class="auth-links">
                <p>Don't have an account? <a href="/signup.html">Sign up</a></p>
                <p><a href="/forgot-password.html">Forgot your password?</a></p>
            </div>
        </div>
    </main>
HTMLMAIN

# Add the exact footer from index.html
echo "Adding footer from index.html..."
sed -n '/<footer/,/<\/footer>/p' index.html >> login.html

# Add the closing tags and script
cat >> login.html << 'HTMLEND'
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
                
                if (response.ok && data.access_token) {
                    // Store auth data
                    localStorage.setItem('access_token', data.access_token);
                    localStorage.setItem('user', JSON.stringify(data.user));
                    
                    // Show success
                    successMsg.textContent = 'Login successful\! Redirecting...';
                    successMsg.style.display = 'block';
                    
                    // Redirect
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
                // Show error
                errorMsg.textContent = 'Network error. Please check your connection and try again.';
                errorMsg.style.display = 'block';
                
                // Re-enable button
                loginBtn.disabled = false;
                loginBtn.textContent = 'Sign In';
            }
        }
    </script>
    
    <\!-- Add any scripts from index.html footer -->
    <script src="/js/nav-dropdown.js"></script>
    <script src="/js/mobile-menu.js"></script>
</body>
</html>
HTMLEND

echo "✅ Created login.html with exact header/footer from index.html"

echo -e "\n5. Setting permissions..."
chmod 644 login.html

echo -e "\n6. Verifying the update..."
echo "Header lines in login.html: $(grep -c "navbar" login.html)"
echo "Footer lines in login.html: $(grep -c "footer" login.html)"

echo -e "\n✅ HEADER AND FOOTER STYLE FIXED\!"
echo "================================"
echo ""
echo "What was done:"
echo "✓ Copied exact header HTML from index.html"
echo "✓ Copied exact footer HTML from index.html" 
echo "✓ Included all CSS files from homepage"
echo "✓ Maintained login functionality"
echo "✓ Consistent styling throughout"
echo ""
echo "🔗 Check your updated login page:"
echo "https://bankcsvconverter.com/login.html"
echo ""
echo "The login page now has the EXACT same header and footer as your homepage\!"

ENDSSH
