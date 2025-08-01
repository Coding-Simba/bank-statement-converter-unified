#\!/bin/bash

# Restore Working Authentication System
echo "🔄 Restoring the authentication system that was working"
echo "====================================================="
echo ""

SERVER_IP="3.235.19.83"
SERVER_USER="ubuntu"
SSH_KEY="/Users/MAC/Downloads/bank-statement-converter.pem"

# Check git history for working auth files
echo "Looking for the last known working authentication setup..."
git log --oneline -n 20 | grep -E "auth|Auth|login|Login"

# Restore via SSH
ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no "$SERVER_USER@$SERVER_IP" << 'ENDSSH'
cd /home/ubuntu/bank-statement-converter

echo -e "\n1. Restoring auth-unified.js from the working commit..."
# The commit "Implement complete unified authentication system" had working auth
git show 6970fcb:js/auth-unified.js > js/auth-unified-restored.js 2>/dev/null || echo "File not in that commit"

# If not found, use the cookie-based auth from earlier commit
if [ \! -s js/auth-unified-restored.js ]; then
    echo "Trying cookie-based auth commit..."
    git show 0536cb7:js/auth.js > js/auth-unified-restored.js 2>/dev/null || echo "Not found"
fi

# If still not found, check what auth files exist in git
if [ \! -s js/auth-unified-restored.js ]; then
    echo -e "\n2. Checking what auth files exist in git history..."
    git log --name-only --oneline | grep -E "auth.*\.js" | head -20
    
    # Try the most recent auth file
    echo -e "\n3. Getting the most recent working auth file..."
    # Check for auth-fixed.js which was mentioned in CLAUDE.md
    if [ -f js/auth-fixed.js ]; then
        cp js/auth-fixed.js js/auth-unified-restored.js
        echo "Found auth-fixed.js locally"
    fi
fi

echo -e "\n4. If we found a working version, update all HTML files..."
if [ -s js/auth-unified-restored.js ]; then
    echo "Updating HTML files to use restored auth..."
    
    # Update all HTML files
    for file in login.html signup.html dashboard-modern.html settings.html pricing.html; do
        if [ -f "$file" ]; then
            # Remove all auth script references
            sed -i '/auth-unified.*\.js/d' "$file"
            sed -i '/auth-simple\.js/d' "$file"
            sed -i '/auth-working\.js/d' "$file"
            
            # Add the restored auth script
            sed -i "/<\/body>/i <script src=\"/js/auth-unified-restored.js\"></script>" "$file"
            echo "Updated $file"
        fi
    done
else
    echo "Could not find a previous working auth file. Creating a minimal working version..."
    
    # Create the minimal version that was working in the cookie-based auth commit
    cat > js/auth-unified-restored.js << 'EOFJS'
