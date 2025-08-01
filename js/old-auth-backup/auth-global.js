// Global Authentication Handler
// This script should be included on ALL pages to maintain authentication state

(function() {
    // Check if user is authenticated
    const token = localStorage.getItem('access_token');
    const user = localStorage.getItem('user');
    
    // Function to update navigation based on auth state
    function updateNavigation() {
        const navAuth = document.querySelector('.nav-auth');
        const navRight = document.querySelector('.nav-right');
        const userMenu = document.querySelector('.user-menu');
        
        if (token && user) {
            // User is logged in
            try {
                const userData = JSON.parse(user);
                
                // Update navigation for logged-in user
                if (navAuth) {
                    navAuth.innerHTML = `
                        <a href="/dashboard.html" class="nav-link">Dashboard</a>
                        <div class="user-menu">
                            <button class="user-menu-toggle" id="userMenuToggle">
                                <i class="fas fa-user-circle"></i>
                                <span class="desktop-only">${userData.email || 'Account'}</span>
                                <i class="fas fa-chevron-down"></i>
                            </button>
                            <div class="user-dropdown" id="userDropdown">
                                <a href="/dashboard.html" class="dropdown-item">
                                    <i class="fas fa-tachometer-alt"></i> Dashboard
                                </a>
                                <a href="/settings.html" class="dropdown-item">
                                    <i class="fas fa-cog"></i> Settings
                                </a>
                                <div class="dropdown-divider"></div>
                                <a href="#" class="dropdown-item" onclick="logout()">
                                    <i class="fas fa-sign-out-alt"></i> Logout
                                </a>
                            </div>
                        </div>
                    `;
                } else if (navRight) {
                    // For pages using nav-right structure
                    const existingUserMenu = navRight.querySelector('.user-menu');
                    if (!existingUserMenu) {
                        // Remove login/signup buttons
                        const loginLink = navRight.querySelector('a[href="/login.html"]');
                        const signupLink = navRight.querySelector('a[href="/signup.html"]');
                        
                        if (loginLink) loginLink.remove();
                        if (signupLink) signupLink.remove();
                        
                        // Add user menu
                        const userMenuHtml = `
                            <div class="user-menu">
                                <button class="user-menu-toggle" id="userMenuToggle">
                                    <i class="fas fa-user-circle"></i>
                                    <span class="desktop-only">${userData.email || 'Account'}</span>
                                    <i class="fas fa-chevron-down"></i>
                                </button>
                                <div class="user-dropdown" id="userDropdown">
                                    <a href="/dashboard.html" class="dropdown-item">
                                        <i class="fas fa-tachometer-alt"></i> Dashboard
                                    </a>
                                    <a href="/settings.html" class="dropdown-item">
                                        <i class="fas fa-cog"></i> Settings
                                    </a>
                                    <div class="dropdown-divider"></div>
                                    <a href="#" class="dropdown-item" onclick="logout()">
                                        <i class="fas fa-sign-out-alt"></i> Logout
                                    </a>
                                </div>
                            </div>
                        `;
                        navRight.insertAdjacentHTML('beforeend', userMenuHtml);
                    }
                }
                
                // Setup user menu toggle
                setupUserMenu();
                
            } catch (error) {
                console.error('Error parsing user data:', error);
            }
        } else {
            // User is not logged in - ensure login/signup buttons are shown
            if (navAuth) {
                navAuth.innerHTML = `
                    <a href="/login.html" class="nav-link">Login</a>
                    <a href="/signup.html" class="btn btn-primary">Sign Up</a>
                `;
            } else if (navRight && !navRight.querySelector('a[href="/login.html"]')) {
                // For pages using nav-right structure
                const userMenu = navRight.querySelector('.user-menu');
                if (userMenu) {
                    userMenu.remove();
                }
                
                // Add login/signup if not present
                if (!navRight.querySelector('a[href="/login.html"]')) {
                    navRight.insertAdjacentHTML('beforeend', `
                        <a href="/login.html" class="nav-link">Log In</a>
                        <a href="/signup.html" class="btn-primary">Sign Up Free</a>
                    `);
                }
            }
        }
    }
    
    // Setup user menu functionality
    function setupUserMenu() {
        const userMenuToggle = document.getElementById('userMenuToggle');
        const userDropdown = document.getElementById('userDropdown');
        
        if (userMenuToggle && userDropdown) {
            // Remove any existing listeners
            const newToggle = userMenuToggle.cloneNode(true);
            userMenuToggle.parentNode.replaceChild(newToggle, userMenuToggle);
            
            newToggle.addEventListener('click', function(e) {
                e.stopPropagation();
                const userMenu = this.closest('.user-menu');
                userMenu.classList.toggle('active');
            });
            
            // Close on outside click
            document.addEventListener('click', function(e) {
                const userMenus = document.querySelectorAll('.user-menu');
                userMenus.forEach(menu => {
                    if (!menu.contains(e.target)) {
                        menu.classList.remove('active');
                    }
                });
            });
        }
    }
    
    // Global logout function
    window.logout = function() {
        localStorage.removeItem('access_token');
        localStorage.removeItem('user');
        window.location.href = '/';
    };
    
    // Verify token is still valid
    async function verifyAuth() {
        if (!token) return;
        
        try {
            const response = await fetch('/api/auth/verify', {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });
            
            if (!response.ok) {
                // Token is invalid or expired
                localStorage.removeItem('access_token');
                localStorage.removeItem('user');
                updateNavigation();
            }
        } catch (error) {
            console.error('Auth verification error:', error);
        }
    }
    
    // Initialize on DOM ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function() {
            updateNavigation();
            verifyAuth();
        });
    } else {
        updateNavigation();
        verifyAuth();
    }
    
    // Add styles for user menu if not present
    if (!document.querySelector('#auth-global-styles')) {
        const styles = document.createElement('style');
        styles.id = 'auth-global-styles';
        styles.textContent = `
            .user-menu {
                position: relative;
            }
            
            .user-menu-toggle {
                display: flex;
                align-items: center;
                gap: 0.5rem;
                padding: 0.5rem 1rem;
                background: var(--light-gray, #f0f2f5);
                border: 1px solid transparent;
                border-radius: 9999px;
                color: var(--black, #212529);
                font-size: 0.875rem;
                font-weight: 500;
                cursor: pointer;
                transition: all 0.2s ease;
            }
            
            .user-menu-toggle:hover {
                background: var(--primary-light, #1dd1b7);
                color: white;
            }
            
            .user-dropdown {
                position: absolute;
                top: 100%;
                right: 0;
                margin-top: 0.5rem;
                background: white;
                border: 1px solid var(--light-gray, #f0f2f5);
                border-radius: 0.5rem;
                box-shadow: 0 10px 25px rgba(0, 0, 0, 0.1);
                min-width: 200px;
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
            
            .dropdown-item {
                display: flex;
                align-items: center;
                gap: 0.75rem;
                padding: 0.75rem 1rem;
                color: var(--dark-gray, #495057);
                text-decoration: none;
                transition: all 0.2s ease;
            }
            
            .dropdown-item:hover {
                background: var(--light-gray, #f0f2f5);
                color: var(--black, #212529);
            }
            
            .dropdown-divider {
                height: 1px;
                background: var(--light-gray, #f0f2f5);
                margin: 0.5rem 0;
            }
            
            @media (max-width: 768px) {
                .desktop-only {
                    display: none;
                }
            }
        `;
        document.head.appendChild(styles);
    }
})();