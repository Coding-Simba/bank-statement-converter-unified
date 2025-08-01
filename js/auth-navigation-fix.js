// Fixed Authentication Navigation - Updates nav based on auth status
document.addEventListener('DOMContentLoaded', async () => {
    console.log('Auth navigation initializing...');
    
    // Wait for UnifiedAuth to initialize
    const waitForAuth = async () => {
        let attempts = 0;
        while (attempts < 50) { // Wait up to 5 seconds
            if (window.UnifiedAuth && window.UnifiedAuth.initialized) {
                return true;
            }
            await new Promise(resolve => setTimeout(resolve, 100));
            attempts++;
        }
        return false;
    };
    
    const authReady = await waitForAuth();
    if (!authReady) {
        console.log('UnifiedAuth not initialized, keeping default navigation');
        return;
    }
    
    // Check if user is authenticated
    const isAuthenticated = window.UnifiedAuth && window.UnifiedAuth.isAuthenticated();
    console.log('User authenticated:', isAuthenticated);
    
    if (isAuthenticated) {
        const user = window.UnifiedAuth.getUser();
        console.log('Updating navigation for authenticated user');
        
        // Find all login links (multiple selectors for different pages)
        const loginLinks = document.querySelectorAll('a[href="/login.html"], a[href="login.html"], .nav-link:contains("Log In"), .nav-link:contains("Sign In")');
        const signupLinks = document.querySelectorAll('a[href="/signup.html"], a[href="signup.html"], .btn-primary[href*="signup"], a:contains("Sign Up")');
        
        // More robust selector for login links
        const allLinks = document.querySelectorAll('a');
        allLinks.forEach(link => {
            const text = link.textContent.trim().toLowerCase();
            const href = link.getAttribute('href') || '';
            
            // Update login links to dashboard
            if (text === 'log in' || text === 'sign in' || text === 'login' || href.includes('login')) {
                if (href.includes('login.html')) {
                    link.textContent = 'Dashboard';
                    link.href = '/dashboard.html';
                    console.log('Updated login link to dashboard');
                }
            }
            
            // Update signup links to logout
            if (text === 'sign up' || text === 'sign up free' || text === 'signup' || href.includes('signup')) {
                if (href.includes('signup.html')) {
                    link.textContent = 'Log Out';
                    link.href = '#';
                    link.classList.remove('btn-primary');
                    link.classList.add('btn-secondary');
                    
                    // Remove any existing click handlers
                    const newLink = link.cloneNode(true);
                    link.parentNode.replaceChild(newLink, link);
                    
                    // Add logout handler
                    newLink.addEventListener('click', async (e) => {
                        e.preventDefault();
                        if (confirm('Are you sure you want to log out?')) {
                            try {
                                await window.UnifiedAuth.logout();
                                window.location.href = '/';
                            } catch (error) {
                                console.error('Logout error:', error);
                                // Force logout on error
                                localStorage.clear();
                                sessionStorage.clear();
                                window.location.href = '/';
                            }
                        }
                    });
                    console.log('Updated signup link to logout');
                }
            }
        });
        
        // Also update mobile navigation if present
        const mobileLoginLinks = document.querySelectorAll('.mobile-nav a[href*="login"]');
        const mobileSignupLinks = document.querySelectorAll('.mobile-nav a[href*="signup"]');
        
        mobileLoginLinks.forEach(link => {
            if (link.getAttribute('href').includes('login.html')) {
                link.textContent = 'Dashboard';
                link.href = '/dashboard.html';
            }
        });
        
        mobileSignupLinks.forEach(link => {
            if (link.getAttribute('href').includes('signup.html')) {
                link.textContent = 'Log Out';
                link.href = '#';
                link.classList.remove('btn-primary');
                link.classList.add('btn-secondary');
                
                const newLink = link.cloneNode(true);
                link.parentNode.replaceChild(newLink, link);
                
                newLink.addEventListener('click', async (e) => {
                    e.preventDefault();
                    if (confirm('Are you sure you want to log out?')) {
                        try {
                            await window.UnifiedAuth.logout();
                            window.location.href = '/';
                        } catch (error) {
                            console.error('Logout error:', error);
                            localStorage.clear();
                            sessionStorage.clear();
                            window.location.href = '/';
                        }
                    }
                });
            }
        });
        
        // Add user info if there's a designated spot
        const userInfoSpot = document.querySelector('.user-info');
        if (userInfoSpot && user) {
            userInfoSpot.textContent = user.email || 'User';
        }
    }
});

// Re-check auth status when window gains focus (in case user logged in/out in another tab)
window.addEventListener('focus', () => {
    if (window.UnifiedAuth && window.UnifiedAuth.initialized) {
        const currentAuth = window.UnifiedAuth.isAuthenticated();
        const navShowsDashboard = document.querySelector('a[href="/dashboard.html"]');
        
        // If auth status changed, reload the page to update navigation
        if ((currentAuth && !navShowsDashboard) || (!currentAuth && navShowsDashboard)) {
            console.log('Auth status changed, reloading page');
            window.location.reload();
        }
    }
});