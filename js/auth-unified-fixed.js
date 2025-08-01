/**
 * 🔥 FIXED UNIFIED AUTHENTICATION
 * This version properly stores tokens and maintains auth state
 */

(function() {
    'use strict';
    
    console.log('🔥 Fixed Auth System Loading...');
    
    const API_BASE = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
        ? 'http://localhost:5000'
        : '';
    
    class FixedAuthSystem {
        constructor() {
            this.user = null;
            this.initialized = false;
            
            // Load auth state immediately
            this.loadAuthState();
            
            // Initialize
            this.initialize();
        }
        
        loadAuthState() {
            // Check for stored auth data
            const storedToken = localStorage.getItem('access_token') || sessionStorage.getItem('access_token');
            const storedUser = localStorage.getItem('user') || sessionStorage.getItem('user');
            
            if (storedToken && storedUser) {
                try {
                    this.user = JSON.parse(storedUser);
                    console.log('🔥 Auth state loaded:', this.user.email);
                } catch (e) {
                    console.error('🔥 Failed to parse user data:', e);
                    this.clearAuth();
                }
            }
        }
        
        async initialize() {
            console.log('🔥 Initializing Fixed Auth...');
            
            // Update UI immediately based on stored state
            this.updateUI();
            
            // Verify auth if we have a token
            if (this.hasToken()) {
                const isValid = await this.verifyAuth();
                if (!isValid) {
                    this.clearAuth();
                    this.updateUI();
                }
            }
            
            // Setup form handlers
            this.setupFormHandlers();
            
            // Setup cross-tab sync
            this.setupCrossTabSync();
            
            this.initialized = true;
            
            console.log('🔥 Fixed Auth initialized!');
        }
        
        hasToken() {
            return !!(localStorage.getItem('access_token') || sessionStorage.getItem('access_token'));
        }
        
        getToken() {
            return localStorage.getItem('access_token') || sessionStorage.getItem('access_token');
        }
        
        async verifyAuth() {
            const token = this.getToken();
            if (!token) return false;
            
            try {
                const response = await fetch(`${API_BASE}/api/auth/check`, {
                    method: 'GET',
                    credentials: 'include',
                    headers: {
                        'Authorization': `Bearer ${token}`,
                        'Accept': 'application/json'
                    }
                });
                
                if (response.ok) {
                    const data = await response.json();
                    if (data.authenticated) {
                        // Update user data if provided
                        if (data.user) {
                            this.user = data.user;
                            const storage = localStorage.getItem('access_token') ? localStorage : sessionStorage;
                            storage.setItem('user', JSON.stringify(this.user));
                        }
                        return true;
                    }
                }
                
                return false;
            } catch (error) {
                console.error('🔥 Auth verification error:', error);
                // Don't invalidate on network errors
                return true; // Assume valid if we can't check
            }
        }
        
        setupCrossTabSync() {
            // Listen for storage changes
            window.addEventListener('storage', (event) => {
                if (event.key === 'access_token' || event.key === 'user') {
                    console.log('🔥 Auth state changed in another tab');
                    this.loadAuthState();
                    this.updateUI();
                }
                
                if (event.key === 'logout-event') {
                    console.log('🔥 Logout detected from another tab');
                    this.clearAuth();
                    this.updateUI();
                }
            });
            
            // Use BroadcastChannel if available
            if (typeof BroadcastChannel !== 'undefined') {
                this.authChannel = new BroadcastChannel('fixed-auth');
                this.authChannel.onmessage = (event) => {
                    if (event.data.type === 'auth-changed') {
                        this.loadAuthState();
                        this.updateUI();
                    }
                };
            }
        }
        
        setupFormHandlers() {
            // Handle login form
            if (window.location.pathname.includes('login')) {
                const loginForm = document.getElementById('loginForm');
                if (loginForm && !loginForm.hasAttribute('data-fixed-auth')) {
                    loginForm.setAttribute('data-fixed-auth', 'true');
                    loginForm.addEventListener('submit', async (e) => {
                        e.preventDefault();
                        await this.handleLogin(e);
                    });
                }
            }
            
            // Handle signup form
            if (window.location.pathname.includes('signup')) {
                const signupForm = document.getElementById('signupForm');
                if (signupForm && !signupForm.hasAttribute('data-fixed-auth')) {
                    signupForm.setAttribute('data-fixed-auth', 'true');
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
                submitBtn.textContent = 'Signing in...';
            }
            
            try {
                const response = await fetch(`${API_BASE}/api/auth/login`, {
                    method: 'POST',
                    credentials: 'include',
                    headers: {
                        'Content-Type': 'application/json',
                        'Accept': 'application/json'
                    },
                    body: JSON.stringify({
                        email,
                        password,
                        remember_me: rememberMe
                    })
                });
                
                const data = await response.json();
                
                if (response.ok && data.access_token) {
                    // Store auth data
                    const storage = rememberMe ? localStorage : sessionStorage;
                    storage.setItem('access_token', data.access_token);
                    if (data.refresh_token) {
                        storage.setItem('refresh_token', data.refresh_token);
                    }
                    storage.setItem('user', JSON.stringify(data.user));
                    
                    this.user = data.user;
                    
                    // Notify other tabs
                    this.broadcastAuthChange();
                    
                    // Update UI
                    this.updateUI();
                    
                    // Show success
                    this.showMessage('Login successful! Redirecting...', 'success');
                    
                    // Redirect
                    setTimeout(() => {
                        window.location.href = '/dashboard-modern.html';
                    }, 500);
                } else {
                    throw new Error(data.detail || 'Login failed');
                }
            } catch (error) {
                console.error('🔥 Login error:', error);
                this.showMessage(error.message || 'Network error. Please try again.', 'error');
                
                if (submitBtn) {
                    submitBtn.disabled = false;
                    submitBtn.textContent = 'Sign In';
                }
            }
        }
        
        async handleSignup(e) {
            const form = e.target;
            const name = form.name.value;
            const email = form.email.value;
            const password = form.password.value;
            const submitBtn = form.querySelector('button[type="submit"]');
            
            if (submitBtn) {
                submitBtn.disabled = true;
                submitBtn.textContent = 'Creating account...';
            }
            
            try {
                const response = await fetch(`${API_BASE}/api/auth/register`, {
                    method: 'POST',
                    credentials: 'include',
                    headers: {
                        'Content-Type': 'application/json',
                        'Accept': 'application/json'
                    },
                    body: JSON.stringify({
                        name,
                        email,
                        password
                    })
                });
                
                const data = await response.json();
                
                if (response.ok && data.access_token) {
                    // Store auth data
                    localStorage.setItem('access_token', data.access_token);
                    if (data.refresh_token) {
                        localStorage.setItem('refresh_token', data.refresh_token);
                    }
                    localStorage.setItem('user', JSON.stringify(data.user));
                    
                    this.user = data.user;
                    
                    // Notify other tabs
                    this.broadcastAuthChange();
                    
                    // Update UI
                    this.updateUI();
                    
                    // Show success
                    this.showMessage('Account created! Redirecting...', 'success');
                    
                    // Redirect
                    setTimeout(() => {
                        window.location.href = '/dashboard-modern.html';
                    }, 500);
                } else {
                    throw new Error(data.detail || 'Registration failed');
                }
            } catch (error) {
                console.error('🔥 Signup error:', error);
                this.showMessage(error.message || 'Network error. Please try again.', 'error');
                
                if (submitBtn) {
                    submitBtn.disabled = false;
                    submitBtn.textContent = 'Create Account';
                }
            }
        }
        
        async logout() {
            const token = this.getToken();
            
            try {
                if (token) {
                    await fetch(`${API_BASE}/api/auth/logout`, {
                        method: 'POST',
                        credentials: 'include',
                        headers: {
                            'Authorization': `Bearer ${token}`
                        }
                    });
                }
            } catch (error) {
                console.error('🔥 Logout error:', error);
            }
            
            // Clear auth
            this.clearAuth();
            
            // Notify other tabs
            localStorage.setItem('logout-event', Date.now().toString());
            this.broadcastAuthChange();
            
            // Redirect
            window.location.href = '/';
        }
        
        clearAuth() {
            this.user = null;
            localStorage.removeItem('access_token');
            localStorage.removeItem('refresh_token');
            localStorage.removeItem('user');
            sessionStorage.removeItem('access_token');
            sessionStorage.removeItem('refresh_token');
            sessionStorage.removeItem('user');
        }
        
        broadcastAuthChange() {
            if (this.authChannel) {
                this.authChannel.postMessage({ type: 'auth-changed' });
            }
        }
        
        updateUI() {
            console.log('🔥 Updating UI, authenticated:', this.isAuthenticated());
            
            // Update navbar
            this.updateNavbar();
            
            // Update auth-dependent elements
            document.querySelectorAll('[data-auth="required"]').forEach(el => {
                el.style.display = this.isAuthenticated() ? '' : 'none';
            });
            
            document.querySelectorAll('[data-auth="guest"]').forEach(el => {
                el.style.display = this.isAuthenticated() ? 'none' : '';
            });
        }
        
        updateNavbar() {
            const navRight = document.querySelector('.nav-right');
            if (!navRight) return;
            
            const loginLink = navRight.querySelector('a[href="/login.html"]');
            const signupLink = navRight.querySelector('a[href="/signup.html"]');
            const userDropdown = navRight.querySelector('.user-dropdown');
            
            if (this.isAuthenticated()) {
                // Remove login/signup
                if (loginLink) loginLink.remove();
                if (signupLink) signupLink.remove();
                
                // Add user dropdown if missing
                if (!userDropdown) {
                    const dropdown = this.createUserDropdown();
                    const mobileToggle = navRight.querySelector('.mobile-menu-toggle');
                    if (mobileToggle) {
                        navRight.insertBefore(dropdown, mobileToggle);
                    } else {
                        navRight.appendChild(dropdown);
                    }
                }
            } else {
                // Remove user dropdown
                if (userDropdown) userDropdown.remove();
                
                // Add login/signup if missing
                if (!loginLink && !signupLink) {
                    const mobileToggle = navRight.querySelector('.mobile-menu-toggle');
                    
                    const newLogin = document.createElement('a');
                    newLogin.href = '/login.html';
                    newLogin.className = 'nav-link';
                    newLogin.textContent = 'Log In';
                    
                    const newSignup = document.createElement('a');
                    newSignup.href = '/signup.html';
                    newSignup.className = 'btn-primary';
                    newSignup.textContent = 'Sign Up Free';
                    
                    if (mobileToggle) {
                        navRight.insertBefore(newLogin, mobileToggle);
                        navRight.insertBefore(newSignup, mobileToggle);
                    } else {
                        navRight.appendChild(newLogin);
                        navRight.appendChild(newSignup);
                    }
                }
            }
        }
        
        createUserDropdown() {
            const dropdown = document.createElement('div');
            dropdown.className = 'user-dropdown dropdown';
            dropdown.innerHTML = `
                <button class="nav-link dropdown-toggle user-dropdown-toggle">
                    <i class="fas fa-user-circle"></i>
                    <span class="user-email">${this.user?.email || 'Account'}</span>
                    <i class="fas fa-chevron-down"></i>
                </button>
                <div class="dropdown-menu user-menu">
                    <a href="/dashboard-modern.html" class="dropdown-item">
                        <i class="fas fa-tachometer-alt"></i>
                        Dashboard
                    </a>
                    <a href="/settings.html" class="dropdown-item">
                        <i class="fas fa-cog"></i>
                        Settings
                    </a>
                    <a href="/pricing.html" class="dropdown-item">
                        <i class="fas fa-star"></i>
                        Upgrade
                    </a>
                    <div class="dropdown-divider"></div>
                    <a href="#" class="dropdown-item logout-btn">
                        <i class="fas fa-sign-out-alt"></i>
                        Logout
                    </a>
                </div>
            `;
            
            const toggle = dropdown.querySelector('.user-dropdown-toggle');
            const menu = dropdown.querySelector('.user-menu');
            const logoutBtn = dropdown.querySelector('.logout-btn');
            
            // Toggle dropdown
            toggle.addEventListener('click', (e) => {
                e.stopPropagation();
                dropdown.classList.toggle('active');
            });
            
            // Close on outside click
            document.addEventListener('click', () => {
                dropdown.classList.remove('active');
            });
            
            // Handle logout
            logoutBtn.addEventListener('click', async (e) => {
                e.preventDefault();
                await this.logout();
            });
            
            return dropdown;
        }
        
        showMessage(message, type = 'info') {
            let msg = document.getElementById('auth-message');
            if (!msg) {
                msg = document.createElement('div');
                msg.id = 'auth-message';
                msg.style.cssText = `
                    position: fixed;
                    top: 20px;
                    right: 20px;
                    padding: 16px 24px;
                    border-radius: 8px;
                    font-size: 14px;
                    z-index: 9999;
                    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
                `;
                document.body.appendChild(msg);
            }
            
            msg.style.background = type === 'error' ? '#fee' : '#efe';
            msg.style.color = type === 'error' ? '#c33' : '#363';
            msg.style.border = type === 'error' ? '1px solid #fcc' : '1px solid #cfc';
            msg.textContent = message;
            msg.style.display = 'block';
            
            setTimeout(() => {
                msg.style.display = 'none';
            }, 5000);
        }
        
        isAuthenticated() {
            return !!this.user && this.hasToken();
        }
        
        getUser() {
            return this.user;
        }
        
        async makeAuthenticatedRequest(url, options = {}) {
            const token = this.getToken();
            if (!token) {
                throw new Error('Not authenticated');
            }
            
            return fetch(url, {
                ...options,
                credentials: 'include',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json',
                    ...options.headers
                }
            });
        }
    }
    
    // Create global instance
    window.UnifiedAuth = new FixedAuthSystem();
    
    // Add CSS
    const style = document.createElement('style');
    style.textContent = `
        .user-dropdown { position: relative; display: inline-block; }
        .user-dropdown-toggle {
            display: flex;
            align-items: center;
            gap: 8px;
            background: none;
            border: none;
            cursor: pointer;
            font-size: 14px;
            color: #666;
            padding: 8px 16px;
            border-radius: 8px;
            transition: all 0.2s;
        }
        .user-dropdown-toggle:hover { background: #f5f5f5; color: #333; }
        .user-dropdown-toggle i { font-size: 18px; }
        .user-email {
            max-width: 150px;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }
        .user-menu {
            position: absolute;
            top: 100%;
            right: 0;
            background: white;
            border-radius: 8px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.15);
            min-width: 200px;
            margin-top: 8px;
            display: none;
            z-index: 1000;
        }
        .user-dropdown.active .user-menu { display: block; }
        .user-menu .dropdown-item {
            padding: 12px 16px;
            display: flex;
            align-items: center;
            gap: 12px;
            color: #333;
            text-decoration: none;
            transition: all 0.2s;
        }
        .user-menu .dropdown-item:hover { background: #f5f5f5; }
        .user-menu .dropdown-item i {
            width: 16px;
            text-align: center;
            color: #666;
        }
        .dropdown-divider {
            height: 1px;
            background: #e1e8ed;
            margin: 8px 0;
        }
        @media (max-width: 768px) {
            .user-dropdown { display: none; }
        }
    `;
    document.head.appendChild(style);
    
    console.log('🔥 Fixed Auth System Ready!');
})();