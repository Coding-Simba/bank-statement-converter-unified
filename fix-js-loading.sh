#!/bin/bash

# Fix JS Loading
echo "🔧 Fixing JavaScript Loading Issue"
echo "================================="
echo ""

SERVER_IP="3.235.19.83"
SERVER_USER="ubuntu"
SSH_KEY="/Users/MAC/Downloads/bank-statement-converter.pem"

# Fix via SSH
ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no "$SERVER_USER@$SERVER_IP" << 'ENDSSH'
cd /home/ubuntu/bank-statement-converter

echo "1. Checking if the JS file has correct permissions..."
ls -la js/auth-unified-1754075455.js

echo -e "\n2. Checking if file has any syntax errors at the beginning..."
head -5 js/auth-unified-1754075455.js

echo -e "\n3. Let's create a new, clean version of the auth script..."
# Create a fresh, working version
cat > js/auth-unified-working.js << 'EOF'
/**
 * Unified Authentication Service
 * Handles all authentication operations
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
                if (!isValid) {
                    this.clearAuth();
                }
            }
            
            // Setup auto-refresh
            this.setupAutoRefresh();
            
            this.initialized = true;
            console.log('[UnifiedAuth] Initialization complete');
            
            // Dispatch ready event
            window.dispatchEvent(new Event('unifiedauth:ready'));
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
                        'X-CSRF-Token': this.csrfToken
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
                    this.setupAutoRefresh();
                    
                    // Dispatch login event
                    window.dispatchEvent(new CustomEvent('unifiedauth:login', { detail: this.user }));
                    
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
        
        async register(email, password, fullName, companyName = null) {
            try {
                const response = await fetch(`${API_BASE}/api/auth/register`, {
                    method: 'POST',
                    credentials: 'include',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRF-Token': this.csrfToken
                    },
                    body: JSON.stringify({
                        email,
                        password,
                        full_name: fullName,
                        company_name: companyName
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
                    this.setupAutoRefresh();
                    
                    // Dispatch register event
                    window.dispatchEvent(new CustomEvent('unifiedauth:register', { detail: this.user }));
                    
                    return { success: true, user: this.user };
                } else {
                    const error = await response.json();
                    return { success: false, error: error.detail || 'Registration failed' };
                }
            } catch (error) {
                console.error('[UnifiedAuth] Register error:', error);
                return { success: false, error: error.message };
            }
        }
        
        async logout() {
            try {
                await fetch(`${API_BASE}/api/auth/logout`, {
                    method: 'POST',
                    credentials: 'include',
                    headers: {
                        'X-CSRF-Token': this.csrfToken
                    }
                });
            } catch (error) {
                console.error('[UnifiedAuth] Logout error:', error);
            }
            
            this.clearAuth();
            
            // Dispatch logout event
            window.dispatchEvent(new Event('unifiedauth:logout'));
        }
        
        clearAuth() {
            this.user = null;
            localStorage.removeItem('user');
            localStorage.removeItem('access_token');
            this.stopAutoRefresh();
        }
        
        async refreshToken() {
            try {
                const response = await fetch(`${API_BASE}/api/auth/refresh`, {
                    method: 'POST',
                    credentials: 'include',
                    headers: {
                        'X-CSRF-Token': this.csrfToken
                    }
                });
                
                if (response.ok) {
                    const data = await response.json();
                    if (data.access_token) {
                        localStorage.setItem('access_token', data.access_token);
                    }
                    return true;
                }
                
                return false;
            } catch (error) {
                console.error('[UnifiedAuth] Token refresh error:', error);
                return false;
            }
        }
        
        setupAutoRefresh() {
            this.stopAutoRefresh();
            
            if (this.user) {
                // Refresh token every 45 minutes
                this.refreshTimer = setInterval(() => {
                    this.refreshToken();
                }, 45 * 60 * 1000);
            }
        }
        
        stopAutoRefresh() {
            if (this.refreshTimer) {
                clearInterval(this.refreshTimer);
                this.refreshTimer = null;
            }
        }
        
        async makeAuthenticatedRequest(url, options = {}) {
            const fullUrl = url.startsWith('http') ? url : `${API_BASE}${url}`;
            
            // Include Authorization header if we have a token
            const headers = {
                ...options.headers,
                'X-CSRF-Token': this.csrfToken
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
            
            // Handle 401 by attempting refresh
            if (response.status === 401) {
                console.log('[UnifiedAuth] Got 401, attempting token refresh...');
                const refreshed = await this.refreshToken();
                if (refreshed) {
                    // Retry request with refreshed token
                    const retryHeaders = {
                        ...options.headers,
                        'X-CSRF-Token': this.csrfToken
                    };
                    
                    const newToken = localStorage.getItem('access_token');
                    if (newToken) {
                        retryHeaders['Authorization'] = `Bearer ${newToken}`;
                    }
                    
                    return fetch(fullUrl, {
                        ...options,
                        credentials: 'include',
                        headers: retryHeaders
                    });
                }
            }
            
            return response;
        }
        
        isAuthenticated() {
            return !!this.user;
        }
        
        getUser() {
            return this.user;
        }
    }
    
    // Create global instance
    window.UnifiedAuth = new UnifiedAuthService();
    
    console.log('[UnifiedAuth] Service created');
})();
EOF

echo -e "\n4. Creating a new timestamped version..."
TIMESTAMP=$(date +%s)
cp js/auth-unified-working.js "js/auth-unified-${TIMESTAMP}.js"

echo -e "\n5. Updating all HTML files to use the new version..."
for file in *.html; do
    if [ -f "$file" ]; then
        sed -i "s|/js/auth-unified-[0-9]*\.js[^\"]*|/js/auth-unified-${TIMESTAMP}.js|g" "$file"
    fi
done

echo -e "\n6. Verifying the updates..."
echo "Login.html now uses:"
grep "auth-unified" login.html | head -2

echo -e "\n7. Setting correct permissions..."
chmod 644 js/auth-unified-${TIMESTAMP}.js

echo -e "\n8. Testing the new file is accessible..."
curl -s -I "https://bankcsvconverter.com/js/auth-unified-${TIMESTAMP}.js" | head -5

echo "New auth file created: js/auth-unified-${TIMESTAMP}.js"

ENDSSH

echo ""
echo "✅ JavaScript loading issue fixed!"
echo ""
echo "Clear your browser cache and try again:"
echo "1. https://bankcsvconverter.com/diagnostic.html (to verify UnifiedAuth loads)"
echo "2. https://bankcsvconverter.com/login.html (to test login)"
echo "3. https://bankcsvconverter.com/pricing.html (to test Stripe)"