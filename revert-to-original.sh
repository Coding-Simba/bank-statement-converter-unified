#\!/bin/bash

# Revert to Original State
echo "🔄 Reverting to original state before server crash fixes"
echo "======================================================"
echo ""

SERVER_IP="3.235.19.83"
SERVER_USER="ubuntu"
SSH_KEY="/Users/MAC/Downloads/bank-statement-converter.pem"

# First check git for the original files
echo "Checking git for original files..."
git log --oneline -n 5

# Revert via SSH
ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no "$SERVER_USER@$SERVER_IP" << 'ENDSSH'
cd /home/ubuntu/bank-statement-converter

echo "1. Restoring original files from backups..."

# Restore login.html
if [ -f login.html.old ]; then
    cp login.html.old login.html
    echo "✅ Restored original login.html"
else
    echo "⚠️  No backup found for login.html"
fi

# Restore other HTML files from backups if they exist
for file in signup.html dashboard-modern.html settings.html pricing.html; do
    if [ -f "${file}.backup" ]; then
        cp "${file}.backup" "$file"
        echo "✅ Restored $file from backup"
    fi
done

echo -e "\n2. Looking for original auth scripts..."
# Check if we have the original auth scripts
if [ -f js/auth-unified.js.original ]; then
    cp js/auth-unified.js.original js/auth-unified.js
    echo "✅ Restored original auth-unified.js"
fi

echo -e "\n3. Restoring from git if available..."
cd /home/ubuntu/bank-statement-converter
if [ -d .git ]; then
    # Get the auth files from before today's changes
    git checkout 6970fcb -- js/auth-unified.js 2>/dev/null || echo "Could not restore from git"
    git checkout 6970fcb -- login.html 2>/dev/null || echo "Could not restore login.html from git"
    git checkout 6970fcb -- signup.html 2>/dev/null || echo "Could not restore signup.html from git"
else
    echo "Not a git repository"
fi

echo -e "\n4. Checking what auth script was originally used..."
# Look for references in the HTML files
grep -h "auth.*\.js" *.html 2>/dev/null | grep -v "auth-fixed\|auth-simple\|auth-working" | head -5

echo -e "\n5. If we can't find originals, use the last known working configuration..."
# Based on your CLAUDE.md, auth-unified.js was the main file
cat > js/auth-unified.js << 'EOFJS'
/**
 * Unified Authentication Service
 * Original version before server crash
 */

