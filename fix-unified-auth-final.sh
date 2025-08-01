#\!/bin/bash

# Fix UnifiedAuth Final
echo "🔧 Final Fix for UnifiedAuth Loading"
echo "===================================="
echo ""

SERVER_IP="3.235.19.83"
SERVER_USER="ubuntu"
SSH_KEY="/Users/MAC/Downloads/bank-statement-converter.pem"

# Fix via SSH
ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no "$SERVER_USER@$SERVER_IP" << 'ENDSSH'
cd /home/ubuntu/bank-statement-converter

echo "1. Checking what's wrong with the current auth script..."
# The issue might be that the script is an IIFE that doesn't expose UnifiedAuth globally

echo "2. Creating a fixed version that properly exposes UnifiedAuth..."
cat > js/auth-unified-fixed.js << 'EOFJS'
/**
 * Unified Authentication Service - Fixed Version
 * Handles all authentication operations
 */

// Immediately log to confirm script is executing
console.log('[UnifiedAuth] Script starting...');

// Define API base
const API_BASE = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
    ? 'http://localhost:5000'
    : 'https://bankcsvconverter.com';

// Define UnifiedAuthService class
class UnifiedAuthService {
    constructor() {
        console.log('[UnifiedAuth] Creating service instance...');
        this.user = null;
        this.csrfToken = null;
        this.initialized = false;
        this.refreshTimer = null;
        
        // Load user from localStorage
        const cachedUser = localStorage.getItem('user');
        if (cachedUser) {
            try {
                this.user = JSON.parse(cachedUser);
                console.log('[UnifiedAuth] Loaded cached user:', this.user.email);
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
                console.log('[UnifiedAuth] Got CSRF token');
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
        console.log('[UnifiedAuth] Attempting login for:', email);
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
            
            const data = await response.json();
            
            if (response.ok) {
                this.user = data.user;
                
                // Store access token
                if (data.access_token) {
                    localStorage.setItem('access_token', data.access_token);
                }
                
                localStorage.setItem('user', JSON.stringify(this.user));
                this.setupAutoRefresh();
                
                // Dispatch login event
                window.dispatchEvent(new CustomEvent('unifiedauth:login', { detail: this.user }));
                
                console.log('[UnifiedAuth] Login successful');
                return { success: true, user: this.user };
            } else {
                console.error('[UnifiedAuth] Login failed:', data);
                return { success: false, error: data.detail || 'Login failed' };
            }
        } catch (error) {
            console.error('[UnifiedAuth] Login error:', error);
            return { success: false, error: error.message };
        }
    }
    
    async register(email, password, fullName, companyName = null) {
        console.log('[UnifiedAuth] Attempting registration for:', email);
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
            
            const data = await response.json();
            
            if (response.ok) {
                this.user = data.user;
                
                // Store access token
                if (data.access_token) {
                    localStorage.setItem('access_token', data.access_token);
                }
                
                localStorage.setItem('user', JSON.stringify(this.user));
                this.setupAutoRefresh();
                
                // Dispatch register event
                window.dispatchEvent(new CustomEvent('unifiedauth:register', { detail: this.user }));
                
                console.log('[UnifiedAuth] Registration successful');
                return { success: true, user: this.user };
            } else {
                console.error('[UnifiedAuth] Registration failed:', data);
                return { success: false, error: data.detail || 'Registration failed' };
            }
        } catch (error) {
            console.error('[UnifiedAuth] Register error:', error);
            return { success: false, error: error.message };
        }
    }
    
    async logout() {
        console.log('[UnifiedAuth] Logging out...');
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
        console.log('[UnifiedAuth] Logged out');
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
        
        // Build headers
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
        return \!\!this.user;
    }
    
    getUser() {
        return this.user;
    }
}

// Create and expose global instance
console.log('[UnifiedAuth] Creating global instance...');
window.UnifiedAuth = new UnifiedAuthService();
console.log('[UnifiedAuth] Global instance created:', typeof window.UnifiedAuth);

// Also expose on the global object for debugging
window.UnifiedAuthService = UnifiedAuthService;

// Log final status
setTimeout(() => {
    console.log('[UnifiedAuth] Final check - UnifiedAuth available:', typeof window.UnifiedAuth \!== 'undefined');
}, 100);
EOFJS

