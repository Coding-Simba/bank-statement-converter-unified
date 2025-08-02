/**
 * Cookie-based Authentication System
 * Uses httpOnly cookies like Google/Facebook for better security
 */

(function() {
    'use strict';
    
    const API_BASE = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
        ? 'http://localhost:5000'
        : `${window.location.protocol}//${window.location.hostname}`;
    
    const AUTH_API = `${API_BASE}/v2/api/auth`;
    
    class CookieAuth {
        constructor() {
            this.user = null;
            this.csrfToken = null;
            this.initialized = false;
            
            // Initialize immediately
            this.init();
        }
        
        async init() {
            console.log('[CookieAuth] Initializing...');
            
            // Get CSRF token first
            await this.getCsrfToken();
            
            // Check authentication status
            await this.checkAuth();
            
            // Setup forms if on login/signup pages
            this.setupForms();
            
            // Update UI
            this.updateUI();
            
            this.initialized = true;
            console.log('[CookieAuth] Ready');
        }
        
        async getCsrfToken() {
            try {
                const response = await fetch(`${AUTH_API}/csrf`, {
                    credentials: 'include'
                });
                
                if (response.ok) {
                    const data = await response.json();
                    this.csrfToken = data.csrf_token;
                    console.log('[CookieAuth] CSRF token obtained');
                }
            } catch (error) {
                console.error('[CookieAuth] Failed to get CSRF token:', error);
            }
        }
        
        async checkAuth() {
            try {
                const response = await fetch(`${AUTH_API}/me`, {
                    credentials: 'include',
                    headers: {
                        'X-CSRF-Token': this.csrfToken
                    }
                });
                
                if (response.ok) {
                    const data = await response.json();
                    this.user = data.user;
                    console.log('[CookieAuth] Authenticated:', this.user.email);
                } else {
                    this.user = null;
                    console.log('[CookieAuth] Not authenticated');
                }
            } catch (error) {
                console.error('[CookieAuth] Auth check failed:', error);
                this.user = null;
            }
        }
        
        async login(email, password, rememberMe = false) {
            try {
                const response = await fetch(`${AUTH_API}/login`, {
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
                    console.log('[CookieAuth] Login successful');
                    return { success: true };
                } else {
                    const error = await response.json();
                    return { success: false, error: error.detail || 'Login failed' };
                }
            } catch (error) {
                console.error('[CookieAuth] Login error:', error);
                return { success: false, error: 'Network error' };
            }
        }
        
        async signup(email, password, fullName = '') {
            try {
                const response = await fetch(`${AUTH_API}/register`, {
                    method: 'POST',
                    credentials: 'include',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRF-Token': this.csrfToken
                    },
                    body: JSON.stringify({
                        email,
                        password,
                        full_name: fullName
                    })
                });
                
                if (response.ok) {
                    const data = await response.json();
                    this.user = data.user;
                    console.log('[CookieAuth] Signup successful');
                    return { success: true };
                } else {
                    const error = await response.json();
                    return { success: false, error: error.detail || 'Signup failed' };
                }
            } catch (error) {
                console.error('[CookieAuth] Signup error:', error);
                return { success: false, error: 'Network error' };
            }
        }
        
        async logout() {
            try {
                await fetch(`${AUTH_API}/logout`, {
                    method: 'POST',
                    credentials: 'include',
                    headers: {
                        'X-CSRF-Token': this.csrfToken
                    }
                });
                
                this.user = null;
                console.log('[CookieAuth] Logged out');
                window.location.href = '/';
            } catch (error) {
                console.error('[CookieAuth] Logout error:', error);
            }
        }
        
        async makeRequest(url, options = {}) {
            // Helper method for authenticated requests
            const response = await fetch(url, {
                ...options,
                credentials: 'include',
                headers: {
                    ...options.headers,
                    'X-CSRF-Token': this.csrfToken
                }
            });
            
            // If we get 401, try to refresh
            if (response.status === 401) {
                console.log('[CookieAuth] Got 401, attempting refresh...');
                const refreshed = await this.refresh();
                
                if (refreshed) {
                    // Retry the request
                    return fetch(url, {
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
        
        async refresh() {
            try {
                const response = await fetch(`${AUTH_API}/refresh`, {
                    method: 'POST',
                    credentials: 'include',
                    headers: {
                        'X-CSRF-Token': this.csrfToken
                    }
                });
                
                if (response.ok) {
                    console.log('[CookieAuth] Token refreshed');
                    return true;
                }
            } catch (error) {
                console.error('[CookieAuth] Refresh failed:', error);
            }
            return false;
        }
        
        isAuthenticated() {
            return !!this.user;
        }
        
        getUser() {
            return this.user;
        }
        
        updateUI() {
            const isAuth = this.isAuthenticated();
            console.log('[CookieAuth] Updating UI, authenticated:', isAuth);
            
            // Update navigation
            const loginBtn = document.getElementById('loginBtn');
            const signupBtn = document.getElementById('signupBtn');
            const userMenu = document.querySelector('.user-menu');
            
            if (loginBtn) loginBtn.style.display = isAuth ? 'none' : 'block';
            if (signupBtn) signupBtn.style.display = isAuth ? 'none' : 'block';
            if (userMenu) userMenu.style.display = isAuth ? 'block' : 'none';
            
            // Update user email display
            if (isAuth && this.user) {
                const emailElements = document.querySelectorAll('.user-email');
                emailElements.forEach(el => {
                    el.textContent = this.user.email;
                });
            }
        }
        
        setupForms() {
            // Setup login form
            const loginForm = document.getElementById('loginForm');
            if (loginForm) {
                loginForm.addEventListener('submit', async (e) => {
                    e.preventDefault();
                    
                    const email = loginForm.email.value;
                    const password = loginForm.password.value;
                    const rememberMe = loginForm.remember?.checked || false;
                    
                    const result = await this.login(email, password, rememberMe);
                    
                    if (result.success) {
                        // Redirect to intended page or dashboard
                        const params = new URLSearchParams(window.location.search);
                        const redirect = params.get('redirect') || '/dashboard.html';
                        window.location.href = redirect;
                    } else {
                        alert(result.error);
                    }
                });
            }
            
            // Setup signup form
            const signupForm = document.getElementById('signupForm');
            if (signupForm) {
                signupForm.addEventListener('submit', async (e) => {
                    e.preventDefault();
                    
                    const email = signupForm.email.value;
                    const password = signupForm.password.value;
                    const fullName = signupForm.fullName?.value || '';
                    
                    const result = await this.signup(email, password, fullName);
                    
                    if (result.success) {
                        // Auto-login after signup
                        const params = new URLSearchParams(window.location.search);
                        const redirect = params.get('redirect') || '/dashboard.html';
                        window.location.href = redirect;
                    } else {
                        alert(result.error);
                    }
                });
            }
        }
    }
    
    // Initialize and expose globally
    window.CookieAuth = new CookieAuth();
    
    // For backward compatibility
    window.UnifiedAuth = window.CookieAuth;
})();