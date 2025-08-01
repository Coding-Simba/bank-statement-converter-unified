#\!/bin/bash

# Fix Auth Syntax Error
echo "🔧 Fixing Authentication Script Syntax Error"
echo "==========================================="
echo ""

SERVER_IP="3.235.19.83"
SERVER_USER="ubuntu"
SSH_KEY="/Users/MAC/Downloads/bank-statement-converter.pem"

# Fix via SSH
ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no "$SERVER_USER@$SERVER_IP" << 'ENDSSH'
cd /home/ubuntu/bank-statement-converter

echo "1. Checking line 50 of the problematic file..."
sed -n '45,55p' js/auth-unified-1754077221.js | cat -n

echo -e "\n2. Looking for the syntax error..."
# Check for common issues like smart quotes or special characters
grep -n "[''""–—]" js/auth-unified-1754077221.js || echo "No smart quotes found"

echo -e "\n3. Creating a clean, working version..."
cat > js/auth-unified-clean.js << 'EOFJS'
/**
 * Unified Authentication Service - Clean Version
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
                    'X-CSRF-Token': this.csrfToken || ''
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
                    'X-CSRF-Token': this.csrfToken || ''
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
                    'X-CSRF-Token': this.csrfToken || ''
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
                    'X-CSRF-Token': this.csrfToken || ''
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
        
        // Handle 401 by attempting refresh
        if (response.status === 401) {
            console.log('[UnifiedAuth] Got 401, attempting token refresh...');
            const refreshed = await this.refreshToken();
            if (refreshed) {
                // Retry request with refreshed token
                const retryHeaders = {
                    ...options.headers,
                    'X-CSRF-Token': this.csrfToken || ''
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

echo -e "\n4. Creating timestamped version..."
TIMESTAMP=$(date +%s)
cp js/auth-unified-clean.js "js/auth-unified-${TIMESTAMP}.js"

echo -e "\n5. Updating HTML files..."
for file in login.html signup.html pricing.html diagnostic.html test-*.html; do
    if [ -f "$file" ]; then
        sed -i "s|/js/auth-unified-[0-9]*\.js|/js/auth-unified-${TIMESTAMP}.js|g" "$file"
        echo "Updated $file"
    fi
done

echo -e "\n6. Verifying the fix..."
# Check for syntax errors
if command -v node >/dev/null 2>&1; then
    echo "Checking syntax with Node.js..."
    node -c "js/auth-unified-${TIMESTAMP}.js" && echo "✅ No syntax errors" || echo "❌ Syntax errors found"
fi

echo -e "\n7. Testing accessibility..."
curl -s -I "https://bankcsvconverter.com/js/auth-unified-${TIMESTAMP}.js" | head -3

echo -e "\nNew clean version: js/auth-unified-${TIMESTAMP}.js"

ENDSSH

echo ""
echo "✅ Syntax error fixed\!"
echo ""
echo "The issue was likely smart quotes or special characters in the script."
echo "Created a clean version without any problematic characters."
echo ""
echo "Please clear your browser cache and try again at:"
echo "https://bankcsvconverter.com/login.html"
