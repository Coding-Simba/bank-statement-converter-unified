#!/bin/bash

echo "🔥 FIXING ALL AUTH ISSUES NOW!"

# Create a fixed version of auth-unified.js
cat > auth-unified-fixed.js << 'EOF'
/**
 * Unified Authentication System - FIXED VERSION
 * Handles all authentication with HTTP-only cookies
 */

(function() {
    'use strict';
    
    // Configuration
    const API_BASE = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
        ? 'http://localhost:5000'
        : `${window.location.protocol}//${window.location.hostname}`;
    
    // Use MODERN dashboard
    const DASHBOARD_URL = '/dashboard-modern.html';
    
    class UnifiedAuthService {
        constructor() {
            this.csrfToken = null;
            this.user = null;
            this.initialized = false;
            this.refreshTimer = null;
            
            // Check for cached user data
            const cachedUser = localStorage.getItem('user');
            if (cachedUser) {
                try {
                    this.user = JSON.parse(cachedUser);
                } catch (e) {
                    localStorage.removeItem('user');
                }
            }
            
            // Set up cross-tab communication
            this.setupCrossTabSync();
        }
        
        setupCrossTabSync() {
            // Listen for BroadcastChannel messages
            if (typeof BroadcastChannel !== 'undefined') {
                this.authChannel = new BroadcastChannel('auth-channel');
                this.authChannel.onmessage = (event) => {
                    if (event.data.type === 'logout') {
                        this.handleCrossTabLogout();
                    } else if (event.data.type === 'login') {
                        // Sync login across tabs
                        this.user = event.data.user;
                        localStorage.setItem('user', JSON.stringify(this.user));
                        this.updateUI();
                    }
                };
            }
            
            // Listen for localStorage changes as fallback
            window.addEventListener('storage', (event) => {
                if (event.key === 'auth-logout-event') {
                    this.handleCrossTabLogout();
                } else if (event.key === 'user' && event.newValue) {
                    // Sync user data across tabs
                    try {
                        this.user = JSON.parse(event.newValue);
                        this.updateUI();
                    } catch (e) {
                        console.error('[UnifiedAuth] Error parsing user data:', e);
                    }
                }
            });
        }
        
        handleCrossTabLogout() {
            console.log('[UnifiedAuth] Logout detected from another tab');
            this.user = null;
            localStorage.removeItem('user');
            localStorage.removeItem('user_data');
            this.clearTokenRefresh();
            this.updateUI();
            
            // Show notification to user
            if (window.location.pathname !== '/') {
                alert('You have been logged out from another tab.');
                window.location.href = '/';
            }
        }
        
        async initialize() {
            if (this.initialized) return;
            
            console.log('[UnifiedAuth] Initializing...');
            
            try {
                // Get CSRF token
                await this.getCsrfToken();
                
                // Check authentication status
                await this.checkAuth();
                
                // Setup automatic token refresh
                this.setupTokenRefresh();
                
                // Update UI
                this.updateUI();
                
                this.initialized = true;
                console.log('[UnifiedAuth] Initialization complete');
            } catch (error) {
                console.error('[UnifiedAuth] Initialization error:', error);
            }
        }
        
        async getCsrfToken() {
            try {
                const response = await fetch(`${API_BASE}/v2/api/auth/csrf`, {
                    credentials: 'include'
                });
                const data = await response.json();
                this.csrfToken = data.csrf_token;
                console.log('[UnifiedAuth] CSRF token obtained');
            } catch (error) {
                console.error('[UnifiedAuth] CSRF token error:', error);
            }
        }
        
        async checkAuth() {
            try {
                const response = await fetch(`${API_BASE}/v2/api/auth/check`, {
                    credentials: 'include'
                });
                
                if (response.ok) {
                    const data = await response.json();
                    if (data.authenticated && data.user) {
                        this.user = data.user;
                        // Sync across tabs
                        localStorage.setItem('user', JSON.stringify(this.user));
                        localStorage.setItem('user_data', JSON.stringify(this.user));
                        
                        // Notify other tabs of login
                        if (typeof BroadcastChannel !== 'undefined') {
                            const channel = new BroadcastChannel('auth-channel');
                            channel.postMessage({ type: 'login', user: this.user });
                            channel.close();
                        }
                        
                        console.log('[UnifiedAuth] User authenticated:', this.user.email);
                    } else {
                        this.user = null;
                        localStorage.removeItem('user');
                        localStorage.removeItem('user_data');
                    }
                } else {
                    this.user = null;
                    localStorage.removeItem('user');
                    localStorage.removeItem('user_data');
                }
            } catch (error) {
                console.error('[UnifiedAuth] Auth check error:', error);
                this.user = null;
            }
        }
        
        async login(email, password, rememberMe = false) {
            try {
                const response = await fetch(`${API_BASE}/v2/api/auth/login`, {
                    method: 'POST',
                    credentials: 'include',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRF-Token': this.csrfToken
                    },
                    body: JSON.stringify({ email, password, remember_me: rememberMe })
                });
                
                if (response.ok) {
                    const data = await response.json();
                    this.user = data.user;
                    
                    // Store in localStorage for compatibility
                    localStorage.setItem('user', JSON.stringify(this.user));
                    localStorage.setItem('user_data', JSON.stringify(this.user));
                    
                    // Notify other tabs
                    if (typeof BroadcastChannel !== 'undefined') {
                        const channel = new BroadcastChannel('auth-channel');
                        channel.postMessage({ type: 'login', user: this.user });
                        channel.close();
                    }
                    
                    this.setupTokenRefresh();
                    this.updateUI();
                    
                    return { success: true, user: this.user };
                } else {
                    const error = await response.json();
                    return { success: false, error: error.detail || 'Login failed' };
                }
            } catch (error) {
                console.error('[UnifiedAuth] Login error:', error);
                return { success: false, error: 'Network error' };
            }
        }
        
        async register(email, password, fullName, companyName = null) {
            try {
                const response = await fetch(`${API_BASE}/v2/api/auth/register`, {
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
                    
                    // Store in localStorage for compatibility
                    localStorage.setItem('user', JSON.stringify(this.user));
                    localStorage.setItem('user_data', JSON.stringify(this.user));
                    
                    // Check authentication status to ensure cookies are set
                    await this.checkAuth();
                    
                    this.setupTokenRefresh();
                    this.updateUI();
                    
                    return { success: true, user: this.user };
                } else {
                    const error = await response.json();
                    return { success: false, error: error.detail || 'Registration failed' };
                }
            } catch (error) {
                console.error('[UnifiedAuth] Registration error:', error);
                return { success: false, error: 'Network error' };
            }
        }
        
        async logout() {
            try {
                await fetch(`${API_BASE}/v2/api/auth/logout`, {
                    method: 'POST',
                    credentials: 'include',
                    headers: {
                        'X-CSRF-Token': this.csrfToken
                    }
                });
            } catch (error) {
                console.error('[UnifiedAuth] Logout error:', error);
            }
            
            this.user = null;
            localStorage.removeItem('user');
            localStorage.removeItem('user_data');
            
            // Notify other tabs about logout
            this.notifyLogout();
            
            this.clearTokenRefresh();
            
            // Small delay to ensure other tabs get the message
            setTimeout(() => {
                window.location.href = '/';
            }, 100);
        }
        
        notifyLogout() {
            // Use BroadcastChannel if available
            if (typeof BroadcastChannel !== 'undefined') {
                const channel = new BroadcastChannel('auth-channel');
                channel.postMessage({ type: 'logout' });
                channel.close();
            }
            
            // Also use localStorage event as fallback
            localStorage.setItem('auth-logout-event', Date.now().toString());
            localStorage.removeItem('auth-logout-event');
        }
        
        async refreshToken() {
            try {
                const response = await fetch(`${API_BASE}/v2/api/auth/refresh`, {
                    method: 'POST',
                    credentials: 'include',
                    headers: {
                        'X-CSRF-Token': this.csrfToken
                    }
                });
                
                if (response.ok) {
                    console.log('[UnifiedAuth] Token refreshed successfully');
                    return true;
                } else {
                    console.log('[UnifiedAuth] Token refresh failed');
                    return false;
                }
            } catch (error) {
                console.error('[UnifiedAuth] Token refresh error:', error);
                return false;
            }
        }
        
        setupTokenRefresh() {
            // Clear existing timer
            this.clearTokenRefresh();
            
            // Refresh token every 10 minutes
            this.refreshTimer = setInterval(() => {
                this.refreshToken();
            }, 10 * 60 * 1000);
        }
        
        clearTokenRefresh() {
            if (this.refreshTimer) {
                clearInterval(this.refreshTimer);
                this.refreshTimer = null;
            }
        }
        
        async makeAuthenticatedRequest(url, options = {}) {
            const fullUrl = url.startsWith('http') ? url : `${API_BASE}${url}`;
            
            const response = await fetch(fullUrl, {
                ...options,
                credentials: 'include',
                headers: {
                    ...options.headers,
                    'X-CSRF-Token': this.csrfToken
                }
            });
            
            // Handle 401 by attempting refresh
            if (response.status === 401) {
                console.log('[UnifiedAuth] Got 401, attempting token refresh...');
                const refreshed = await this.refreshToken();
                if (refreshed) {
                    // Retry request
                    return fetch(fullUrl, {
                        ...options,
                        credentials: 'include',
                        headers: {
                            ...options.headers,
                            'X-CSRF-Token': this.csrfToken
                        }
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
        
        updateUI() {
            const isAuth = this.isAuthenticated();
            
            // Update navigation
            const loginBtn = document.getElementById('loginBtn');
            const signupBtn = document.getElementById('signupBtn');
            const userMenu = document.getElementById('userMenu');
            const userEmail = document.getElementById('userEmail');
            
            if (loginBtn) loginBtn.style.display = isAuth ? 'none' : 'block';
            if (signupBtn) signupBtn.style.display = isAuth ? 'none' : 'block';
            
            if (userMenu) {
                userMenu.style.display = isAuth ? 'flex' : 'none';
                if (userEmail && this.user) {
                    userEmail.textContent = this.user.email;
                }
            }
            
            // Update any auth-dependent elements
            document.querySelectorAll('[data-auth-required]').forEach(el => {
                el.style.display = isAuth ? 'block' : 'none';
            });
            
            document.querySelectorAll('[data-guest-only]').forEach(el => {
                el.style.display = isAuth ? 'none' : 'block';
            });
        }
    }
    
    // Create and initialize the auth service
    window.UnifiedAuth = new UnifiedAuthService();
    
    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => {
            window.UnifiedAuth.initialize();
        });
    } else {
        window.UnifiedAuth.initialize();
    }
    
    // Handle login form if on login page
    if (window.location.pathname.includes('login')) {
        document.addEventListener('DOMContentLoaded', () => {
            const loginForm = document.getElementById('loginForm');
            if (loginForm) {
                loginForm.addEventListener('submit', async (e) => {
                    e.preventDefault();
                    
                    const email = document.getElementById('email').value;
                    const password = document.getElementById('password').value;
                    const rememberMe = document.getElementById('rememberMe')?.checked || false;
                    
                    const submitBtn = loginForm.querySelector('button[type="submit"]');
                    const originalText = submitBtn.textContent;
                    submitBtn.textContent = 'Signing in...';
                    submitBtn.disabled = true;
                    
                    const result = await window.UnifiedAuth.login(email, password, rememberMe);
                    
                    if (result.success) {
                        const urlParams = new URLSearchParams(window.location.search);
                        const redirect = urlParams.get('redirect') || DASHBOARD_URL;
                        window.location.href = redirect;
                    } else {
                        // Show error
                        alert(result.error);
                        submitBtn.textContent = originalText;
                        submitBtn.disabled = false;
                    }
                });
            }
        });
    }
    
    // Handle signup form if on signup page
    if (window.location.pathname.includes('signup')) {
        document.addEventListener('DOMContentLoaded', () => {
            const signupForm = document.getElementById('signupForm');
            if (signupForm) {
                signupForm.addEventListener('submit', async (e) => {
                    e.preventDefault();
                    
                    const fullName = document.getElementById('fullName').value;
                    const email = document.getElementById('email').value;
                    const password = document.getElementById('password').value;
                    const company = document.getElementById('company')?.value || null;
                    const terms = document.getElementById('terms').checked;
                    
                    if (!terms) {
                        alert('Please accept the terms and conditions');
                        return;
                    }
                    
                    const submitBtn = signupForm.querySelector('button[type="submit"]');
                    const originalText = submitBtn.textContent;
                    submitBtn.textContent = 'Creating account...';
                    submitBtn.disabled = true;
                    
                    const result = await window.UnifiedAuth.register(email, password, fullName, company);
                    
                    if (result.success) {
                        window.location.href = DASHBOARD_URL;
                    } else {
                        // Show error
                        alert(result.error);
                        submitBtn.textContent = originalText;
                        submitBtn.disabled = false;
                    }
                });
            }
        });
    }
    
    // Handle logout links
    document.addEventListener('click', (e) => {
        if (e.target.matches('a[href="/logout"], a[href="#logout"], .logout-btn')) {
            e.preventDefault();
            window.UnifiedAuth.logout();
        }
    });
    
})();
EOF

# Deploy the fix
echo "🚀 Deploying fixed auth system..."

SERVER_IP="3.235.19.83"
SERVER_USER="ubuntu"
KEY_PATH="$HOME/Downloads/bank-statement-converter.pem"

# Upload fixed auth script
scp -i "$KEY_PATH" auth-unified-fixed.js "$SERVER_USER@$SERVER_IP:/tmp/"

# Apply fix on server
ssh -i "$KEY_PATH" "$SERVER_USER@$SERVER_IP" << 'ENDSSH'
    echo "📦 Installing fixed auth system..."
    
    # Backup current version
    sudo cp /home/ubuntu/bank-statement-converter/js/auth-unified.js /home/ubuntu/bank-statement-converter/js/auth-unified.js.backup
    
    # Install fixed version
    sudo cp /tmp/auth-unified-fixed.js /home/ubuntu/bank-statement-converter/js/auth-unified.js
    
    # Clear CloudFlare cache by adding version parameter to all pages
    cd /home/ubuntu/bank-statement-converter
    for file in *.html; do
        if [ -f "$file" ]; then
            # Update auth-unified.js reference to include cache-busting parameter
            sudo sed -i 's|/js/auth-unified.js"|/js/auth-unified.js?v='$(date +%s)'"|g' "$file"
            echo "✓ Updated $file"
        fi
    done
    
    # Restart nginx to clear any server-side caches
    sudo nginx -s reload
    
    echo "✅ Fixed auth system deployed!"
ENDSSH

# Clean up
rm -f auth-unified-fixed.js

echo ""
echo "🎉 AUTHENTICATION FIXED!"
echo ""
echo "The fix includes:"
echo "✅ Redirects to dashboard-modern.html (not old dashboard)"
echo "✅ Better cross-tab synchronization"
echo "✅ Auth persistence across entire site"
echo "✅ Cache-busting to force browser updates"
echo ""
echo "⚡ IMPORTANT: Clear your browser cache or hard refresh (Ctrl+Shift+R)"
echo ""
echo "Test now at: https://bankcsvconverter.com"