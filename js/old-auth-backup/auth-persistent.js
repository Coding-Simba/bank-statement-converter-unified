// Persistent Authentication System
// This script maintains auth state across all pages

(function() {
    console.log('[Auth] Checking authentication state...');
    
    // Migrate old user data if needed
    if (localStorage.getItem('user') && !localStorage.getItem('user_data')) {
        console.log('[Auth] Migrating user data to new format...');
        localStorage.setItem('user_data', localStorage.getItem('user'));
    }
    
    // Get auth data
    const token = localStorage.getItem('access_token');
    const userStr = localStorage.getItem('user_data') || localStorage.getItem('user'); // Check both keys for compatibility
    
    console.log('[Auth] Token exists:', !!token);
    console.log('[Auth] User data exists:', !!userStr);
    
    // Parse user data safely
    let userData = null;
    if (userStr) {
        try {
            userData = JSON.parse(userStr);
            console.log('[Auth] User email:', userData.email);
        } catch (e) {
            console.error('[Auth] Failed to parse user data:', e);
        }
    }
    
    // Wait for DOM to be ready
    function initAuth() {
        console.log('[Auth] Initializing auth UI...');
        
        // Find navigation elements - try multiple selectors
        const navRight = document.querySelector('.nav-right');
        const navAuth = document.querySelector('.nav-auth');
        const navContainer = document.querySelector('.nav-container');
        const navMenu = document.querySelector('.nav-menu');
        
        console.log('[Auth] Found nav-right:', !!navRight);
        console.log('[Auth] Found nav-auth:', !!navAuth);
        console.log('[Auth] Found nav-container:', !!navContainer);
        console.log('[Auth] Found nav-menu:', !!navMenu);
        
        // Determine where to add auth UI
        let targetNav = navRight || navAuth;
        
        // For pricing page and similar layouts
        if (!targetNav && navContainer) {
            // Create a nav-auth div at the end of nav-container
            const authDiv = document.createElement('div');
            authDiv.className = 'nav-auth';
            authDiv.style.cssText = 'margin-left: auto; display: flex; align-items: center; gap: 1rem;';
            navContainer.appendChild(authDiv);
            targetNav = authDiv;
            console.log('[Auth] Created nav-auth element');
        }
        
        if (!targetNav) {
            console.warn('[Auth] No suitable navigation container found');
            return;
        }
        
        if (token && userData) {
            // User is logged in
            console.log('[Auth] User is authenticated, updating UI...');
            
            // Find and remove login/signup links
            const loginLinks = targetNav.querySelectorAll('a[href="/login.html"], a[href="/signup.html"], .btn-primary[href="/signup.html"]');
            console.log('[Auth] Found login/signup links:', loginLinks.length);
            
            loginLinks.forEach(link => {
                console.log('[Auth] Removing:', link.textContent);
                link.remove();
            });
            
            // Check if user menu already exists
            let userMenu = targetNav.querySelector('.user-menu');
            if (!userMenu) {
                console.log('[Auth] Creating user menu...');
                
                // Create user menu HTML
                const userMenuHTML = `
                    <div class="user-menu">
                        <button class="user-menu-toggle" id="userMenuToggle">
                            <i class="fas fa-user-circle"></i>
                            <span class="user-email">${userData.email || 'Account'}</span>
                            <i class="fas fa-chevron-down"></i>
                        </button>
                        <div class="user-dropdown" id="userDropdown">
                            <div class="dropdown-header">
                                <div class="user-info">
                                    <i class="fas fa-user-circle"></i>
                                    <span>${userData.email}</span>
                                </div>
                            </div>
                            <a href="/dashboard.html" class="dropdown-item">
                                <i class="fas fa-tachometer-alt"></i> Dashboard
                            </a>
                            <a href="/settings.html" class="dropdown-item">
                                <i class="fas fa-cog"></i> Settings
                            </a>
                            <div class="dropdown-divider"></div>
                            <a href="#" class="dropdown-item logout-btn">
                                <i class="fas fa-sign-out-alt"></i> Logout
                            </a>
                        </div>
                    </div>
                `;
                
                // Insert user menu
                targetNav.insertAdjacentHTML('beforeend', userMenuHTML);
                
                // Setup event listeners
                setupUserMenu();
            }
        } else {
            // User is not logged in
            console.log('[Auth] User is not authenticated');
            
            // Remove any existing user menu
            const userMenu = targetNav.querySelector('.user-menu');
            if (userMenu) {
                console.log('[Auth] Removing user menu');
                userMenu.remove();
            }
            
            // Ensure login/signup links exist
            const hasLogin = targetNav.querySelector('a[href="/login.html"]');
            const hasSignup = targetNav.querySelector('a[href="/signup.html"]');
            
            if (!hasLogin && !hasSignup) {
                console.log('[Auth] Adding login/signup links');
                targetNav.insertAdjacentHTML('beforeend', `
                    <a href="/login.html" class="nav-link">Log In</a>
                    <a href="/signup.html" class="btn-primary">Sign Up Free</a>
                `);
            }
        }
    }
    
    // Setup user menu functionality
    function setupUserMenu() {
        const toggle = document.getElementById('userMenuToggle');
        const dropdown = document.getElementById('userDropdown');
        const logoutBtns = document.querySelectorAll('.logout-btn');
        
        if (toggle) {
            toggle.addEventListener('click', function(e) {
                e.stopPropagation();
                const menu = this.closest('.user-menu');
                menu.classList.toggle('active');
                console.log('[Auth] Menu toggled');
            });
        }
        
        // Close menu on outside click
        document.addEventListener('click', function(e) {
            const menus = document.querySelectorAll('.user-menu');
            menus.forEach(menu => {
                if (!menu.contains(e.target)) {
                    menu.classList.remove('active');
                }
            });
        });
        
        // Setup logout buttons
        logoutBtns.forEach(btn => {
            btn.addEventListener('click', function(e) {
                e.preventDefault();
                console.log('[Auth] Logging out...');
                localStorage.removeItem('access_token');
                localStorage.removeItem('user');
                window.location.href = '/';
            });
        });
    }
    
    // Add styles
    function addStyles() {
        if (document.getElementById('auth-persistent-styles')) return;
        
        const styles = document.createElement('style');
        styles.id = 'auth-persistent-styles';
        styles.textContent = `
            .user-menu {
                position: relative;
                display: inline-block;
            }
            
            .user-menu-toggle {
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
                transition: all 0.2s ease;
                font-family: inherit;
            }
            
            .user-menu-toggle:hover {
                background: #00bfa5;
                color: white;
            }
            
            .user-email {
                max-width: 150px;
                overflow: hidden;
                text-overflow: ellipsis;
                white-space: nowrap;
            }
            
            @media (max-width: 768px) {
                .user-email {
                    display: none;
                }
            }
            
            .user-dropdown {
                position: absolute;
                top: 100%;
                right: 0;
                margin-top: 0.5rem;
                background: white;
                border: 1px solid #e5e7eb;
                border-radius: 0.5rem;
                box-shadow: 0 10px 25px rgba(0, 0, 0, 0.1);
                min-width: 220px;
                opacity: 0;
                visibility: hidden;
                transform: translateY(-10px);
                transition: all 0.2s ease;
                z-index: 1000;
            }
            
            .user-menu.active .user-dropdown {
                opacity: 1;
                visibility: visible;
                transform: translateY(0);
            }
            
            .dropdown-header {
                padding: 1rem;
                border-bottom: 1px solid #e5e7eb;
                background: #f8f9fa;
            }
            
            .user-info {
                display: flex;
                align-items: center;
                gap: 0.75rem;
                font-size: 0.875rem;
                color: #495057;
            }
            
            .user-info i {
                font-size: 1.25rem;
            }
            
            .dropdown-item {
                display: flex;
                align-items: center;
                gap: 0.75rem;
                padding: 0.75rem 1rem;
                color: #495057;
                text-decoration: none;
                transition: all 0.2s ease;
                font-size: 0.875rem;
            }
            
            .dropdown-item:hover {
                background: #f0f2f5;
                color: #212529;
            }
            
            .dropdown-item i {
                width: 16px;
                text-align: center;
            }
            
            .dropdown-divider {
                height: 1px;
                background: #e5e7eb;
                margin: 0;
            }
            
            /* Ensure nav items align properly */
            .nav-right {
                display: flex;
                align-items: center;
                gap: 1rem;
            }
            
            .nav-auth {
                display: flex;
                align-items: center;
                gap: 1rem;
            }
        `;
        document.head.appendChild(styles);
    }
    
    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function() {
            console.log('[Auth] DOM loaded, initializing...');
            addStyles();
            initAuth();
        });
    } else {
        console.log('[Auth] DOM already loaded, initializing...');
        addStyles();
        initAuth();
    }
    
    // Also run after a short delay to catch any dynamic content
    setTimeout(function() {
        console.log('[Auth] Running delayed initialization...');
        initAuth();
    }, 500);
})();