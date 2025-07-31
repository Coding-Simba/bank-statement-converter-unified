// Auth Login Fix - Ensures proper redirect after login
(function() {
    console.log('[Auth Login Fix] Initializing...');
    
    // Only run on login page
    if (!window.location.pathname.includes('login.html')) {
        return;
    }
    
    // Check for saved redirect
    const savedRedirect = sessionStorage.getItem('redirect_after_stripe') || 
                         sessionStorage.getItem('stripe_redirect') || 
                         sessionStorage.getItem('redirect_after_login');
    
    if (savedRedirect) {
        console.log('[Auth Login Fix] Found saved redirect:', savedRedirect);
    }
    
    // Override the auth.js redirect
    if (window.AuthForms && window.AuthForms.handleLogin) {
        const originalHandleLogin = window.AuthForms.handleLogin;
        
        window.AuthForms.handleLogin = async function(formData) {
            console.log('[Auth Login Fix] Intercepting login...');
            
            try {
                // Call original login
                const result = await originalHandleLogin.call(this, formData);
                
                // Check for saved redirect
                const redirect = sessionStorage.getItem('redirect_after_stripe') || 
                               sessionStorage.getItem('stripe_redirect') || 
                               sessionStorage.getItem('redirect_after_login');
                
                if (redirect && redirect !== '/dashboard.html') {
                    console.log('[Auth Login Fix] Redirecting to saved URL:', redirect);
                    
                    // Clear session storage
                    sessionStorage.removeItem('redirect_after_stripe');
                    sessionStorage.removeItem('stripe_redirect');
                    sessionStorage.removeItem('redirect_after_login');
                    
                    // Override the redirect
                    setTimeout(() => {
                        window.location.href = redirect;
                    }, 500);
                    
                    // Prevent default redirect
                    return result;
                }
                
                return result;
            } catch (error) {
                throw error;
            }
        };
    }
    
    // Also intercept form submission directly
    document.addEventListener('DOMContentLoaded', () => {
        const loginForm = document.getElementById('loginForm');
        if (!loginForm) return;
        
        loginForm.addEventListener('submit', async (e) => {
            // Check if we have a saved redirect
            const redirect = sessionStorage.getItem('redirect_after_stripe') || 
                           sessionStorage.getItem('stripe_redirect') || 
                           sessionStorage.getItem('redirect_after_login');
            
            if (redirect) {
                console.log('[Auth Login Fix] Login form submitted, will redirect to:', redirect);
                
                // Wait for successful login by monitoring localStorage
                let checkCount = 0;
                const checkInterval = setInterval(() => {
                    if (localStorage.getItem('access_token')) {
                        console.log('[Auth Login Fix] Login successful, redirecting...');
                        clearInterval(checkInterval);
                        
                        // Clear saved data
                        sessionStorage.removeItem('redirect_after_stripe');
                        sessionStorage.removeItem('stripe_redirect');
                        sessionStorage.removeItem('redirect_after_login');
                        
                        // Redirect
                        window.location.href = redirect;
                    }
                    
                    checkCount++;
                    if (checkCount > 50) { // 5 seconds timeout
                        clearInterval(checkInterval);
                    }
                }, 100);
            }
        });
    });
    
    // Final fallback - monitor localStorage changes
    const originalSetItem = localStorage.setItem;
    localStorage.setItem = function(key, value) {
        originalSetItem.call(localStorage, key, value);
        
        if (key === 'access_token' && value) {
            const redirect = sessionStorage.getItem('redirect_after_stripe') || 
                           sessionStorage.getItem('stripe_redirect') || 
                           sessionStorage.getItem('redirect_after_login');
            
            if (redirect && redirect !== '/dashboard.html') {
                console.log('[Auth Login Fix] Token set, redirecting to:', redirect);
                
                // Restore original function
                localStorage.setItem = originalSetItem;
                
                // Clear session storage
                sessionStorage.removeItem('redirect_after_stripe');
                sessionStorage.removeItem('stripe_redirect');
                sessionStorage.removeItem('redirect_after_login');
                sessionStorage.removeItem('stripe_plan');
                
                // Redirect immediately
                window.location.href = redirect;
            }
        }
    };
})();