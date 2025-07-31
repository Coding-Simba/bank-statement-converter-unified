// Force Auth Storage - Ensures tokens are properly stored after login
(function() {
    console.log('[Force Auth] Initializing...');
    
    // Monitor all fetch responses for login success
    const originalFetch = window.fetch;
    window.fetch = async function(...args) {
        const [url, options] = args;
        
        try {
            const response = await originalFetch.apply(this, args);
            
            // Check if this is a login response
            if (url && url.includes('/api/auth/login') && response.ok) {
                console.log('[Force Auth] Login API call successful');
                
                // Clone response to read data
                const cloned = response.clone();
                try {
                    const data = await cloned.json();
                    
                    // Force storage of tokens
                    if (data.access_token) {
                        console.log('[Force Auth] Storing access_token');
                        localStorage.setItem('access_token', data.access_token);
                    }
                    
                    if (data.refresh_token) {
                        console.log('[Force Auth] Storing refresh_token');
                        localStorage.setItem('refresh_token', data.refresh_token);
                    }
                    
                    if (data.user) {
                        console.log('[Force Auth] Storing user data');
                        localStorage.setItem('user_data', JSON.stringify(data.user));
                        localStorage.setItem('user', JSON.stringify(data.user)); // Both formats
                    }
                    
                    // Check for redirect after tokens are stored
                    setTimeout(() => {
                        const redirect = sessionStorage.getItem('redirect_after_stripe') || 
                                       sessionStorage.getItem('stripe_redirect') || 
                                       sessionStorage.getItem('redirect_after_login');
                        
                        if (redirect && redirect !== '/dashboard.html') {
                            console.log('[Force Auth] Redirecting to:', redirect);
                            
                            // Clear session storage
                            sessionStorage.removeItem('redirect_after_stripe');
                            sessionStorage.removeItem('stripe_redirect');
                            sessionStorage.removeItem('redirect_after_login');
                            
                            window.location.href = redirect;
                        }
                    }, 100);
                    
                } catch (e) {
                    console.error('[Force Auth] Error parsing login response:', e);
                }
            }
            
            return response;
        } catch (error) {
            throw error;
        }
    };
    
    // Also monitor form submissions on login page
    if (window.location.pathname.includes('login.html')) {
        document.addEventListener('DOMContentLoaded', () => {
            const loginForm = document.getElementById('loginForm');
            if (loginForm) {
                console.log('[Force Auth] Monitoring login form');
                
                loginForm.addEventListener('submit', (e) => {
                    console.log('[Force Auth] Login form submitted');
                    
                    // Log current redirect info
                    const redirect = sessionStorage.getItem('redirect_after_stripe') || 
                                   sessionStorage.getItem('stripe_redirect') || 
                                   sessionStorage.getItem('redirect_after_login');
                    
                    if (redirect) {
                        console.log('[Force Auth] Will redirect to:', redirect);
                    }
                });
            }
        });
    }
})();