/**
 * 🧠 ULTRATHINK UNIFIED AUTHENTICATION SYSTEM
 * 
 * This system ensures authentication state persists across all pages
 * and dynamically updates the navbar to show logged-in state
 */

(function() {
    'use strict';
    
    console.log('🧠 ULTRATHINK Auth System Loading...');
    
    // Configuration
    const API_BASE = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
        ? 'http://localhost:5000'
        : '';
    
    class UltraThinkAuth {
        constructor() {
            this.user = null;
            this.initialized = false;
            this.authCheckInterval = null;
            
            // Load user data from storage immediately
            this.loadUserFromStorage();
            
            // Set up cross-tab synchronization
            this.setupCrossTabSync();
            
            // Initialize immediately
            this.initialize();
        }
        
        loadUserFromStorage() {
            // Check multiple storage locations for maximum compatibility
            const storedUser = localStorage.getItem('user') || 
                             sessionStorage.getItem('user') ||
                             localStorage.getItem('user_data');
            
            const storedToken = localStorage.getItem('access_token') ||
                              sessionStorage.getItem('access_token');
            
            if (storedUser && storedToken) {
                try {
                    this.user = JSON.parse(storedUser);
                    console.log('🧠 User loaded from storage:', this.user.email);
                } catch (e) {
                    console.error('🧠 Failed to parse stored user:', e);
                    this.clearAuth();
                }
            }
        }
        
        setupCrossTabSync() {
            // Listen for storage changes
            window.addEventListener('storage', (event) => {
                if (event.key === 'user' || event.key === 'access_token') {
                    console.log('🧠 Auth state changed in another tab');
                    this.loadUserFromStorage();
                    this.updateNavbar();
                }
                
                if (event.key === 'auth-logout') {
                    console.log('🧠 Logout detected from another tab');
                    this.clearAuth();
                    this.updateNavbar();
                }
            });
            
            // Use BroadcastChannel for more reliable cross-tab communication
            if (typeof BroadcastChannel !== 'undefined') {
                this.authChannel = new BroadcastChannel('ultrathink-auth');
                this.authChannel.onmessage = (event) => {
                    if (event.data.type === 'auth-update') {
                        console.log('🧠 Auth update from another tab');
                        this.loadUserFromStorage();
                        this.updateNavbar();
                    }
                };
            }
        }
        
        async initialize() {
            console.log('🧠 Initializing ULTRATHINK Auth...');
            
            // Check auth status if we have a token
            if (this.hasStoredAuth()) {
                await this.verifyAuth();
            }
            
            // Update navbar immediately
            this.updateNavbar();
            
            // Set up periodic auth checks
            this.setupAuthChecks();
            
            // Handle login/signup forms if on those pages
            this.setupFormHandlers();
            
            // Mark as initialized
            this.initialized = true;
            
            // Dispatch ready event
            window.dispatchEvent(new CustomEvent('ultrathink-auth-ready', {
                detail: { user: this.user, authenticated: this.isAuthenticated() }
            }));
            
            console.log('🧠 ULTRATHINK Auth initialized!');
        }
        
        hasStoredAuth() {
            return !!(localStorage.getItem('access_token') || 
                     sessionStorage.getItem('access_token'));
        }
        
        async verifyAuth() {
            try {
                const token = localStorage.getItem('access_token') || 
                            sessionStorage.getItem('access_token');
                
                if (!token) {
                    this.clearAuth();
                    return false;
                }
                
                const response = await fetch(`${API_BASE}/api/auth/check`, {
                    method: 'GET',
                    credentials: 'include',
                    headers: {
                        'Authorization': `Bearer ${token}`,
                        'Content-Type': 'application/json'
                    }
                });
                
                if (response.ok) {
                    const data = await response.json();
                    console.log('🧠 Auth verified:', data);
                    return true;
                } else {
                    console.log('🧠 Auth check failed:', response.status);
                    this.clearAuth();
                    return false;
                }
            } catch (error) {
                console.error('🧠 Auth verification error:', error);
                // Don't clear auth on network errors - user might be offline
                return !!this.user;
            }
        }
        
        setupAuthChecks() {
            // Check auth status every 5 minutes
            this.authCheckInterval = setInterval(() => {
                if (this.hasStoredAuth()) {
                    this.verifyAuth();
                }
            }, 5 * 60 * 1000);
        }
        
        setupFormHandlers() {
            // Handle login form
            if (window.location.pathname.includes('login')) {
                const loginForm = document.getElementById('loginForm');
                if (loginForm && !loginForm.hasAttribute('data-ultrathink')) {
                    loginForm.setAttribute('data-ultrathink', 'true');
                    loginForm.addEventListener('submit', async (e) => {
                        e.preventDefault();
                        await this.handleLogin(e);
                    });
                }
            }
            
            // Handle signup form
            if (window.location.pathname.includes('signup')) {
                const signupForm = document.getElementById('signupForm');
                if (signupForm && !signupForm.hasAttribute('data-ultrathink')) {
                    signupForm.setAttribute('data-ultrathink', 'true');
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
                        'Content-Type': 'application/json'
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
                    this.user = data.user;
                    
                    if (rememberMe) {
                        localStorage.setItem('access_token', data.access_token);
                        localStorage.setItem('user', JSON.stringify(data.user));
                    } else {
                        sessionStorage.setItem('access_token', data.access_token);
                        sessionStorage.setItem('user', JSON.stringify(data.user));
                    }
                    
                    // Broadcast auth update
                    this.broadcastAuthUpdate();
                    
                    // Update navbar
                    this.updateNavbar();
                    
                    // Show success message
                    this.showMessage('Login successful! Redirecting...', 'success');
                    
                    // Redirect to dashboard
                    setTimeout(() => {
                        window.location.href = '/dashboard-modern.html';
                    }, 500);
                } else {
                    throw new Error(data.detail || 'Login failed');
                }
            } catch (error) {
                console.error('🧠 Login error:', error);
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
                        'Content-Type': 'application/json'
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
                    this.user = data.user;
                    localStorage.setItem('access_token', data.access_token);
                    localStorage.setItem('user', JSON.stringify(data.user));
                    
                    // Broadcast auth update
                    this.broadcastAuthUpdate();
                    
                    // Update navbar
                    this.updateNavbar();
                    
                    // Show success message
                    this.showMessage('Account created! Redirecting...', 'success');
                    
                    // Redirect to dashboard
                    setTimeout(() => {
                        window.location.href = '/dashboard-modern.html';
                    }, 500);
                } else {
                    throw new Error(data.detail || 'Registration failed');
                }
            } catch (error) {
                console.error('🧠 Signup error:', error);
                this.showMessage(error.message || 'Network error. Please try again.', 'error');
                
                if (submitBtn) {
                    submitBtn.disabled = false;
                    submitBtn.textContent = 'Create Account';
                }
            }
        }
        
        async logout() {
            try {
                const token = localStorage.getItem('access_token') || 
                            sessionStorage.getItem('access_token');
                
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
                console.error('🧠 Logout error:', error);
            }
            
            // Clear auth data
            this.clearAuth();
            
            // Broadcast logout
            localStorage.setItem('auth-logout', Date.now().toString());
            localStorage.removeItem('auth-logout');
            
            if (this.authChannel) {
                this.authChannel.postMessage({ type: 'auth-update' });
            }
            
            // Redirect to home
            window.location.href = '/';
        }
        
        clearAuth() {
            this.user = null;
            localStorage.removeItem('access_token');
            localStorage.removeItem('user');
            localStorage.removeItem('user_data');
            sessionStorage.removeItem('access_token');
            sessionStorage.removeItem('user');
        }
        
        broadcastAuthUpdate() {
            if (this.authChannel) {
                this.authChannel.postMessage({ type: 'auth-update' });
            }
        }
        
        updateNavbar() {
            console.log('🧠 Updating navbar for auth state:', this.isAuthenticated());
            
            // Find the nav-right container
            const navRight = document.querySelector('.nav-right');
            if (!navRight) {
                console.log('🧠 Nav-right not found, waiting for DOM...');
                return;
            }
            
            // Find login and signup links
            const loginLink = navRight.querySelector('a[href="/login.html"]');
            const signupLink = navRight.querySelector('a[href="/signup.html"]');
            
            if (this.isAuthenticated()) {
                // User is logged in - replace login/signup with user menu
                if (loginLink || signupLink) {
                    // Remove login and signup links
                    if (loginLink) loginLink.remove();
                    if (signupLink) signupLink.remove();
                    
                    // Create user dropdown
                    const userDropdown = this.createUserDropdown();
                    
                    // Insert before mobile menu toggle
                    const mobileToggle = navRight.querySelector('.mobile-menu-toggle');
                    if (mobileToggle) {
                        navRight.insertBefore(userDropdown, mobileToggle);
                    } else {
                        navRight.appendChild(userDropdown);
                    }
                }
            } else {
                // User is logged out - ensure login/signup links exist
                const existingDropdown = navRight.querySelector('.user-dropdown');
                if (existingDropdown) {
                    existingDropdown.remove();
                }
                
                // Re-add login and signup links if they don't exist
                if (!loginLink && !signupLink) {
                    const mobileToggle = navRight.querySelector('.mobile-menu-toggle');
                    
                    // Add login link
                    const newLoginLink = document.createElement('a');
                    newLoginLink.href = '/login.html';
                    newLoginLink.className = 'nav-link';
                    newLoginLink.textContent = 'Log In';
                    
                    // Add signup link
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
            
            // Update mobile menu as well
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
                <a href="#" class="dropdown-item logout-btn">
                    <i class="fas fa-sign-out-alt"></i>
                    Logout
                </a>
            `;
            
            dropdown.appendChild(dropdownToggle);
            dropdown.appendChild(dropdownMenu);
            
            // Add dropdown toggle functionality
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
            logoutBtn.addEventListener('click', (e) => {
                e.preventDefault();
                this.logout();
            });
            
            return dropdown;
        }
        
        updateMobileMenu() {
            const mobileMenu = document.querySelector('.mobile-menu-content');
            if (!mobileMenu) return;
            
            if (this.isAuthenticated()) {
                // Remove login/signup links
                const loginLink = mobileMenu.querySelector('a[href="/login.html"]');
                const signupLink = mobileMenu.querySelector('a[href="/signup.html"]');
                if (loginLink) loginLink.remove();
                if (signupLink) signupLink.remove();
                
                // Add user menu items if not already present
                if (!mobileMenu.querySelector('a[href="/dashboard-modern.html"]')) {
                    const dashboardLink = document.createElement('a');
                    dashboardLink.href = '/dashboard-modern.html';
                    dashboardLink.className = 'mobile-link';
                    dashboardLink.textContent = 'Dashboard';
                    mobileMenu.insertBefore(dashboardLink, mobileMenu.firstChild);
                    
                    const settingsLink = document.createElement('a');
                    settingsLink.href = '/settings.html';
                    settingsLink.className = 'mobile-link';
                    settingsLink.textContent = 'Settings';
                    mobileMenu.insertBefore(settingsLink, dashboardLink.nextSibling);
                    
                    const logoutLink = document.createElement('a');
                    logoutLink.href = '#';
                    logoutLink.className = 'mobile-link';
                    logoutLink.textContent = 'Logout';
                    logoutLink.addEventListener('click', (e) => {
                        e.preventDefault();
                        this.logout();
                    });
                    mobileMenu.appendChild(logoutLink);
                }
            }
        }
        
        showMessage(message, type = 'info') {
            // Look for existing message containers
            let messageEl = document.getElementById('errorMessage') || 
                           document.getElementById('successMessage');
            
            if (!messageEl) {
                // Create a message element if none exists
                messageEl = document.createElement('div');
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
                `;
                document.body.appendChild(messageEl);
            }
            
            // Set message style based on type
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
            
            // Auto-hide after 5 seconds
            setTimeout(() => {
                messageEl.style.display = 'none';
            }, 5000);
        }
        
        isAuthenticated() {
            return !!this.user && this.hasStoredAuth();
        }
        
        getUser() {
            return this.user;
        }
        
        async makeAuthenticatedRequest(url, options = {}) {
            const token = localStorage.getItem('access_token') || 
                        sessionStorage.getItem('access_token');
            
            if (!token) {
                throw new Error('No authentication token found');
            }
            
            const headers = {
                ...options.headers,
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            };
            
            return fetch(url, {
                ...options,
                credentials: 'include',
                headers
            });
        }
    }
    
    // Create and initialize the global instance
    window.UltraThinkAuth = new UltraThinkAuth();
    
    // Ensure navbar updates when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => {
            window.UltraThinkAuth.updateNavbar();
        });
    }
    
    // Add CSS for user dropdown
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
    
    console.log('🧠 ULTRATHINK Auth System Ready!');
})();