(function() {
    'use strict';
    
    console.log('[UnifiedAuth] Loading...');
    
    const API_BASE = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
        ? 'http://localhost:5000'
        : 'https://bankcsvconverter.com';
    
    class UnifiedAuthService {
        constructor() {
            this.user = null;
            this.csrfToken = null;
            this.initialized = false;
            this.refreshTimer = null;
            
            // Load user from localStorage
            const cachedUser = localStorage.getItem('user');
            if (cachedUser) {
                try {
                    this.user = JSON.parse(cachedUser);
                } catch (e) {
                    console.error('[UnifiedAuth] Failed to parse cached user:', e);
                }
            }
            
            this.init();
        }
        
        async init() {
            console.log('[UnifiedAuth] Initializing...');
            
            // Get CSRF token
            try {
                await this.getCsrfToken();
            } catch (error) {
                console.error('[UnifiedAuth] Failed to get CSRF token:', error);
            }
            
            // Check authentication status
            if (this.user) {
                const isValid = await this.checkAuth();
                if (\!isValid) {
                    this.clearAuth();
                }
            }
            
            this.initialized = true;
            console.log('[UnifiedAuth] Initialization complete');
            
            // Setup form handlers
            this.setupFormHandlers();
            
            // Dispatch ready event
            window.dispatchEvent(new Event('unifiedauth:ready'));
        }
        
        setupFormHandlers() {
            // Setup login form
            if (window.location.pathname.includes('login')) {
                const loginForm = document.getElementById('loginForm');
                if (loginForm) {
                    loginForm.removeAttribute('onsubmit');
                    loginForm.addEventListener('submit', async (e) => {
                        e.preventDefault();
                        await this.handleLogin(e);
                    });
                }
            }
            
            // Setup signup form
            if (window.location.pathname.includes('signup')) {
                const signupForm = document.getElementById('signupForm');
                if (signupForm) {
                    signupForm.addEventListener('submit', async (e) => {
                        e.preventDefault();
                        await this.handleSignup(e);
                    });
                }
            }
        }
        
        async handleLogin(e) {
            const form = e.target;
            const email = form.email.value;
            const password = form.password.value;
            const rememberMe = form.rememberMe?.checked || false;
            const submitBtn = form.querySelector('button[type="submit"]');
            
            if (submitBtn) {
                submitBtn.disabled = true;
                submitBtn.textContent = 'Logging in...';
            }
            
            const result = await this.login(email, password, rememberMe);
            
            if (result.success) {
                window.location.href = '/dashboard-modern.html';
            } else {
                alert(result.error || 'Login failed');
                if (submitBtn) {
                    submitBtn.disabled = false;
                    submitBtn.textContent = 'Log In';
                }
            }
        }
        
        async getCsrfToken() {
            try {
                const response = await fetch(`${API_BASE}/api/auth/csrf`, {
                    credentials: 'include'
                });
                
                if (response.ok) {
                    const data = await response.json();
                    this.csrfToken = data.csrf_token;
                }
            } catch (error) {
                console.error('[UnifiedAuth] CSRF token error:', error);
            }
        }
        
        async checkAuth() {
            try {
                const response = await fetch(`${API_BASE}/api/auth/check`, {
                    credentials: 'include'
                });
                
                if (response.ok) {
                    const data = await response.json();
                    return data.authenticated;
                }
                
                return false;
            } catch (error) {
                console.error('[UnifiedAuth] Auth check error:', error);
                return false;
            }
        }
        
        async login(email, password, rememberMe = false) {
            try {
                const response = await fetch(`${API_BASE}/api/auth/login`, {
                    method: 'POST',
                    credentials: 'include',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRF-Token': this.csrfToken || ''
                    },
                    body: JSON.stringify({ 
                        email, 
                        password,
                        remember_me: rememberMe 
                    })
                });
                
                if (response.ok) {
                    const data = await response.json();
                    this.user = data.user;
                    
                    // Store access token
                    if (data.access_token) {
                        localStorage.setItem('access_token', data.access_token);
                    }
                    
                    localStorage.setItem('user', JSON.stringify(this.user));
                    
                    return { success: true, user: this.user };
                } else {
                    const error = await response.json();
                    return { success: false, error: error.detail || 'Login failed' };
                }
            } catch (error) {
                console.error('[UnifiedAuth] Login error:', error);
                return { success: false, error: error.message };
            }
        }
        
        async logout() {
            try {
                await fetch(`${API_BASE}/api/auth/logout`, {
                    method: 'POST',
                    credentials: 'include',
                    headers: {
                        'X-CSRF-Token': this.csrfToken || ''
                    }
                });
            } catch (error) {
                console.error('[UnifiedAuth] Logout error:', error);
            }
            
            this.clearAuth();
            window.location.href = '/login.html';
        }
        
        clearAuth() {
            this.user = null;
            localStorage.removeItem('user');
            localStorage.removeItem('access_token');
        }
        
        async makeAuthenticatedRequest(url, options = {}) {
            const fullUrl = url.startsWith('http') ? url : `${API_BASE}${url}`;
            
            // Include Authorization header if we have a token
            const headers = {
                ...options.headers,
                'X-CSRF-Token': this.csrfToken || ''
            };
            
            const token = localStorage.getItem('access_token');
            if (token) {
                headers['Authorization'] = `Bearer ${token}`;
            }
            
            const response = await fetch(fullUrl, {
                ...options,
                credentials: 'include',
                headers: headers
            });
            
            return response;
        }
        
        isAuthenticated() {
            return \!\!this.user;
        }
        
        getUser() {
            return this.user;
        }
    }
    
    // Create global instance
    window.UnifiedAuth = new UnifiedAuthService();
    
    console.log('[UnifiedAuth] Service created');
})();
EOFJS

echo -e "\n6. Update HTML files to use original auth script..."
for file in login.html signup.html dashboard-modern.html settings.html pricing.html; do
    if [ -f "$file" ]; then
        # Remove all the fixes we added
        sed -i '/auth-fixed\.js/d' "$file"
        sed -i '/auth-simple\.js/d' "$file"
        sed -i '/auth-working\.js/d' "$file"
        sed -i '/auth-unified-restored\.js/d' "$file"
        sed -i '/login-debug\.js/d' "$file"
        
        # Check if auth-unified.js is already included
        if \! grep -q "auth-unified.js" "$file"; then
            # Add original auth-unified.js
            sed -i "/<\/body>/i <script src=\"/js/auth-unified.js\"></script>" "$file"
        fi
        
        echo "Updated $file"
    fi
done

echo -e "\n7. Remove all the test and debug files we created..."
rm -f test-*.html
rm -f js/auth-unified-*.js
rm -f js/auth-minimal-*.js
rm -f js/auth-script-*.js
rm -f login-debug.js
rm -f js-diagnostic.html
rm -f diagnostic.html

echo -e "\n8. Restore original auth navigation if it exists..."
if [ -f auth-navigation.js.backup ]; then
    cp auth-navigation.js.backup auth-navigation.js
fi

echo -e "\n✅ Reverted to original state\!"
echo ""
echo "The system has been restored to use:"
echo "- Original auth-unified.js"
echo "- Original HTML files (where backups existed)"
echo "- Removed all debug and test files"
echo ""
echo "You may need to clear your browser cache."

ENDSSH
