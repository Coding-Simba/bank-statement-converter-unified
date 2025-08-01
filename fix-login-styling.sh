#\!/bin/bash

# 🎨 FIX LOGIN PAGE STYLING
echo "🎨 FIXING LOGIN PAGE STYLING"
echo "==========================="
echo ""

SERVER_IP="3.235.19.83"
SERVER_USER="ubuntu"
SSH_KEY="/Users/MAC/Downloads/bank-statement-converter.pem"

ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no "$SERVER_USER@$SERVER_IP" << 'ENDSSH'
cd /home/ubuntu/bank-statement-converter

echo "1. Checking if CSS files exist..."
echo "---------------------------------"
ls -la css/ | grep -E "unified-auth|styles" || echo "⚠️ CSS files might be missing"

echo -e "\n2. Creating beautiful login page with inline styles..."
echo "---------------------------------------------------"

cat > login.html << 'HTMLEOF'
<\!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="description" content="Log in to Bank Statement Converter - Access your account to convert bank statements to CSV/Excel.">
    <title>Login - Bank Statement Converter</title>
    
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }
        
        .auth-container {
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
            width: 100%;
            max-width: 420px;
            padding: 40px;
            animation: slideIn 0.5s ease-out;
        }
        
        @keyframes slideIn {
            from {
                opacity: 0;
                transform: translateY(30px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        
        .logo {
            text-align: center;
            margin-bottom: 30px;
        }
        
        .logo h1 {
            color: #333;
            font-size: 28px;
            font-weight: 700;
            margin-bottom: 8px;
        }
        
        .logo p {
            color: #666;
            font-size: 16px;
        }
        
        .form-group {
            margin-bottom: 20px;
        }
        
        label {
            display: block;
            margin-bottom: 8px;
            color: #333;
            font-weight: 500;
            font-size: 14px;
        }
        
        input[type="email"],
        input[type="password"] {
            width: 100%;
            padding: 12px 16px;
            border: 2px solid #e1e4e8;
            border-radius: 8px;
            font-size: 16px;
            transition: all 0.3s ease;
            background: #fafbfc;
        }
        
        input[type="email"]:focus,
        input[type="password"]:focus {
            outline: none;
            border-color: #667eea;
            background: white;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }
        
        input::placeholder {
            color: #999;
        }
        
        .checkbox-group {
            display: flex;
            align-items: center;
            margin-bottom: 24px;
        }
        
        .checkbox-group input[type="checkbox"] {
            width: 18px;
            height: 18px;
            margin-right: 8px;
            cursor: pointer;
        }
        
        .checkbox-group label {
            margin-bottom: 0;
            cursor: pointer;
            user-select: none;
            color: #666;
        }
        
        .login-btn {
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
            position: relative;
            overflow: hidden;
        }
        
        .login-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 20px rgba(102, 126, 234, 0.3);
        }
        
        .login-btn:active {
            transform: translateY(0);
        }
        
        .login-btn:disabled {
            background: #ccc;
            cursor: not-allowed;
            transform: none;
            box-shadow: none;
        }
        
        .error-message,
        .success-message {
            padding: 12px 16px;
            border-radius: 8px;
            margin-bottom: 20px;
            font-size: 14px;
            display: none;
            animation: fadeIn 0.3s ease;
        }
        
        @keyframes fadeIn {
            from { opacity: 0; }
            to { opacity: 1; }
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
            transition: color 0.3s ease;
        }
        
        .footer-links a:hover {
            color: #764ba2;
            text-decoration: underline;
        }
        
        .oauth-btn {
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
        
        .oauth-btn:hover {
            border-color: #667eea;
            background: #f8f9ff;
        }
        
        .oauth-btn img {
            width: 20px;
            height: 20px;
        }
        
        /* Mobile responsive */
        @media (max-width: 480px) {
            .auth-container {
                padding: 30px 20px;
            }
            
            .logo h1 {
                font-size: 24px;
            }
        }
    </style>
</head>
<body>
    <div class="auth-container">
        <div class="logo">
            <h1>Bank Statement Converter</h1>
            <p>Welcome back\! Please login to your account</p>
        </div>
        
        <form id="loginForm">
            <div class="form-group">
                <label for="email">Email Address</label>
                <input 
                    type="email" 
                    id="email" 
                    name="email" 
                    required 
                    placeholder="you@example.com"
                    autocomplete="email"
                    autofocus
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
            
            <div class="checkbox-group">
                <input type="checkbox" id="rememberMe" name="rememberMe">
                <label for="rememberMe">Remember me for 30 days</label>
            </div>
            
            <div id="errorMessage" class="error-message"></div>
            <div id="successMessage" class="success-message"></div>
            
            <button type="submit" class="login-btn" id="loginButton">
                Sign In
            </button>
        </form>
        
        <div class="divider">
            <span>or continue with</span>
        </div>
        
        <button class="oauth-btn" onclick="alert('Google login coming soon\!')">
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
    
    <\!-- Scripts -->
    <script src="/js/ultrathink-auth.js"></script>
    <script src="/js/auth-fixed.js"></script>
    
    <\!-- Inline login handler -->
    <script>
        document.getElementById('loginForm').addEventListener('submit', async function(e) {
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
            loginButton.textContent = 'Signing in...';
            
            try {
                // Try UltraAuth first if available
                if (typeof UltraAuth \!== 'undefined' && UltraAuth.login) {
                    const result = await UltraAuth.login(email, password, rememberMe);
                    if (result.success) {
                        successDiv.textContent = 'Login successful\! Redirecting...';
                        successDiv.style.display = 'block';
                        setTimeout(() => window.location.href = '/dashboard-modern.html', 1000);
                        return;
                    } else {
                        throw new Error(result.error);
                    }
                }
                
                // Fallback to direct API call
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
                loginButton.textContent = 'Sign In';
            }
        });
        
        // Auto-focus email field
        window.addEventListener('load', () => {
            document.getElementById('email').focus();
        });
    </script>
</body>
</html>
HTMLEOF

echo "✅ Created beautiful login page with inline styles"

echo -e "\n3. Creating a modern CSS file for other pages..."
echo "-----------------------------------------------"

# Ensure css directory exists
mkdir -p css

# Create unified-auth.css
cat > css/unified-auth.css << 'CSSEOF'
/* Unified Auth Styles */
.auth-wrapper {
    min-height: 100vh;
    display: flex;
    align-items: center;
    justify-content: center;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    padding: 20px;
}

.auth-container {
    width: 100%;
    max-width: 420px;
}

.auth-box {
    background: white;
    padding: 40px;
    border-radius: 20px;
    box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
}

.auth-header {
    text-align: center;
    margin-bottom: 30px;
}

.auth-header h1 {
    color: #333;
    font-size: 28px;
    margin-bottom: 8px;
}

.auth-header p {
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
}

.form-group input:focus {
    outline: none;
    border-color: #667eea;
    box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.submit-btn {
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

.submit-btn:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 20px rgba(102, 126, 234, 0.3);
}

.submit-btn:disabled {
    background: #ccc;
    cursor: not-allowed;
}
CSSEOF

echo "✅ Created unified-auth.css"

echo -e "\n4. Setting permissions..."
chmod 644 login.html
chmod -R 644 css/
echo "✅ Set proper permissions"

echo -e "\n✅ LOGIN PAGE STYLING FIXED\!"
echo "============================"
echo ""
echo "Your login page now has:"
echo "✓ Beautiful gradient background"
echo "✓ Modern card-based design"
echo "✓ Smooth animations"
echo "✓ Professional form styling"
echo "✓ Responsive design"
echo "✓ Google sign-in button"
echo "✓ All styles inline (no CSS dependencies)"
echo ""
echo "🔗 Check it out: https://bankcsvconverter.com/login.html"
echo ""
echo "The login page now looks professional and modern\! 🎨"

ENDSSH
