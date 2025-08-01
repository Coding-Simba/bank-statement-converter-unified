// Complete Authentication Navigation Fix
(function() {
    'use strict';
    
    console.log('[AuthNav] Starting authentication navigation...');
    
    // Function to update navigation
    async function updateNavigation() {
        // Wait for UnifiedAuth to be available
        let attempts = 0;
        while (attempts < 50 && (!window.UnifiedAuth || !window.UnifiedAuth.initialized)) {
            await new Promise(resolve => setTimeout(resolve, 100));
            attempts++;
        }
        
        if (!window.UnifiedAuth || !window.UnifiedAuth.initialized) {
            console.log('[AuthNav] UnifiedAuth not available after 5 seconds');
            return;
        }
        
        console.log('[AuthNav] UnifiedAuth is ready, checking authentication...');
        
        try {
            const isAuthenticated = window.UnifiedAuth.isAuthenticated();
            console.log('[AuthNav] Is authenticated:', isAuthenticated);
            
            if (isAuthenticated) {
                const user = window.UnifiedAuth.getUser();
                console.log('[AuthNav] User:', user);
                
                // Find the navigation elements
                const navRight = document.querySelector('.nav-right');
                if (!navRight) {
                    console.log('[AuthNav] Nav-right not found');
                    return;
                }
                
                // Find login and signup links
                const loginLink = navRight.querySelector('a[href="/login.html"], a[href="login.html"]');
                const signupLink = navRight.querySelector('a[href="/signup.html"], a[href="signup.html"]');
                
                console.log('[AuthNav] Found login link:', !!loginLink);
                console.log('[AuthNav] Found signup link:', !!signupLink);
                
                if (loginLink) {
                    // Replace login link with Dashboard
                    loginLink.textContent = 'Dashboard';
                    loginLink.href = '/dashboard.html';
                    loginLink.classList.add('nav-link');
                    console.log('[AuthNav] Updated login link to Dashboard');
                }
                
                if (signupLink) {
                    // Create user dropdown or logout button
                    const userEmail = user?.email || 'User';
                    
                    // Create a dropdown for user menu
                    const userDropdown = document.createElement('div');
                    userDropdown.className = 'user-dropdown';
                    userDropdown.innerHTML = `
                        <button class="user-dropdown-toggle">
                            <i class="fas fa-user-circle"></i>
                            <span class="user-email">${userEmail}</span>
                            <i class="fas fa-chevron-down"></i>
                        </button>
                        <div class="user-dropdown-menu">
                            <a href="/dashboard.html" class="dropdown-item">
                                <i class="fas fa-tachometer-alt"></i> Dashboard
                            </a>
                            <a href="/settings.html" class="dropdown-item">
                                <i class="fas fa-cog"></i> Settings
                            </a>
                            <div class="dropdown-divider"></div>
                            <a href="#" class="dropdown-item logout-btn">
                                <i class="fas fa-sign-out-alt"></i> Log Out
                            </a>
                        </div>
                    `;
                    
                    // Replace signup button with user dropdown
                    signupLink.parentNode.replaceChild(userDropdown, signupLink);
                    console.log('[AuthNav] Replaced signup with user dropdown');
                    
                    // Add dropdown toggle functionality
                    const toggle = userDropdown.querySelector('.user-dropdown-toggle');
                    const menu = userDropdown.querySelector('.user-dropdown-menu');
                    
                    toggle.addEventListener('click', (e) => {
                        e.stopPropagation();
                        menu.classList.toggle('show');
                    });
                    
                    // Close dropdown when clicking outside
                    document.addEventListener('click', () => {
                        menu.classList.remove('show');
                    });
                    
                    // Add logout functionality
                    const logoutBtn = userDropdown.querySelector('.logout-btn');
                    logoutBtn.addEventListener('click', async (e) => {
                        e.preventDefault();
                        if (confirm('Are you sure you want to log out?')) {
                            try {
                                await window.UnifiedAuth.logout();
                                window.location.href = '/';
                            } catch (error) {
                                console.error('[AuthNav] Logout error:', error);
                                // Force logout
                                localStorage.clear();
                                sessionStorage.clear();
                                window.location.href = '/';
                            }
                        }
                    });
                }
                
                // Also update mobile menu if present
                updateMobileMenu(user);
            }
        } catch (error) {
            console.error('[AuthNav] Error updating navigation:', error);
        }
    }
    
    // Function to update mobile menu
    function updateMobileMenu(user) {
        const mobileMenu = document.querySelector('.mobile-nav, .mobile-menu');
        if (!mobileMenu) return;
        
        const mobileLoginLink = mobileMenu.querySelector('a[href*="login"]');
        const mobileSignupLink = mobileMenu.querySelector('a[href*="signup"]');
        
        if (mobileLoginLink) {
            mobileLoginLink.textContent = 'Dashboard';
            mobileLoginLink.href = '/dashboard.html';
        }
        
        if (mobileSignupLink) {
            mobileSignupLink.textContent = 'Log Out';
            mobileSignupLink.href = '#';
            mobileSignupLink.onclick = async (e) => {
                e.preventDefault();
                if (confirm('Are you sure you want to log out?')) {
                    try {
                        await window.UnifiedAuth.logout();
                        window.location.href = '/';
                    } catch (error) {
                        console.error('[AuthNav] Mobile logout error:', error);
                        localStorage.clear();
                        sessionStorage.clear();
                        window.location.href = '/';
                    }
                }
            };
        }
    }
    
    // Add CSS for user dropdown
    const style = document.createElement('style');
    style.textContent = `
        .user-dropdown {
            position: relative;
            display: inline-block;
        }
        
        .user-dropdown-toggle {
            background: transparent;
            border: 1px solid #ddd;
            border-radius: 8px;
            padding: 8px 16px;
            display: flex;
            align-items: center;
            gap: 8px;
            cursor: pointer;
            font-size: 14px;
            color: #333;
            transition: all 0.3s ease;
        }
        
        .user-dropdown-toggle:hover {
            background: #f5f5f5;
            border-color: #007bff;
        }
        
        .user-dropdown-toggle i {
            font-size: 16px;
        }
        
        .user-email {
            max-width: 150px;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }
        
        .user-dropdown-menu {
            position: absolute;
            top: 100%;
            right: 0;
            margin-top: 8px;
            background: white;
            border: 1px solid #ddd;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
            min-width: 200px;
            opacity: 0;
            visibility: hidden;
            transform: translateY(-10px);
            transition: all 0.3s ease;
            z-index: 1000;
        }
        
        .user-dropdown-menu.show {
            opacity: 1;
            visibility: visible;
            transform: translateY(0);
        }
        
        .dropdown-item {
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 12px 16px;
            color: #333;
            text-decoration: none;
            transition: background 0.2s ease;
        }
        
        .dropdown-item:hover {
            background: #f5f5f5;
        }
        
        .dropdown-item i {
            width: 16px;
            text-align: center;
            color: #666;
        }
        
        .dropdown-divider {
            height: 1px;
            background: #eee;
            margin: 8px 0;
        }
        
        .logout-btn {
            color: #dc3545;
        }
        
        .logout-btn i {
            color: #dc3545;
        }
        
        @media (max-width: 768px) {
            .user-dropdown-toggle .user-email {
                display: none;
            }
        }
    `;
    document.head.appendChild(style);
    
    // Run when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', updateNavigation);
    } else {
        updateNavigation();
    }
    
    // Re-check when window gains focus
    window.addEventListener('focus', async () => {
        if (window.UnifiedAuth && window.UnifiedAuth.initialized) {
            const isAuth = window.UnifiedAuth.isAuthenticated();
            const hasDropdown = document.querySelector('.user-dropdown');
            
            // If auth state changed, reload page
            if ((isAuth && !hasDropdown) || (!isAuth && hasDropdown)) {
                window.location.reload();
            }
        }
    });
})();