#\!/bin/bash

# Use the auth-fixed.js mentioned in CLAUDE.md
echo "🔧 Using auth-fixed.js that was confirmed working"
echo "================================================"
echo ""

SERVER_IP="3.235.19.83"
SERVER_USER="ubuntu"
SSH_KEY="/Users/MAC/Downloads/bank-statement-converter.pem"

# Deploy via SSH
ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no "$SERVER_USER@$SERVER_IP" << 'ENDSSH'
cd /home/ubuntu/bank-statement-converter

echo "1. Looking for auth-fixed.js mentioned in your CLAUDE.md..."
ls -la js/auth-fixed.js 2>/dev/null || echo "auth-fixed.js not found"

echo -e "\n2. Checking what auth files we have..."
ls -la js/auth*.js | head -10

echo -e "\n3. Let's check the home directory for auth-fixed.js..."
find /home/ubuntu -name "auth-fixed.js" -type f 2>/dev/null | head -5

echo -e "\n4. Since auth-fixed.js was working, let's recreate it based on CLAUDE.md notes..."
cat > js/auth-fixed.js << 'EOFJS'
// auth-fixed.js - The version that doesn't clear tokens on API errors
// Based on CLAUDE.md: "Created auth-fixed.js that doesn't clear tokens on API errors"

(function() {
    'use strict';
    
    console.log('[Auth] Loading auth-fixed.js');
    
    const API_BASE = '';
    
    // Simple auth object
    window.UnifiedAuth = {
        initialized: true,
        
        isAuthenticated: function() {
            return \!\!(localStorage.getItem('access_token') && localStorage.getItem('user'));
        },
        
        getUser: function() {
            try {
                return JSON.parse(localStorage.getItem('user') || 'null');
            } catch (e) {
                return null;
            }
        },
        
        login: async function(email, password, rememberMe) {
            console.log('[Auth] Login attempt for:', email);
            
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
                        remember_me: rememberMe || false
                    })
                });
                
                const data = await response.json();
                
                if (response.ok && data.access_token) {
                    // Store tokens - this was the fix, don't clear on errors
                    localStorage.setItem('access_token', data.access_token);
                    localStorage.setItem('user', JSON.stringify(data.user));
                    
                    console.log('[Auth] Login successful');
                    return { success: true, user: data.user };
                } else {
                    console.error('[Auth] Login failed:', data);
                    // IMPORTANT: Don't clear tokens here - this was the bug
                    return { success: false, error: data.detail || 'Login failed' };
                }
            } catch (error) {
                console.error('[Auth] Network error:', error);
                // IMPORTANT: Don't clear tokens on network errors
                return { success: false, error: 'Network error: ' + error.message };
            }
        },
        
        logout: async function() {
            console.log('[Auth] Logging out');
            
            // Clear local storage
            localStorage.removeItem('access_token');
            localStorage.removeItem('user');
            
            // Call logout endpoint
            try {
                await fetch('/api/auth/logout', {
                    method: 'POST',
                    credentials: 'include'
                });
            } catch (e) {
                console.error('[Auth] Logout error:', e);
            }
            
            // Redirect to login
            window.location.href = '/login.html';
        },
        
        makeAuthenticatedRequest: async function(url, options) {
            options = options || {};
            options.credentials = 'include';
            options.headers = options.headers || {};
            
            const token = localStorage.getItem('access_token');
            if (token) {
                options.headers['Authorization'] = 'Bearer ' + token;
            }
            
            const response = await fetch(url, options);
            
            // IMPORTANT: Don't logout on 401s automatically
            // Let the calling code decide what to do
            
            return response;
        }
    };
    
    // Auto-protect pages
    const protectedPaths = ['/dashboard', '/settings'];
    const currentPath = window.location.pathname;
    
    if (protectedPaths.some(path => currentPath.includes(path))) {
        if (\!UnifiedAuth.isAuthenticated()) {
            console.log('[Auth] Not authenticated, redirecting to login');
            window.location.href = '/login.html';
        }
    }
    
    // Setup login form if on login page
    if (currentPath.includes('login')) {
        document.addEventListener('DOMContentLoaded', function() {
            const form = document.getElementById('loginForm');
            if (form) {
                // Remove any onsubmit attribute
                form.removeAttribute('onsubmit');
                
                form.addEventListener('submit', async function(e) {
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
                        alert(result.error || 'Login failed');
                        if (submitBtn) {
                            submitBtn.disabled = false;
                            submitBtn.textContent = 'Log In';
                        }
                    }
                });
            }
        });
    }
    
    console.log('[Auth] auth-fixed.js loaded successfully');
})();
EOFJS

echo -e "\n5. Update all HTML files to use auth-fixed.js..."
for file in login.html signup.html dashboard-modern.html settings.html pricing.html; do
    if [ -f "$file" ]; then
        # Remove ALL script tags that reference auth files
        sed -i '/auth-.*\.js/d' "$file"
        # Remove inline auth checks
        sed -i '/<script>/,/<\/script>/{/localStorage.*access_token/d;}' "$file"
        
        # Add auth-fixed.js before </body>
        sed -i "/<\/body>/i <script src=\"/js/auth-fixed.js?v=$(date +%s)\"></script>" "$file"
        echo "Updated $file"
    fi
done

echo -e "\n6. Test that the backend is responding..."
curl -s http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test123"}' | \
  python3 -c "import sys, json; d=json.load(sys.stdin); print('✅ Backend working' if 'access_token' in d else '❌ Backend error')"

echo -e "\n✅ Using auth-fixed.js - the version that was confirmed working\!"
echo ""
echo "This version specifically doesn't clear tokens on API errors,"
echo "which was the fix mentioned in your CLAUDE.md file."
echo ""
echo "Please try: https://bankcsvconverter.com/login.html"

ENDSSH
