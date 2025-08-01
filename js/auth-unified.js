/**
 * Unified Authentication System
 * Handles all authentication with HTTP-only cookies
 * Replaces all other auth scripts
 */

(function() {
    'use strict';
    
    // Configuration
    const API_BASE = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
        ? 'http://localhost:5000'
        : `${window.location.protocol}//${window.location.hostname}`;
    
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
                const response = await fetch(`${API_BASE}/api/v2/auth/csrf`, {
                    credentials: 'include'
                });
                
                if (response.ok) {
                    const data = await response.json();
                    this.csrfToken = data.csrf_token;
                    console.log('[UnifiedAuth] CSRF token obtained');
                }
            } catch (error) {
                console.error('[UnifiedAuth] Failed to get CSRF token:', error);
            }
        }
        
        async checkAuth() {
            try {
                const response = await fetch(`${API_BASE}/api/v2/auth/check`, {
                    credentials: 'include'
                });
                
                if (response.ok) {
                    const data = await response.json();
                    if (data.authenticated && data.user) {
                        this.user = data.user;
                        localStorage.setItem('user', JSON.stringify(this.user));
                        console.log('[UnifiedAuth] User authenticated:', this.user.email);
                    } else {
                        this.user = null;
                        localStorage.removeItem('user');
                        console.log('[UnifiedAuth] Not authenticated');
                    }
                }
            } catch (error) {
                console.error('[UnifiedAuth] Auth check failed:', error);
            }
        }
        
        async login(email, password, rememberMe = false) {
            try {
                const response = await fetch(`${API_BASE}/api/v2/auth/login`, {
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
                    localStorage.setItem('user', JSON.stringify(this.user));
                    this.setupTokenRefresh();
                    this.updateUI();
                    console.log('[UnifiedAuth] Login successful');
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
        
        async logout() {
            try {
                await fetch(`${API_BASE}/api/v2/auth/logout`, {
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
            this.clearTokenRefresh();
            window.location.href = '/';
        }
        
        async refreshToken() {
            try {
                const response = await fetch(`${API_BASE}/api/v2/auth/refresh`, {
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
            
            // Refresh token 5 minutes before expiry (access token is 15 minutes)
            this.refreshTimer = setInterval(async () => {
                console.log('[UnifiedAuth] Attempting token refresh...');
                const refreshed = await this.refreshToken();
                if (!refreshed) {
                    // Refresh failed, user needs to login again
                    this.user = null;
                    localStorage.removeItem('user');
                    this.updateUI();
                }
            }, 10 * 60 * 1000); // Every 10 minutes
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
            
            // Update auth-dependent elements
            document.querySelectorAll('[data-auth="required"]').forEach(el => {
                el.style.display = isAuth ? '' : 'none';
            });
            
            document.querySelectorAll('[data-auth="guest"]').forEach(el => {
                el.style.display = isAuth ? 'none' : '';
            });
            
            // Dispatch custom event
            window.dispatchEvent(new CustomEvent('authStateChanged', { 
                detail: { authenticated: isAuth, user: this.user }
            }));
        }
    }
    
    // Create global instance
    window.UnifiedAuth = new UnifiedAuthService();
    
    // Initialize on DOM ready
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
                    const rememberMe = document.getElementById('remember')?.checked || false;
                    
                    const submitBtn = loginForm.querySelector('button[type="submit"]');
                    const originalText = submitBtn.textContent;
                    submitBtn.textContent = 'Logging in...';
                    submitBtn.disabled = true;
                    
                    const result = await window.UnifiedAuth.login(email, password, rememberMe);
                    
                    if (result.success) {
                        // Check for redirect
                        const urlParams = new URLSearchParams(window.location.search);
                        const redirect = urlParams.get('redirect') || 
                                       sessionStorage.getItem('redirect_after_login') || 
                                       '/dashboard.html';
                        
                        sessionStorage.removeItem('redirect_after_login');
                        window.location.href = redirect;
                    } else {
                        submitBtn.textContent = originalText;
                        submitBtn.disabled = false;
                        
                        // Show error
                        const errorDiv = document.getElementById('errorMessage');
                        if (errorDiv) {
                            errorDiv.style.display = 'block';
                            errorDiv.textContent = result.error;
                        } else {
                            alert(result.error);
                        }
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