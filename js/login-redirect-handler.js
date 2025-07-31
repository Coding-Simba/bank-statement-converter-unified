// Login Redirect Handler - Ensures proper redirect after login
(function() {
    console.log('[Login Redirect] Initializing...');
    
    // Only run on login page
    if (!window.location.pathname.includes('login.html')) {
        return;
    }
    
    // Check for saved redirect info
    const savedPlan = sessionStorage.getItem('stripe_plan') || sessionStorage.getItem('intended_plan');
    const savedRedirect = sessionStorage.getItem('stripe_redirect') || sessionStorage.getItem('redirect_after_login');
    
    if (savedPlan || savedRedirect) {
        console.log('[Login Redirect] Found saved redirect info:', {
            plan: savedPlan,
            redirect: savedRedirect
        });
    }
    
    // Override form submission to handle redirect
    document.addEventListener('DOMContentLoaded', () => {
        const loginForm = document.getElementById('loginForm');
        if (!loginForm) {
            console.log('[Login Redirect] No login form found');
            return;
        }
        
        loginForm.addEventListener('submit', async (e) => {
            // Let the default auth.js handle the login
            // We'll check for success via storage event
            console.log('[Login Redirect] Login form submitted');
        });
    });
    
    // Listen for successful login
    let checkCount = 0;
    const checkLogin = setInterval(() => {
        const token = localStorage.getItem('access_token');
        if (token) {
            console.log('[Login Redirect] Login successful, checking redirect...');
            clearInterval(checkLogin);
            
            const savedRedirect = sessionStorage.getItem('stripe_redirect') || 
                                 sessionStorage.getItem('redirect_after_login') ||
                                 '/dashboard.html';
            
            // Clear session storage
            sessionStorage.removeItem('stripe_plan');
            sessionStorage.removeItem('intended_plan');
            sessionStorage.removeItem('stripe_redirect');
            sessionStorage.removeItem('redirect_after_login');
            
            console.log('[Login Redirect] Redirecting to:', savedRedirect);
            
            // Small delay to ensure everything is saved
            setTimeout(() => {
                window.location.href = savedRedirect;
            }, 500);
        }
        
        checkCount++;
        if (checkCount > 100) { // Stop after 10 seconds
            clearInterval(checkLogin);
        }
    }, 100);
})();