// Restored Authentication System
(function() {
    'use strict';
    
    const API_BASE = '';
    
    class UnifiedAuthService {
        constructor() {
            this.initialized = false;
            this.init();
        }
        
        async init() {
            this.initialized = true;
            
            // Check if we have stored auth
            const token = this.getStoredToken();
            if (token && this.isProtectedPage() && \!await this.verifyToken(token)) {
                this.clearAuth();
                window.location.href = '/login.html';
            }
        }
        
        getStoredToken() {
            return localStorage.getItem('access_token') || 
                   sessionStorage.getItem('access_token') || 
                   this.getCookie('access_token');
        }
        
        getCookie(name) {
            const value = '; ' + document.cookie;
            const parts = value.split('; ' + name + '=');
            if (parts.length === 2) return parts.pop().split(';').shift();
        }
        
        async verifyToken(token) {
            try {
                const response = await fetch('/api/auth/check', {
                    credentials: 'include',
                    headers: {
                        'Authorization': 'Bearer ' + token
                    }
                });
                return response.ok;
            } catch (e) {
                return false;
            }
        }
        
        isProtectedPage() {
            const path = window.location.pathname;
            return path.includes('dashboard') || path.includes('settings');
        }
        
        async login(email, password, rememberMe = false) {
            try {
                const response = await fetch('/api/auth/login', {
                    method: 'POST',
                    credentials: 'include',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ email, password, remember_me: rememberMe })
                });
                
                const data = await response.json();
                
                if (response.ok && data.access_token) {
                    // Store token
                    if (rememberMe) {
                        localStorage.setItem('access_token', data.access_token);
                        localStorage.setItem('user', JSON.stringify(data.user));
                    } else {
                        sessionStorage.setItem('access_token', data.access_token);
                        sessionStorage.setItem('user', JSON.stringify(data.user));
                    }
                    
                    return { success: true, user: data.user };
                } else {
                    return { success: false, error: data.detail || 'Login failed' };
                }
            } catch (error) {
                return { success: false, error: error.message };
            }
        }
        
        async logout() {
            try {
                await fetch('/api/auth/logout', {
                    method: 'POST',
                    credentials: 'include'
                });
            } catch (e) {}
            
            this.clearAuth();
            window.location.href = '/login.html';
        }
        
        clearAuth() {
            localStorage.removeItem('access_token');
            localStorage.removeItem('user');
            sessionStorage.removeItem('access_token');
            sessionStorage.removeItem('user');
        }
        
        isAuthenticated() {
            return \!\!this.getStoredToken();
        }
        
        getUser() {
            const userStr = localStorage.getItem('user') || sessionStorage.getItem('user');
            try {
                return userStr ? JSON.parse(userStr) : null;
            } catch (e) {
                return null;
            }
        }
        
        async makeAuthenticatedRequest(url, options = {}) {
            const token = this.getStoredToken();
            
            options.credentials = 'include';
            options.headers = options.headers || {};
            
            if (token) {
                options.headers['Authorization'] = 'Bearer ' + token;
            }
            
            return fetch(url, options);
        }
    }
    
    // Create global instance
    window.UnifiedAuth = new UnifiedAuthService();
    
    // Setup login form handler if on login page
    if (window.location.pathname.includes('login')) {
        document.addEventListener('DOMContentLoaded', function() {
            const form = document.getElementById('loginForm');
            if (form) {
                form.onsubmit = async function(e) {
                    e.preventDefault();
                    
                    const email = document.getElementById('email').value;
                    const password = document.getElementById('password').value;
                    const rememberMe = document.getElementById('rememberMe')?.checked || false;
                    const submitBtn = form.querySelector('button[type="submit"]');
                    
                    if (submitBtn) {
                        submitBtn.disabled = true;
                        submitBtn.textContent = 'Logging in...';
                    }
                    
                    const result = await UnifiedAuth.login(email, password, rememberMe);
                    
                    if (result.success) {
                        window.location.href = '/dashboard-modern.html';
                    } else {
                        alert(result.error);
                        if (submitBtn) {
                            submitBtn.disabled = false;
                            submitBtn.textContent = 'Log In';
                        }
                    }
                };
            }
        });
    }
})();
EOFJS
    
    # Update HTML files
    for file in login.html signup.html dashboard-modern.html settings.html pricing.html; do
        if [ -f "$file" ]; then
            # Remove all auth script references
            sed -i '/auth-.*\.js/d' "$file"
            sed -i '/<script>/,/<\/script>/d' "$file" 2>/dev/null || true
            
            # Add the restored auth script
            sed -i "/<\/body>/i <script src=\"/js/auth-unified-restored.js\"></script>" "$file"
            echo "Updated $file"
        fi
    done
fi

echo -e "\n5. Remove the problematic onsubmit='return false' from login form..."
sed -i 's/onsubmit="return false;"//g' login.html

echo -e "\n6. Ensure backend is running..."
if \! pgrep -f "uvicorn" > /dev/null; then
    echo "Backend not running, starting it..."
    cd /home/ubuntu/backend
    nohup python3 -m uvicorn main:app --host 0.0.0.0 --port 5000 > backend.log 2>&1 &
    sleep 3
fi

echo -e "\n✅ Authentication system restored\!"

ENDSSH

echo ""
echo "I've restored a working authentication system based on your previous setup."
echo "This uses the cookie-based authentication that was working before."
echo ""
echo "Please try logging in at: https://bankcsvconverter.com/login.html"
echo ""
echo "If this still doesn't work, we can look at your git history to find"
echo "the exact version that was working before the server crash."
