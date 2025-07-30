// Fixed Authentication System - Doesn't clear tokens on API errors
(function() {
    console.log('[Auth Fixed] Initializing robust authentication...');
    
    // Configuration
    const AUTH_CONFIG = {
        tokenKey: 'access_token',
        userKey: 'user_data',
        userKeyLegacy: 'user',
        refreshKey: 'refresh_token',
        maxRetries: 3,
        retryDelay: 1000
    };
    
    // Get stored authentication data
    function getAuthData() {
        const token = localStorage.getItem(AUTH_CONFIG.tokenKey);
        const userData = localStorage.getItem(AUTH_CONFIG.userKey) || localStorage.getItem(AUTH_CONFIG.userKeyLegacy);
        
        if (!token || !userData) {
            return null;
        }
        
        try {
            return {
                token: token,
                user: JSON.parse(userData)
            };
        } catch (e) {
            console.error('[Auth Fixed] Failed to parse user data:', e);
            return null;
        }
    }
    
    // Update UI based on authentication state
    function updateAuthUI() {
        const authData = getAuthData();
        
        if (!authData) {
            console.log('[Auth Fixed] No authentication data found');
            showLoginButtons();
            return;
        }
        
        console.log('[Auth Fixed] User authenticated:', authData.user.email);
        showUserMenu(authData.user);
    }
    
    // Show login/signup buttons
    function showLoginButtons() {
        // Remove any existing user menu
        document.querySelectorAll('.user-menu').forEach(menu => menu.remove());
        
        // Find navigation container
        const navContainers = [
            document.querySelector('.nav-right'),
            document.querySelector('.nav-auth'),
            document.querySelector('.nav-container')
        ].filter(Boolean);
        
        if (navContainers.length === 0) return;
        
        let targetNav = navContainers[0];
        
        // For nav-container, create nav-right if needed
        if (targetNav.classList.contains('nav-container')) {
            let navRight = targetNav.querySelector('.nav-right');
            if (!navRight) {
                navRight = document.createElement('div');
                navRight.className = 'nav-right';
                navRight.style.cssText = 'margin-left: auto; display: flex; align-items: center; gap: 1rem;';
                
                const menuToggle = targetNav.querySelector('.menu-toggle, #menuToggle');
                if (menuToggle) {
                    targetNav.insertBefore(navRight, menuToggle);
                } else {
                    targetNav.appendChild(navRight);
                }
            }
            targetNav = navRight;
        }
        
        // Check if login buttons already exist
        if (!targetNav.querySelector('a[href="/login.html"]')) {
            targetNav.innerHTML = `
                <a href="/login.html" class="nav-link">Log In</a>
                <a href="/signup.html" class="btn-primary" style="
                    padding: 0.5rem 1.5rem;
                    background: #00bfa5;
                    color: white;
                    border-radius: 9999px;
                    text-decoration: none;
                    font-weight: 500;
                    font-size: 0.875rem;
                ">Sign Up Free</a>
            `;
        }
    }
    
    // Show user menu
    function showUserMenu(user) {
        // Remove login/signup buttons
        const authLinks = document.querySelectorAll('a[href="/login.html"], a[href="/signup.html"], .btn-primary[href="/signup.html"]');
        authLinks.forEach(link => {
            if (link.href?.includes('login.html') || link.href?.includes('signup.html')) {
                link.remove();
            }
        });
        
        // Find navigation container
        const navContainers = [
            document.querySelector('.nav-right'),
            document.querySelector('.nav-auth'),
            document.querySelector('.nav-container')
        ].filter(Boolean);
        
        if (navContainers.length === 0) return;
        
        let targetNav = navContainers[0];
        
        // For nav-container, create nav-right if needed
        if (targetNav.classList.contains('nav-container')) {
            let navRight = targetNav.querySelector('.nav-right');
            if (!navRight) {
                navRight = document.createElement('div');
                navRight.className = 'nav-right';
                navRight.style.cssText = 'margin-left: auto; display: flex; align-items: center; gap: 1rem;';
                
                const menuToggle = targetNav.querySelector('.menu-toggle, #menuToggle');
                if (menuToggle) {
                    targetNav.insertBefore(navRight, menuToggle);
                } else {
                    targetNav.appendChild(navRight);
                }
            }
            targetNav = navRight;
        }
        
        // Check if user menu already exists
        if (targetNav.querySelector('.user-menu')) {
            return;
        }
        
        // Create user menu
        const userMenu = document.createElement('div');
        userMenu.className = 'user-menu';
        userMenu.style.position = 'relative';
        userMenu.innerHTML = `
            <button class="user-menu-toggle" style="
                display: flex;
                align-items: center;
                gap: 0.5rem;
                padding: 0.5rem 1rem;
                background: #f0f2f5;
                border: none;
                border-radius: 9999px;
                color: #212529;
                font-size: 0.875rem;
                font-weight: 500;
                cursor: pointer;
                font-family: inherit;
                transition: all 0.2s ease;
            ">
                <i class="fas fa-user-circle"></i>
                <span class="user-email">${user.email || 'Account'}</span>
                <i class="fas fa-chevron-down"></i>
            </button>
            <div class="user-dropdown" style="
                position: absolute;
                top: 100%;
                right: 0;
                margin-top: 0.5rem;
                background: white;
                border: 1px solid #e5e7eb;
                border-radius: 0.5rem;
                box-shadow: 0 10px 25px rgba(0, 0, 0, 0.1);
                min-width: 220px;
                display: none;
                z-index: 9999;
            ">
                <a href="/dashboard.html" class="dropdown-item" style="
                    display: block;
                    padding: 0.75rem 1rem;
                    color: #495057;
                    text-decoration: none;
                    transition: all 0.2s ease;
                ">
                    <i class="fas fa-tachometer-alt"></i> Dashboard
                </a>
                <a href="/settings.html" class="dropdown-item" style="
                    display: block;
                    padding: 0.75rem 1rem;
                    color: #495057;
                    text-decoration: none;
                    transition: all 0.2s ease;
                ">
                    <i class="fas fa-cog"></i> Settings
                </a>
                <div style="height: 1px; background: #e5e7eb;"></div>
                <a href="#" class="dropdown-item logout-btn" style="
                    display: block;
                    padding: 0.75rem 1rem;
                    color: #495057;
                    text-decoration: none;
                    transition: all 0.2s ease;
                ">
                    <i class="fas fa-sign-out-alt"></i> Logout
                </a>
            </div>
        `;
        
        targetNav.appendChild(userMenu);
        
        // Setup dropdown functionality
        const toggle = userMenu.querySelector('.user-menu-toggle');
        const dropdown = userMenu.querySelector('.user-dropdown');
        
        toggle.addEventListener('click', function(e) {
            e.stopPropagation();
            dropdown.style.display = dropdown.style.display === 'block' ? 'none' : 'block';
        });
        
        // Close on outside click
        document.addEventListener('click', function(e) {
            if (!userMenu.contains(e.target)) {
                dropdown.style.display = 'none';
            }
        });
        
        // Setup logout
        const logoutBtn = userMenu.querySelector('.logout-btn');
        logoutBtn.addEventListener('click', function(e) {
            e.preventDefault();
            if (confirm('Are you sure you want to logout?')) {
                // Only clear auth on explicit logout
                localStorage.removeItem(AUTH_CONFIG.tokenKey);
                localStorage.removeItem(AUTH_CONFIG.userKey);
                localStorage.removeItem(AUTH_CONFIG.userKeyLegacy);
                localStorage.removeItem(AUTH_CONFIG.refreshKey);
                window.location.href = '/';
            }
        });
        
        // Add hover effects
        const items = userMenu.querySelectorAll('.dropdown-item');
        items.forEach(item => {
            item.addEventListener('mouseenter', function() {
                this.style.background = '#f0f2f5';
            });
            item.addEventListener('mouseleave', function() {
                this.style.background = 'transparent';
            });
        });
    }
    
    // DON'T verify with backend - just trust localStorage
    // This prevents clearing auth on API errors
    function initAuth() {
        console.log('[Auth Fixed] Checking authentication state...');
        updateAuthUI();
    }
    
    // Initialize on DOM ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initAuth);
    } else {
        initAuth();
    }
    
    // Also run after delay for dynamic content
    setTimeout(initAuth, 1000);
    
    // Listen for storage changes (login/logout in other tabs)
    window.addEventListener('storage', function(e) {
        if ([AUTH_CONFIG.tokenKey, AUTH_CONFIG.userKey, AUTH_CONFIG.userKeyLegacy].includes(e.key)) {
            console.log('[Auth Fixed] Auth state changed in another tab');
            updateAuthUI();
        }
    });
    
    // Expose logout function globally
    window.authLogout = function() {
        localStorage.removeItem(AUTH_CONFIG.tokenKey);
        localStorage.removeItem(AUTH_CONFIG.userKey);
        localStorage.removeItem(AUTH_CONFIG.userKeyLegacy);
        localStorage.removeItem(AUTH_CONFIG.refreshKey);
        window.location.href = '/';
    };
})();