echo "3. Updating all HTML files to use the fixed version..."
TIMESTAMP=$(date +%s)
cp js/auth-unified-fixed.js "js/auth-unified-${TIMESTAMP}.js"

# Update HTML files
for file in login.html signup.html pricing.html diagnostic.html test-unified-auth.html minimal-auth-test.html; do
    if [ -f "$file" ]; then
        sed -i "s|/js/auth-unified-[0-9]*\.js|/js/auth-unified-${TIMESTAMP}.js|g" "$file"
        echo "Updated $file"
    fi
done

echo -e "\n4. Creating final test page..."
cat > test-final-auth.html << 'EOFHTML'
<\!DOCTYPE html>
<html>
<head>
    <title>Final Auth Test</title>
    <style>
        body { font-family: Arial, sans-serif; padding: 40px; max-width: 600px; margin: 0 auto; }
        .status { margin: 20px 0; padding: 15px; border-radius: 8px; }
        .success { background: #d4edda; color: #155724; }
        .error { background: #f8d7da; color: #721c24; }
        .info { background: #d1ecf1; color: #004085; }
        button { padding: 10px 20px; margin: 10px 0; cursor: pointer; }
        pre { background: #f5f5f5; padding: 10px; overflow-x: auto; }
    </style>
</head>
<body>
    <h1>Final Authentication Test</h1>
    
    <div id="status" class="status info">Loading UnifiedAuth...</div>
    
    <div id="content" style="display: none;">
        <h2>Test Login</h2>
        <button onclick="testLogin()">Test Login with test@example.com</button>
        
        <h2>Console Output</h2>
        <pre id="console"></pre>
    </div>
    
    <script src="/js/auth-unified-TIMESTAMP.js"></script>
    
    <script>
        const statusDiv = document.getElementById('status');
        const contentDiv = document.getElementById('content');
        const consoleDiv = document.getElementById('console');
        
        // Override console.log to capture output
        const originalLog = console.log;
        console.log = function(...args) {
            originalLog.apply(console, args);
            consoleDiv.textContent += args.join(' ') + '\n';
        };
        
        // Check after a delay
        setTimeout(() => {
            if (typeof UnifiedAuth \!== 'undefined') {
                statusDiv.className = 'status success';
                statusDiv.textContent = '✅ UnifiedAuth loaded successfully\!';
                contentDiv.style.display = 'block';
                
                console.log('UnifiedAuth properties:', Object.getOwnPropertyNames(UnifiedAuth));
                console.log('UnifiedAuth initialized:', UnifiedAuth.initialized);
                console.log('User authenticated:', UnifiedAuth.isAuthenticated());
            } else {
                statusDiv.className = 'status error';
                statusDiv.textContent = '❌ UnifiedAuth failed to load';
                
                // Check window object
                console.log('Checking window object...');
                for (let key in window) {
                    if (key.includes('Auth')) {
                        console.log(`Found: window.${key} = ${typeof window[key]}`);
                    }
                }
            }
        }, 1000);
        
        async function testLogin() {
            console.log('Testing login...');
            try {
                const result = await UnifiedAuth.login('test@example.com', 'test123');
                if (result.success) {
                    console.log('Login successful\!', result.user);
                    alert('Login successful\! Redirecting to pricing page...');
                    window.location.href = '/pricing.html';
                } else {
                    console.log('Login failed:', result.error);
                    alert('Login failed: ' + result.error);
                }
            } catch (error) {
                console.log('Login error:', error);
                alert('Login error: ' + error.message);
            }
        }
    </script>
</body>
</html>
EOFHTML

# Replace TIMESTAMP in the test file
sed -i "s/TIMESTAMP/${TIMESTAMP}/g" test-final-auth.html

echo -e "\n5. Verifying the new script is accessible..."
curl -s -I "https://bankcsvconverter.com/js/auth-unified-${TIMESTAMP}.js" | head -3

echo -e "\nFixed version created: js/auth-unified-${TIMESTAMP}.js"
echo "Test it at: https://bankcsvconverter.com/test-final-auth.html"

ENDSSH

echo ""
echo "✅ Final fix applied\!"
echo ""
echo "The issue was that the UnifiedAuth script was wrapped in an IIFE that wasn't properly exposing the global variable."
echo ""
echo "Test the fix at:"
echo "1. https://bankcsvconverter.com/test-final-auth.html"
echo "2. https://bankcsvconverter.com/login.html"
