/**
 * 🚀 IMMEDIATE AUTH NAVBAR FIX
 * This runs immediately to update the navbar based on auth state
 */

(function() {
    'use strict';
    
    // Check auth state from localStorage (always use localStorage for persistence)
    const token = localStorage.getItem('access_token');
    const userStr = localStorage.getItem('user');
    let user = null;
    
    if (token && userStr) {
        try {
            user = JSON.parse(userStr);
        } catch (e) {}
    }
    
    // Function to update navbar
    function updateNavbarNow() {
        const navRight = document.querySelector('.nav-right');
        if (!navRight) return;
        
        const loginLink = navRight.querySelector('a[href="/login.html"]');
        const signupLink = navRight.querySelector('a[href="/signup.html"]');
        const userDropdown = navRight.querySelector('.user-dropdown');
        
        if (user && token) {
            // User is logged in - update navbar
            if (loginLink) loginLink.remove();
            if (signupLink) signupLink.remove();
            
            if (!userDropdown) {
                // Create user dropdown
                const dropdown = document.createElement('div');
                dropdown.className = 'user-dropdown dropdown';
                dropdown.innerHTML = `
                    <button class="nav-link dropdown-toggle user-dropdown-toggle">
                        <i class="fas fa-user-circle"></i>
                        <span class="user-email">${user.email}</span>
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
                        <a href="#" class="dropdown-item logout-btn" onclick="handleLogout(); return false;">
                            <i class="fas fa-sign-out-alt"></i>
                            Logout
                        </a>
                    </div>
                `;
                
                const mobileToggle = navRight.querySelector('.mobile-menu-toggle');
                if (mobileToggle) {
                    navRight.insertBefore(dropdown, mobileToggle);
                } else {
                    navRight.appendChild(dropdown);
                }
                
                // Add dropdown functionality
                const toggle = dropdown.querySelector('.user-dropdown-toggle');
                toggle.addEventListener('click', (e) => {
                    e.stopPropagation();
                    dropdown.classList.toggle('active');
                });
                
                // Close on outside click
                document.addEventListener('click', () => {
                    dropdown.classList.remove('active');
                });
            }
        }
    }
    
    // Global logout function
    window.handleLogout = async function() {
        try {
            const token = localStorage.getItem('access_token') || sessionStorage.getItem('access_token');
            if (token) {
                await fetch('/api/auth/logout', {
                    method: 'POST',
                    credentials: 'include',
                    headers: {
                        'Authorization': `Bearer ${token}`
                    }
                });
            }
        } catch (e) {}
        
        // Clear storage
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        localStorage.removeItem('user');
        sessionStorage.removeItem('access_token');
        sessionStorage.removeItem('refresh_token');
        sessionStorage.removeItem('user');
        
        // Redirect
        window.location.href = '/';
    };
    
    // Update immediately if DOM is ready
    if (document.readyState !== 'loading') {
        updateNavbarNow();
    } else {
        document.addEventListener('DOMContentLoaded', updateNavbarNow);
    }
    
    // Add required CSS inline to ensure it loads immediately
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
            font-weight: 500;
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
            border: 1px solid rgba(0,0,0,0.05);
        }
        
        .user-dropdown.active .user-menu {
            display: block;
            animation: dropdownSlide 0.2s ease-out;
        }
        
        @keyframes dropdownSlide {
            from {
                opacity: 0;
                transform: translateY(-10px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
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
        
        .user-menu .dropdown-item:first-child {
            border-radius: 8px 8px 0 0;
        }
        
        .user-menu .dropdown-item:last-child {
            border-radius: 0 0 8px 8px;
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
        
        @media (max-width: 768px) {
            .user-dropdown {
                display: none;
            }
        }
    `;
    document.head.appendChild(style);
})();