// Final Login Override - Aggressive redirect handling
(function() {
    console.log('[Login Override Final] Loading...');
    
    // Only run on login page
    if (!window.location.pathname.includes('login.html')) {
        return;
    }
    
    // Check for saved redirect immediately
    const savedRedirect = sessionStorage.getItem('redirect_after_stripe') || 
                         sessionStorage.getItem('stripe_redirect') || 
                         sessionStorage.getItem('redirect_after_login');
    
    if (savedRedirect) {
        console.log('[Login Override Final] Target redirect:', savedRedirect);
        
        // Method 1: Override XMLHttpRequest to catch login success
        const originalXHR = window.XMLHttpRequest;
        window.XMLHttpRequest = function() {
            const xhr = new originalXHR();
            const originalOpen = xhr.open;
            const originalSend = xhr.send;
            
            xhr.open = function(method, url, ...rest) {
                if (url && url.includes('/api/auth/login')) {
                    console.log('[Login Override Final] Intercepting login request');
                    
                    // Add response listener
                    xhr.addEventListener('load', function() {
                        if (this.status === 200) {
                            console.log('[Login Override Final] Login successful!');
                            
                            try {
                                const response = JSON.parse(this.responseText);
                                if (response.access_token) {
                                    console.log('[Login Override Final] Tokens received, redirecting in 100ms...');
                                    
                                    // Clear session storage
                                    sessionStorage.removeItem('redirect_after_stripe');
                                    sessionStorage.removeItem('stripe_redirect');
                                    sessionStorage.removeItem('redirect_after_login');
                                    
                                    // Force redirect
                                    setTimeout(() => {
                                        window.location.href = savedRedirect;
                                    }, 100);
                                }
                            } catch (e) {
                                console.error('[Login Override Final] Parse error:', e);
                            }
                        }
                    });
                }
                
                return originalOpen.apply(this, [method, url, ...rest]);
            };
            
            return xhr;
        };
        
        // Method 2: Override fetch as well
        const originalFetch = window.fetch;
        window.fetch = async function(...args) {
            const [url, options] = args;
            
            if (url && url.includes('/api/auth/login')) {
                console.log('[Login Override Final] Intercepting login fetch');
                
                try {
                    const response = await originalFetch.apply(this, args);
                    
                    if (response.ok) {
                        const cloned = response.clone();
                        const data = await cloned.json();
                        
                        if (data.access_token) {
                            console.log('[Login Override Final] Login successful via fetch!');
                            
                            // Clear session storage
                            sessionStorage.removeItem('redirect_after_stripe');
                            sessionStorage.removeItem('stripe_redirect');
                            sessionStorage.removeItem('redirect_after_login');
                            
                            // Force redirect
                            setTimeout(() => {
                                window.location.href = savedRedirect;
                            }, 100);
                        }
                    }
                    
                    return response;
                } catch (error) {
                    throw error;
                }
            }
            
            return originalFetch.apply(this, args);
        };
        
        // Method 3: Monitor form submission directly
        document.addEventListener('DOMContentLoaded', () => {
            const loginForm = document.querySelector('#loginForm, form[action*="login"]');
            if (loginForm) {
                console.log('[Login Override Final] Found login form');
                
                loginForm.addEventListener('submit', (e) => {
                    console.log('[Login Override Final] Form submitted, will redirect to:', savedRedirect);
                });
            }
        });
        
        // Method 4: Aggressive localStorage monitoring
        let checkCount = 0;
        const checkInterval = setInterval(() => {
            if (localStorage.getItem('access_token')) {
                console.log('[Login Override Final] Token detected! Redirecting immediately...');
                clearInterval(checkInterval);
                
                // Clear session storage
                sessionStorage.removeItem('redirect_after_stripe');
                sessionStorage.removeItem('stripe_redirect');
                sessionStorage.removeItem('redirect_after_login');
                sessionStorage.removeItem('stripe_plan');
                
                // Force immediate redirect
                window.location.href = savedRedirect;
            }
            
            checkCount++;
            if (checkCount > 100) { // 10 seconds
                clearInterval(checkInterval);
            }
        }, 100);
    }
})();