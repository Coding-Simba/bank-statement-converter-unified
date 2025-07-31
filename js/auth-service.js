/**
 * Modern Authentication Service using HTTP-only cookies
 * Replaces all localStorage-based authentication
 */

class AuthService {
    constructor() {
        this.baseURL = window.location.origin;
        this.csrfToken = null;
        this.user = null;
        this.initialized = false;
        this.refreshInProgress = false;
        
        // Check for saved user data (non-sensitive)
        const savedUser = localStorage.getItem('user');
        if (savedUser) {
            try {
                this.user = JSON.parse(savedUser);
            } catch (e) {
                localStorage.removeItem('user');
            }
        }
    }
    
    /**
     * Initialize the auth service - get CSRF token
     */
    async initialize() {
        if (this.initialized) return;
        
        try {
            const response = await fetch('/api/auth/csrf', {
                credentials: 'include'
            });
            
            if (response.ok) {
                const data = await response.json();
                this.csrfToken = data.csrf_token;
                this.initialized = true;
            }
        } catch (error) {
            console.error('[AuthService] Failed to get CSRF token:', error);
        }
        
        // Check authentication status
        await this.checkAuth();
    }
    
    /**
     * Check if user is authenticated
     */
    async checkAuth() {
        try {
            const response = await fetch('/api/auth/check', {
                credentials: 'include'
            });
            
            if (response.ok) {
                const data = await response.json();
                if (data.authenticated && data.user) {
                    this.user = data.user;
                    localStorage.setItem('user', JSON.stringify(this.user));
                } else {
                    this.user = null;
                    localStorage.removeItem('user');
                }
            }
        } catch (error) {
            console.error('[AuthService] Auth check failed:', error);
        }
    }
    
    /**
     * Login with email and password
     */
    async login(email, password) {
        await this.initialize();
        
        const response = await fetch('/api/auth/login', {
            method: 'POST',
            credentials: 'include',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRF-Token': this.csrfToken
            },
            body: JSON.stringify({ email, password })
        });
        
        if (response.ok) {
            const data = await response.json();
            this.user = data.user;
            localStorage.setItem('user', JSON.stringify(this.user));
            return { success: true, user: this.user };
        } else {
            const error = await response.json();
            return { success: false, error: error.detail || 'Login failed' };
        }
    }
    
    /**
     * Register new user
     */
    async register(email, password, fullName, companyName) {
        await this.initialize();
        
        const response = await fetch('/api/auth/register', {
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
            localStorage.setItem('user', JSON.stringify(this.user));
            return { success: true, user: this.user };
        } else {
            const error = await response.json();
            return { success: false, error: error.detail || 'Registration failed' };
        }
    }
    
    /**
     * Logout user
     */
    async logout() {
        await this.initialize();
        
        try {
            await fetch('/api/auth/logout', {
                method: 'POST',
                credentials: 'include',
                headers: {
                    'X-CSRF-Token': this.csrfToken
                }
            });
        } catch (error) {
            console.error('[AuthService] Logout error:', error);
        }
        
        this.user = null;
        localStorage.removeItem('user');
        window.location.href = '/login.html';
    }
    
    /**
     * Refresh access token
     */
    async refreshToken() {
        if (this.refreshInProgress) {
            // Wait for existing refresh to complete
            await new Promise(resolve => {
                const checkInterval = setInterval(() => {
                    if (!this.refreshInProgress) {
                        clearInterval(checkInterval);
                        resolve();
                    }
                }, 100);
            });
            return true;
        }
        
        this.refreshInProgress = true;
        
        try {
            const response = await fetch('/api/auth/refresh', {
                method: 'POST',
                credentials: 'include',
                headers: {
                    'X-CSRF-Token': this.csrfToken
                }
            });
            
            if (response.ok) {
                return true;
            } else {
                // Refresh failed - user needs to login again
                this.user = null;
                localStorage.removeItem('user');
                return false;
            }
        } catch (error) {
            console.error('[AuthService] Token refresh failed:', error);
            return false;
        } finally {
            this.refreshInProgress = false;
        }
    }
    
    /**
     * Make authenticated API request with automatic token refresh
     */
    async fetch(url, options = {}) {
        await this.initialize();
        
        // Add credentials and CSRF token
        const fetchOptions = {
            ...options,
            credentials: 'include',
            headers: {
                ...options.headers,
                'X-CSRF-Token': this.csrfToken
            }
        };
        
        // First attempt
        let response = await fetch(url, fetchOptions);
        
        // If 401, try to refresh token
        if (response.status === 401 && !url.includes('/auth/')) {
            const refreshed = await this.refreshToken();
            if (refreshed) {
                // Retry request
                response = await fetch(url, fetchOptions);
            } else {
                // Redirect to login
                window.location.href = '/login.html';
            }
        }
        
        return response;
    }
    
    /**
     * Check if user is authenticated (synchronous)
     */
    isAuthenticated() {
        return !!this.user;
    }
    
    /**
     * Get current user data
     */
    getUser() {
        return this.user;
    }
    
    /**
     * Update UI based on authentication status
     */
    updateUI() {
        const loginBtn = document.getElementById('loginBtn');
        const signupBtn = document.getElementById('signupBtn');
        const userMenu = document.getElementById('userMenu');
        const userEmail = document.getElementById('userEmail');
        
        if (this.isAuthenticated()) {
            // Hide login/signup buttons
            if (loginBtn) loginBtn.style.display = 'none';
            if (signupBtn) signupBtn.style.display = 'none';
            
            // Show user menu
            if (userMenu) {
                userMenu.style.display = 'flex';
                if (userEmail) {
                    userEmail.textContent = this.user.email;
                }
            }
            
            // Update any auth-dependent elements
            document.querySelectorAll('[data-auth="required"]').forEach(el => {
                el.style.display = '';
            });
            document.querySelectorAll('[data-auth="guest"]').forEach(el => {
                el.style.display = 'none';
            });
        } else {
            // Show login/signup buttons
            if (loginBtn) loginBtn.style.display = 'block';
            if (signupBtn) signupBtn.style.display = 'block';
            
            // Hide user menu
            if (userMenu) userMenu.style.display = 'none';
            
            // Update any auth-dependent elements
            document.querySelectorAll('[data-auth="required"]').forEach(el => {
                el.style.display = 'none';
            });
            document.querySelectorAll('[data-auth="guest"]').forEach(el => {
                el.style.display = '';
            });
        }
    }
}

// Create global instance
window.authService = new AuthService();

// Initialize on DOM ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', async () => {
        await window.authService.initialize();
        window.authService.updateUI();
    });
} else {
    // DOM already loaded
    (async () => {
        await window.authService.initialize();
        window.authService.updateUI();
    })();
}

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = AuthService;
}