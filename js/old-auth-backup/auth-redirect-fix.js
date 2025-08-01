// Authentication Redirect Fix
// This script handles proper redirects after login/signup

(function() {
    console.log('[Auth Redirect Fix] Initializing...');
    
    // Check if we're on login or signup page
    const isLoginPage = window.location.pathname.includes('login.html');
    const isSignupPage = window.location.pathname.includes('signup.html');
    
    if (!isLoginPage && !isSignupPage) {
        return; // Not on auth pages
    }
    
    // Get redirect URL from session storage or URL params
    function getRedirectUrl() {
        // First check session storage (set by stripe integration)
        const sessionRedirect = sessionStorage.getItem('redirect_after_login');
        if (sessionRedirect) {
            console.log('[Auth Redirect Fix] Found redirect in session:', sessionRedirect);
            return sessionRedirect;
        }
        
        // Check URL parameters
        const urlParams = new URLSearchParams(window.location.search);
        const redirectParam = urlParams.get('redirect');
        if (redirectParam) {
            console.log('[Auth Redirect Fix] Found redirect in URL:', redirectParam);
            return redirectParam;
        }
        
        // Default to dashboard
        return '/dashboard.html';
    }
    
    // Override the default redirect behavior
    const originalHandleLogin = window.AuthForms?.handleLogin;
    if (originalHandleLogin) {
        window.AuthForms.handleLogin = async function(formData) {
            try {
                // Call original login handler
                const result = await originalHandleLogin.call(this, formData);
                
                // Get redirect URL
                const redirectUrl = getRedirectUrl();
                
                // Clear session storage
                sessionStorage.removeItem('redirect_after_login');
                sessionStorage.removeItem('intended_plan');
                
                // Redirect to intended page
                console.log('[Auth Redirect Fix] Login successful, redirecting to:', redirectUrl);
                setTimeout(() => {
                    window.location.href = redirectUrl;
                }, 1000);
                
                return result;
            } catch (error) {
                throw error;
            }
        };
    }
    
    // Also intercept direct form submissions
    document.addEventListener('DOMContentLoaded', () => {
        const loginForm = document.getElementById('loginForm');
        if (loginForm) {
            const originalSubmit = loginForm.onsubmit;
            loginForm.onsubmit = function(e) {
                // Store current redirect URL before submission
                const redirectUrl = getRedirectUrl();
                console.log('[Auth Redirect Fix] Storing redirect URL before submission:', redirectUrl);
                
                // Let the original handler run
                if (originalSubmit) {
                    return originalSubmit.call(this, e);
                }
            };
        }
    });
    
    // Monitor for successful login via localStorage changes
    window.addEventListener('storage', (e) => {
        if (e.key === 'access_token' && e.newValue) {
            console.log('[Auth Redirect Fix] Detected login via storage event');
            const redirectUrl = getRedirectUrl();
            if (redirectUrl && redirectUrl !== '/dashboard.html') {
                console.log('[Auth Redirect Fix] Redirecting to:', redirectUrl);
                window.location.href = redirectUrl;
            }
        }
    });
})();