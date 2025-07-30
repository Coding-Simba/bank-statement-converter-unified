// Universal Authentication Handler
// This script ensures authentication state is properly reflected on ALL pages

(function() {
    console.log('[Auth Universal] Initializing...');
    
    // Function to check and update auth state
    function updateAuthState() {
        const token = localStorage.getItem('access_token');
        const userDataStr = localStorage.getItem('user_data') || localStorage.getItem('user');
        
        console.log('[Auth Universal] Checking auth:', {
            hasToken: !!token,
            hasUserData: !!userDataStr
        });
        
        if (!token || !userDataStr) {
            console.log('[Auth Universal] Not authenticated');
            return;
        }
        
        let userData;
        try {
            userData = JSON.parse(userDataStr);
        } catch (e) {
            console.error('[Auth Universal] Failed to parse user data');
            return;
        }
        
        console.log('[Auth Universal] User authenticated:', userData.email);
        
        // Find ALL possible login/signup elements
        const selectors = [
            'a[href="/login.html"]',
            'a[href="/signup.html"]',
            '.btn-primary[href="/signup.html"]',
            'a:contains("Log In")',
            'a:contains("Sign Up")'
        ];
        
        // Remove all login/signup links
        selectors.forEach(selector => {
            const elements = document.querySelectorAll(selector);
            elements.forEach(el => {
                if (el.textContent.includes('Log In') || 
                    el.textContent.includes('Sign Up') || 
                    el.href?.includes('login.html') || 
                    el.href?.includes('signup.html')) {
                    console.log('[Auth Universal] Removing:', el.textContent);
                    el.remove();
                }
            });
        });
        
        // Find the navigation container
        const navContainers = [
            document.querySelector('.nav-right'),
            document.querySelector('.nav-auth'),
            document.querySelector('.nav-container'),
            document.querySelector('nav')
        ].filter(Boolean);
        
        if (navContainers.length === 0) {
            console.error('[Auth Universal] No navigation container found');
            return;
        }
        
        // Use the most specific container
        let targetContainer = navContainers[0];
        
        // For nav-container, create a nav-right div
        if (targetContainer.classList.contains('nav-container') && !targetContainer.querySelector('.nav-right')) {
            const navRight = document.createElement('div');
            navRight.className = 'nav-right';
            navRight.style.cssText = 'margin-left: auto; display: flex; align-items: center; gap: 1rem;';
            
            // Insert before menu toggle if exists
            const menuToggle = targetContainer.querySelector('.menu-toggle, #menuToggle');
            if (menuToggle) {
                targetContainer.insertBefore(navRight, menuToggle);
            } else {
                targetContainer.appendChild(navRight);
            }
            targetContainer = navRight;
            console.log('[Auth Universal] Created nav-right container');
        }
        
        // Check if user menu already exists
        if (targetContainer.querySelector('.user-menu')) {
            console.log('[Auth Universal] User menu already exists');
            return;
        }
        
        // Create user menu
        const userMenuHTML = `
            <div class="user-menu" style="position: relative;">
                <button class="user-menu-toggle" id="userMenuToggle" style="
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
                ">
                    <i class="fas fa-user-circle"></i>
                    <span class="user-email">${userData.email}</span>
                    <i class="fas fa-chevron-down"></i>
                </button>
                <div class="user-dropdown" id="userDropdown" style="
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
                    z-index: 9999;
                ">
                    <a href="/dashboard.html" class="dropdown-item" style="
                        display: flex;
                        align-items: center;
                        gap: 0.75rem;
                        padding: 0.75rem 1rem;
                        color: #495057;
                        text-decoration: none;
                        transition: all 0.2s ease;
                        font-size: 0.875rem;
                    ">
                        <i class="fas fa-tachometer-alt"></i> Dashboard
                    </a>
                    <a href="/settings.html" class="dropdown-item" style="
                        display: flex;
                        align-items: center;
                        gap: 0.75rem;
                        padding: 0.75rem 1rem;
                        color: #495057;
                        text-decoration: none;
                        transition: all 0.2s ease;
                        font-size: 0.875rem;
                    ">
                        <i class="fas fa-cog"></i> Settings
                    </a>
                    <div style="height: 1px; background: #e5e7eb; margin: 0;"></div>
                    <a href="#" class="dropdown-item logout-btn" onclick="event.preventDefault(); localStorage.clear(); window.location.href='/';" style="
                        display: flex;
                        align-items: center;
                        gap: 0.75rem;
                        padding: 0.75rem 1rem;
                        color: #495057;
                        text-decoration: none;
                        transition: all 0.2s ease;
                        font-size: 0.875rem;
                    ">
                        <i class="fas fa-sign-out-alt"></i> Logout
                    </a>
                </div>
            </div>
        `;
        
        targetContainer.insertAdjacentHTML('beforeend', userMenuHTML);
        console.log('[Auth Universal] User menu added');
        
        // Setup dropdown functionality
        const toggle = document.getElementById('userMenuToggle');
        const menu = toggle?.closest('.user-menu');
        
        if (toggle && menu) {
            toggle.addEventListener('click', function(e) {
                e.stopPropagation();
                const dropdown = menu.querySelector('.user-dropdown');
                const isOpen = dropdown.style.opacity === '1';
                
                if (isOpen) {
                    dropdown.style.opacity = '0';
                    dropdown.style.visibility = 'hidden';
                    dropdown.style.transform = 'translateY(-10px)';
                } else {
                    dropdown.style.opacity = '1';
                    dropdown.style.visibility = 'visible';
                    dropdown.style.transform = 'translateY(0)';
                }
            });
            
            // Close on outside click
            document.addEventListener('click', function(e) {
                if (!menu.contains(e.target)) {
                    const dropdown = menu.querySelector('.user-dropdown');
                    dropdown.style.opacity = '0';
                    dropdown.style.visibility = 'hidden';
                    dropdown.style.transform = 'translateY(-10px)';
                }
            });
        }
        
        // Add hover effects
        const dropdownItems = document.querySelectorAll('.dropdown-item');
        dropdownItems.forEach(item => {
            item.addEventListener('mouseenter', function() {
                this.style.background = '#f0f2f5';
                this.style.color = '#212529';
            });
            item.addEventListener('mouseleave', function() {
                this.style.background = 'transparent';
                this.style.color = '#495057';
            });
        });
    }
    
    // Run when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', updateAuthState);
    } else {
        updateAuthState();
    }
    
    // Also run after a delay to catch any dynamic content
    setTimeout(updateAuthState, 1000);
    
    // Listen for auth changes
    window.addEventListener('storage', function(e) {
        if (e.key === 'access_token' || e.key === 'user' || e.key === 'user_data') {
            updateAuthState();
        }
    });
})();