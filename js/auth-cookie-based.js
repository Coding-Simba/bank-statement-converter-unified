/**
 * 🔐 SECURE COOKIE-BASED AUTHENTICATION
 * Works like Google/Facebook - no client-side token storage
 * All auth state is managed by secure HTTP-only cookies
 */

(function() {
    'use strict';
    
    console.log('🔐 Cookie-Based Auth System Loading...');
    
    const API_BASE = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
        ? 'http://localhost:5000'
        : '';
    
    class CookieAuthSystem {
        constructor() {
            this.user = null;
            this.initialized = false;
            this.authCheckInterval = null;
            
            // Initialize immediately
            this.initialize();
        }
        
        async initialize() {
            console.log('🔐 Initializing Cookie Auth...');
            
            // Check authentication status on load
            await this.checkAuth();
            
            // Update UI immediately
            this.updateUI();
            
            // Set up periodic auth checks
            this.setupPeriodicChecks();
            
            // Handle forms if on login/signup pages
            this.setupFormHandlers();
            
            // Listen for cross-tab events
            this.setupCrossTabSync();
            
            this.initialized = true;
            
            // Dispatch ready event
            window.dispatchEvent(new CustomEvent('cookie-auth-ready', {
                detail: { user: this.user, authenticated: this.isAuthenticated() }
            }));
            
            console.log('🔐 Cookie Auth initialized!');
        }
        
        async checkAuth() {
            try {
                const response = await fetch(`${API_BASE}/api/auth/check`, {
                    method: 'GET',
                    credentials: 'include', // CRITICAL: Include cookies
                    headers: {
                        'Accept': 'application/json'
                    }
                });
                
                if (response.ok) {
                    const data = await response.json();
                    if (data.authenticated) {
                        this.user = data.user;
                        console.log('🔐 User authenticated:', this.user.email);
                        return true;
                    }
                }
                
                this.user = null;
                return false;
            } catch (error) {
                console.error('🔐 Auth check error:', error);
                // Don't clear user on network error
                return false;
            }
        }
        
        setupPeriodicChecks() {
            // Check auth status every 5 minutes
            this.authCheckInterval = setInterval(async () => {
                await this.checkAuth();
                this.updateUI();
            }, 5 * 60 * 1000);
            
            // Also check when window regains focus
            window.addEventListener('focus', async () => {
                await this.checkAuth();
                this.updateUI();
            });
        }
        
        setupCrossTabSync() {
            // Listen for storage events (logout from another tab)
            window.addEventListener('storage', async (event) => {
                if (event.key === 'auth-logout-event') {
                    console.log('🔐 Logout detected from another tab');
                    this.user = null;
                    this.updateUI();
                    await this.checkAuth();
                }
            });
            
            // Use BroadcastChannel if available
            if (typeof BroadcastChannel !== 'undefined') {
                this.authChannel = new BroadcastChannel('cookie-auth');
                this.authChannel.onmessage = async (event) => {
                    if (event.data.type === 'auth-changed') {
                        console.log('🔐 Auth change detected');
                        await this.checkAuth();
                        this.updateUI();
                    }
                };
            }
        }
        
        setupFormHandlers() {
            // Handle login form
            if (window.location.pathname.includes('login')) {
                const loginForm = document.getElementById('loginForm');
                if (loginForm && !loginForm.hasAttribute('data-cookie-auth')) {
                    loginForm.setAttribute('data-cookie-auth', 'true');
                    loginForm.addEventListener('submit', async (e) => {
                        e.preventDefault();
                        await this.handleLogin(e);
                    });
                }
            }
            
            // Handle signup form
            if (window.location.pathname.includes('signup')) {
                const signupForm = document.getElementById('signupForm');
                if (signupForm && !signupForm.hasAttribute('data-cookie-auth')) {
                    signupForm.setAttribute('data-cookie-auth', 'true');
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
                    credentials: 'include', // CRITICAL: Include cookies
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
                
                if (response.ok) {
                    // Server has set the auth cookie
                    this.user = data.user;
                    
                    // Notify other tabs
                    this.broadcastAuthChange();
                    
                    // Show success
                    this.showMessage('Login successful! Redirecting...', 'success');
                    
                    // Redirect to dashboard
                    setTimeout(() => {
                        window.location.href = '/dashboard-modern.html';
                    }, 500);
                } else {
                    throw new Error(data.detail || 'Login failed');
                }
            } catch (error) {
                console.error('🔐 Login error:', error);
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
                    credentials: 'include', // CRITICAL: Include cookies
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
                
                if (response.ok) {
                    // Server has set the auth cookie
                    this.user = data.user;
                    
                    // Notify other tabs
                    this.broadcastAuthChange();
                    
                    // Show success
                    this.showMessage('Account created! Redirecting...', 'success');
                    
                    // Redirect to dashboard
                    setTimeout(() => {
                        window.location.href = '/dashboard-modern.html';
                    }, 500);
                } else {
                    throw new Error(data.detail || 'Registration failed');
                }
            } catch (error) {
                console.error('🔐 Signup error:', error);
                this.showMessage(error.message || 'Network error. Please try again.', 'error');
                
                if (submitBtn) {
                    submitBtn.disabled = false;
                    submitBtn.textContent = 'Create Account';
                }
            }
        }
        
        async logout() {
            try {
                await fetch(`${API_BASE}/api/auth/logout`, {
                    method: 'POST',
                    credentials: 'include' // CRITICAL: Include cookies
                });
                
                // Clear user data
                this.user = null;
                
                // Notify other tabs
                localStorage.setItem('auth-logout-event', Date.now().toString());
                this.broadcastAuthChange();
                
                // Redirect to home
                window.location.href = '/';
            } catch (error) {
                console.error('🔐 Logout error:', error);
                // Still redirect even if request fails
                window.location.href = '/';
            }
        }
        
        broadcastAuthChange() {
            if (this.authChannel) {
                this.authChannel.postMessage({ type: 'auth-changed' });
            }
        }
        
        updateUI() {
            console.log('🔐 Updating UI for auth state:', this.isAuthenticated());
            
            // Update navigation
            this.updateNavbar();
            
            // Update auth-dependent elements
            document.querySelectorAll('[data-auth="required"]').forEach(el => {
                el.style.display = this.isAuthenticated() ? '' : 'none';
            });
            
            document.querySelectorAll('[data-auth="guest"]').forEach(el => {
                el.style.display = this.isAuthenticated() ? 'none' : '';
            });
            
            // Dispatch event
            window.dispatchEvent(new CustomEvent('auth-state-changed', {
                detail: { authenticated: this.isAuthenticated(), user: this.user }
            }));
        }
        
        updateNavbar() {
            const navRight = document.querySelector('.nav-right');
            if (!navRight) return;
            
            // Find existing elements
            const loginLink = navRight.querySelector('a[href="/login.html"]');
            const signupLink = navRight.querySelector('a[href="/signup.html"]');
            const userDropdown = navRight.querySelector('.user-dropdown');
            
            if (this.isAuthenticated()) {
                // Remove login/signup links
                if (loginLink) loginLink.remove();
                if (signupLink) signupLink.remove();
                
                // Add user dropdown if it doesn't exist
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
                
                // Add login/signup links if they don't exist
                if (!loginLink && !signupLink) {
                    const mobileToggle = navRight.querySelector('.mobile-menu-toggle');
                    
                    const newLoginLink = document.createElement('a');
                    newLoginLink.href = '/login.html';
                    newLoginLink.className = 'nav-link';
                    newLoginLink.textContent = 'Log In';
                    
                    const newSignupLink = document.createElement('a');
                    newSignupLink.href = '/signup.html';
                    newSignupLink.className = 'btn-primary';
                    newSignupLink.textContent = 'Sign Up Free';
                    
                    if (mobileToggle) {
                        navRight.insertBefore(newLoginLink, mobileToggle);
                        navRight.insertBefore(newSignupLink, mobileToggle);
                    } else {
                        navRight.appendChild(newLoginLink);
                        navRight.appendChild(newSignupLink);
                    }
                }
            }
            
            // Update mobile menu
            this.updateMobileMenu();
        }
        
        createUserDropdown() {
            const dropdown = document.createElement('div');
            dropdown.className = 'user-dropdown dropdown';
            
            const dropdownToggle = document.createElement('button');
            dropdownToggle.className = 'nav-link dropdown-toggle user-dropdown-toggle';
            dropdownToggle.innerHTML = `
                <i class="fas fa-user-circle"></i>
                <span class="user-email">${this.user?.email || 'Account'}</span>
                <i class="fas fa-chevron-down"></i>
            `;
            
            const dropdownMenu = document.createElement('div');
            dropdownMenu.className = 'dropdown-menu user-menu';
            dropdownMenu.innerHTML = `
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
                <a href="#" class="dropdown-item logout-btn" onclick="return false;">
                    <i class="fas fa-sign-out-alt"></i>
                    Logout
                </a>
            `;
            
            dropdown.appendChild(dropdownToggle);
            dropdown.appendChild(dropdownMenu);
            
            // Add dropdown functionality
            dropdownToggle.addEventListener('click', (e) => {
                e.stopPropagation();
                dropdown.classList.toggle('active');
            });
            
            // Close dropdown when clicking outside
            document.addEventListener('click', () => {
                dropdown.classList.remove('active');
            });
            
            // Handle logout
            const logoutBtn = dropdownMenu.querySelector('.logout-btn');
            logoutBtn.addEventListener('click', async (e) => {
                e.preventDefault();
                await this.logout();
            });
            
            return dropdown;
        }
        
        updateMobileMenu() {
            const mobileMenu = document.querySelector('.mobile-menu-content');
            if (!mobileMenu) return;
            
            const dashboardLink = mobileMenu.querySelector('a[href="/dashboard-modern.html"]');
            const settingsLink = mobileMenu.querySelector('a[href="/settings.html"]');
            const logoutLink = mobileMenu.querySelector('.mobile-logout');
            
            if (this.isAuthenticated()) {
                // Add user menu items
                if (!dashboardLink) {
                    const newDashboard = document.createElement('a');
                    newDashboard.href = '/dashboard-modern.html';
                    newDashboard.className = 'mobile-link';
                    newDashboard.textContent = 'Dashboard';
                    mobileMenu.insertBefore(newDashboard, mobileMenu.firstChild);
                }
                
                if (!settingsLink) {
                    const newSettings = document.createElement('a');
                    newSettings.href = '/settings.html';
                    newSettings.className = 'mobile-link';
                    newSettings.textContent = 'Settings';
                    mobileMenu.appendChild(newSettings);
                }
                
                if (!logoutLink) {
                    const newLogout = document.createElement('a');
                    newLogout.href = '#';
                    newLogout.className = 'mobile-link mobile-logout';
                    newLogout.textContent = 'Logout';
                    newLogout.addEventListener('click', async (e) => {
                        e.preventDefault();
                        await this.logout();
                    });
                    mobileMenu.appendChild(newLogout);
                }
            } else {
                // Remove user menu items
                if (dashboardLink) dashboardLink.remove();
                if (settingsLink) settingsLink.remove();
                if (logoutLink) logoutLink.remove();
            }
        }
        
        showMessage(message, type = 'info') {
            let messageEl = document.getElementById('auth-message');
            
            if (!messageEl) {
                messageEl = document.createElement('div');
                messageEl.id = 'auth-message';
                messageEl.style.cssText = `
                    position: fixed;
                    top: 20px;
                    right: 20px;
                    padding: 16px 24px;
                    border-radius: 8px;
                    font-size: 14px;
                    z-index: 9999;
                    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
                    animation: slideIn 0.3s ease-out;
                    max-width: 400px;
                `;
                document.body.appendChild(messageEl);
            }
            
            if (type === 'error') {
                messageEl.style.background = '#fee';
                messageEl.style.color = '#c33';
                messageEl.style.border = '1px solid #fcc';
            } else if (type === 'success') {
                messageEl.style.background = '#efe';
                messageEl.style.color = '#363';
                messageEl.style.border = '1px solid #cfc';
            }
            
            messageEl.textContent = message;
            messageEl.style.display = 'block';
            
            setTimeout(() => {
                messageEl.style.display = 'none';
            }, 5000);
        }
        
        isAuthenticated() {
            return !!this.user;
        }
        
        getUser() {
            return this.user;
        }
        
        // Protected requests automatically include cookies
        async makeAuthenticatedRequest(url, options = {}) {
            return fetch(url, {
                ...options,
                credentials: 'include', // CRITICAL: Always include cookies
                headers: {
                    'Accept': 'application/json',
                    'Content-Type': 'application/json',
                    ...options.headers
                }
            });
        }
    }
    
    // Create global instance
    window.CookieAuth = new CookieAuthSystem();
    
    // Add required CSS
    const style = document.createElement('style');
    style.textContent = `
        .user-dropdown {
            position: relative;
            display: inline-block;
        }
        
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
        
        .user-dropdown-toggle:hover {
            background: #f5f5f5;
            color: #333;
        }
        
        .user-dropdown-toggle i {
            font-size: 18px;
        }
        
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
        
        .user-dropdown.active .user-menu {
            display: block;
        }
        
        .user-menu .dropdown-item {
            padding: 12px 16px;
            display: flex;
            align-items: center;
            gap: 12px;
            color: #333;
            text-decoration: none;
            transition: all 0.2s;
        }
        
        .user-menu .dropdown-item:hover {
            background: #f5f5f5;
        }
        
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
        
        @keyframes slideIn {
            from {
                transform: translateX(100%);
                opacity: 0;
            }
            to {
                transform: translateX(0);
                opacity: 1;
            }
        }
        
        @media (max-width: 768px) {
            .user-dropdown {
                display: none;
            }
        }
    `;
    document.head.appendChild(style);
    
    console.log('🔐 Cookie-Based Auth System Ready!');
})();