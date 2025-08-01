/**
 * 🚀 NO-REDIRECT AUTH SYSTEM
 * This version doesn't redirect from protected pages
 * It only manages auth state and navbar updates
 */

(function() {
    'use strict';
    
    console.log('🚀 No-Redirect Auth Loading...');
    
    const API_BASE = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
        ? 'http://localhost:5000'
        : '';
    
    class NoRedirectAuth {
        constructor() {
            this.user = null;
            this.initialized = false;
            
            // Load auth state
            this.loadAuthState();
            
            // Initialize
            this.initialize();
        }
        
        loadAuthState() {
            const storedToken = localStorage.getItem('access_token');
            const storedUser = localStorage.getItem('user');
            
            if (storedToken && storedUser) {
                try {
                    this.user = JSON.parse(storedUser);
                    console.log('🚀 Auth loaded:', this.user.email);
                } catch (e) {
                    console.error('Failed to parse user:', e);
                }
            }
        }
        
        async initialize() {
            console.log('🚀 Initializing...');
            
            // Update UI immediately
            this.updateUI();
            
            // Setup form handlers ONLY on login/signup pages
            this.setupFormHandlers();
            
            // Setup cross-tab sync
            this.setupCrossTabSync();
            
            this.initialized = true;
            console.log('🚀 Auth Ready!');
        }
        
        setupCrossTabSync() {
            window.addEventListener('storage', (event) => {
                if (event.key === 'access_token' || event.key === 'user') {
                    this.loadAuthState();
                    this.updateUI();
                }
                
                if (event.key === 'logout-event') {
                    this.user = null;
                    this.updateUI();
                }
            });
        }
        
        setupFormHandlers() {
            // Only setup handlers on login/signup pages
            const path = window.location.pathname;
            
            if (path.includes('login')) {
                const loginForm = document.getElementById('loginForm');
                if (loginForm && !loginForm.hasAttribute('data-no-redirect')) {
                    loginForm.setAttribute('data-no-redirect', 'true');
                    loginForm.addEventListener('submit', async (e) => {
                        e.preventDefault();
                        await this.handleLogin(e);
                    });
                }
            }
            
            if (path.includes('signup')) {
                const signupForm = document.getElementById('signupForm');
                if (signupForm && !signupForm.hasAttribute('data-no-redirect')) {
                    signupForm.setAttribute('data-no-redirect', 'true');
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
                    localStorage.setItem('access_token', data.access_token);
                    if (data.refresh_token) {
                        localStorage.setItem('refresh_token', data.refresh_token);
                    }
                    localStorage.setItem('user', JSON.stringify(data.user));
                    
                    this.user = data.user;
                    
                    // Show success
                    this.showMessage('Login successful! Redirecting...', 'success');
                    
                    // Redirect to dashboard
                    window.location.href = '/dashboard-modern.html';
                } else {
                    throw new Error(data.detail || 'Login failed');
                }
            } catch (error) {
                console.error('Login error:', error);
                this.showMessage(error.message || 'Network error', 'error');
                
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
                    localStorage.setItem('access_token', data.access_token);
                    if (data.refresh_token) {
                        localStorage.setItem('refresh_token', data.refresh_token);
                    }
                    localStorage.setItem('user', JSON.stringify(data.user));
                    
                    this.user = data.user;
                    
                    // Show success
                    this.showMessage('Account created! Redirecting...', 'success');
                    
                    // Redirect to dashboard
                    window.location.href = '/dashboard-modern.html';
                } else {
                    throw new Error(data.detail || 'Registration failed');
                }
            } catch (error) {
                console.error('Signup error:', error);
                this.showMessage(error.message || 'Network error', 'error');
                
                if (submitBtn) {
                    submitBtn.disabled = false;
                    submitBtn.textContent = 'Create Account';
                }
            }
        }
        
        async logout() {
            const token = localStorage.getItem('access_token');
            
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
                console.error('Logout error:', error);
            }
            
            // Clear auth
            localStorage.removeItem('access_token');
            localStorage.removeItem('refresh_token');
            localStorage.removeItem('user');
            
            // Notify other tabs
            localStorage.setItem('logout-event', Date.now().toString());
            
            // Redirect to home
            window.location.href = '/';
        }
        
        updateUI() {
            console.log('🚀 Updating UI, auth:', !!this.user);
            
            // Update navbar
            this.updateNavbar();
            
            // Update auth elements
            document.querySelectorAll('[data-auth="required"]').forEach(el => {
                el.style.display = this.user ? '' : 'none';
            });
            
            document.querySelectorAll('[data-auth="guest"]').forEach(el => {
                el.style.display = this.user ? 'none' : '';
            });
        }
        
        updateNavbar() {
            const navRight = document.querySelector('.nav-right');
            if (!navRight) return;
            
            const loginLink = navRight.querySelector('a[href="/login.html"]');
            const signupLink = navRight.querySelector('a[href="/signup.html"]');
            let userDropdown = navRight.querySelector('.user-dropdown');
            
            if (this.user) {
                // Remove login/signup
                if (loginLink) loginLink.remove();
                if (signupLink) signupLink.remove();
                
                // Add user dropdown
                if (!userDropdown) {
                    userDropdown = document.createElement('div');
                    userDropdown.className = 'user-dropdown dropdown';
                    userDropdown.innerHTML = `
                        <button class="nav-link dropdown-toggle user-dropdown-toggle">
                            <i class="fas fa-user-circle"></i>
                            <span class="user-email">${this.user.email}</span>
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
                            <a href="#" class="dropdown-item logout-btn" onclick="return false;">
                                <i class="fas fa-sign-out-alt"></i>
                                Logout
                            </a>
                        </div>
                    `;
                    
                    const mobileToggle = navRight.querySelector('.mobile-menu-toggle');
                    if (mobileToggle) {
                        navRight.insertBefore(userDropdown, mobileToggle);
                    } else {
                        navRight.appendChild(userDropdown);
                    }
                    
                    // Add dropdown functionality
                    const toggle = userDropdown.querySelector('.user-dropdown-toggle');
                    toggle.addEventListener('click', (e) => {
                        e.stopPropagation();
                        userDropdown.classList.toggle('active');
                    });
                    
                    // Close on outside click
                    document.addEventListener('click', () => {
                        userDropdown.classList.remove('active');
                    });
                    
                    // Handle logout
                    const logoutBtn = userDropdown.querySelector('.logout-btn');
                    logoutBtn.addEventListener('click', async (e) => {
                        e.preventDefault();
                        await this.logout();
                    });
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
            return !!this.user;
        }
        
        getUser() {
            return this.user;
        }
    }
    
    // Create global instance
    window.UnifiedAuth = new NoRedirectAuth();
    
    // Add CSS
    const style = document.createElement('style');
    style.textContent = `
        .user-dropdown { position: relative; display: inline-block; }
        .user-dropdown-toggle {
            display: flex; align-items: center; gap: 8px;
            background: none; border: none; cursor: pointer;
            font-size: 14px; color: #666; padding: 8px 16px;
            border-radius: 8px; transition: all 0.2s;
        }
        .user-dropdown-toggle:hover { background: #f5f5f5; color: #333; }
        .user-dropdown-toggle i { font-size: 18px; }
        .user-email {
            max-width: 150px; overflow: hidden;
            text-overflow: ellipsis; white-space: nowrap;
        }
        .user-menu {
            position: absolute; top: 100%; right: 0;
            background: white; border-radius: 8px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.15);
            min-width: 200px; margin-top: 8px;
            display: none; z-index: 1000;
        }
        .user-dropdown.active .user-menu { display: block; }
        .user-menu .dropdown-item {
            padding: 12px 16px; display: flex;
            align-items: center; gap: 12px;
            color: #333; text-decoration: none;
            transition: all 0.2s;
        }
        .user-menu .dropdown-item:hover { background: #f5f5f5; }
        .user-menu .dropdown-item i {
            width: 16px; text-align: center; color: #666;
        }
        .dropdown-divider {
            height: 1px; background: #e1e8ed; margin: 8px 0;
        }
        @media (max-width: 768px) {
            .user-dropdown { display: none; }
        }
    `;
    document.head.appendChild(style);
    
    console.log('🚀 No-Redirect Auth Ready!');
})();