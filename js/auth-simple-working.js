/**
 * SIMPLE WORKING AUTH - No redirects, just auth state management
 */

(function() {
    'use strict';
    
    const API_BASE = '';
    
    // Load auth state
    const token = localStorage.getItem('access_token');
    const userStr = localStorage.getItem('user');
    let currentUser = null;
    
    if (token && userStr) {
        try {
            currentUser = JSON.parse(userStr);
        } catch (e) {}
    }
    
    // Update navbar immediately
    function updateNavbar() {
        const navRight = document.querySelector('.nav-right');
        if (!navRight) return;
        
        const loginLink = navRight.querySelector('a[href="/login.html"]');
        const signupLink = navRight.querySelector('a[href="/signup.html"]');
        const existingDropdown = navRight.querySelector('.user-dropdown');
        
        if (currentUser && token) {
            // User is logged in
            if (loginLink) loginLink.style.display = 'none';
            if (signupLink) signupLink.style.display = 'none';
            
            if (!existingDropdown) {
                const dropdown = document.createElement('div');
                dropdown.className = 'user-dropdown';
                dropdown.style.cssText = 'position: relative; display: inline-block;';
                dropdown.innerHTML = `
                    <button style="background: none; border: none; cursor: pointer; padding: 8px 16px; color: #666; font-size: 14px; display: flex; align-items: center; gap: 8px;" onclick="toggleDropdown(event)">
                        <i class="fas fa-user-circle" style="font-size: 18px;"></i>
                        <span>${currentUser.email}</span>
                        <i class="fas fa-chevron-down" style="font-size: 12px;"></i>
                    </button>
                    <div class="user-menu" style="display: none; position: absolute; top: 100%; right: 0; background: white; border-radius: 8px; box-shadow: 0 4px 20px rgba(0,0,0,0.15); min-width: 200px; margin-top: 8px; z-index: 1000;">
                        <a href="/dashboard-modern.html" style="display: block; padding: 12px 16px; color: #333; text-decoration: none;">Dashboard</a>
                        <a href="/settings.html" style="display: block; padding: 12px 16px; color: #333; text-decoration: none;">Settings</a>
                        <hr style="margin: 8px 0; border: none; border-top: 1px solid #e1e8ed;">
                        <a href="#" onclick="doLogout(); return false;" style="display: block; padding: 12px 16px; color: #333; text-decoration: none;">Logout</a>
                    </div>
                `;
                
                const mobileToggle = navRight.querySelector('.mobile-menu-toggle');
                if (mobileToggle) {
                    navRight.insertBefore(dropdown, mobileToggle);
                } else {
                    navRight.appendChild(dropdown);
                }
            }
        } else {
            // Not logged in
            if (existingDropdown) existingDropdown.remove();
            if (loginLink) loginLink.style.display = '';
            if (signupLink) signupLink.style.display = '';
        }
    }
    
    // Global functions
    window.toggleDropdown = function(e) {
        e.stopPropagation();
        const menu = e.target.closest('.user-dropdown').querySelector('.user-menu');
        menu.style.display = menu.style.display === 'none' ? 'block' : 'none';
    };
    
    window.doLogout = async function() {
        if (token) {
            try {
                await fetch('/api/auth/logout', {
                    method: 'POST',
                    headers: { 'Authorization': `Bearer ${token}` }
                });
            } catch (e) {}
        }
        
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        localStorage.removeItem('user');
        
        window.location.href = '/';
    };
    
    // Close dropdown on outside click
    document.addEventListener('click', () => {
        const menu = document.querySelector('.user-menu');
        if (menu) menu.style.display = 'none';
    });
    
    // Handle login form if on login page
    if (window.location.pathname.includes('login')) {
        document.addEventListener('DOMContentLoaded', () => {
            const form = document.getElementById('loginForm');
            if (form) {
                form.onsubmit = async function(e) {
                    e.preventDefault();
                    
                    const submitBtn = form.querySelector('button[type="submit"]');
                    if (submitBtn) {
                        submitBtn.disabled = true;
                        submitBtn.textContent = 'Signing in...';
                    }
                    
                    try {
                        const response = await fetch('/api/auth/login', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({
                                email: form.email.value,
                                password: form.password.value,
                                remember_me: form.rememberMe?.checked || false
                            })
                        });
                        
                        const data = await response.json();
                        
                        if (response.ok && data.access_token) {
                            // Store auth
                            localStorage.setItem('access_token', data.access_token);
                            if (data.refresh_token) {
                                localStorage.setItem('refresh_token', data.refresh_token);
                            }
                            localStorage.setItem('user', JSON.stringify(data.user));
                            
                            // Redirect
                            window.location.href = '/dashboard-modern.html';
                        } else {
                            alert(data.detail || 'Login failed');
                            if (submitBtn) {
                                submitBtn.disabled = false;
                                submitBtn.textContent = 'Sign In';
                            }
                        }
                    } catch (error) {
                        alert('Network error: ' + error.message);
                        if (submitBtn) {
                            submitBtn.disabled = false;
                            submitBtn.textContent = 'Sign In';
                        }
                    }
                };
            }
        });
    }
    
    // Update navbar on load
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', updateNavbar);
    } else {
        updateNavbar();
    }
    
    // Export for other scripts
    window.SimpleAuth = {
        isAuthenticated: () => !!(token && currentUser),
        getUser: () => currentUser,
        getToken: () => token
    };
})();