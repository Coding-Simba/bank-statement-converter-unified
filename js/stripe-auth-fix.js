// Stripe Authentication Fix
// Handles token refresh before making Stripe API calls

(function() {
    console.log('[Stripe Auth Fix] Initializing...');
    
    // Get API base URL
    const API_BASE = (() => {
        const hostname = window.location.hostname;
        if (hostname === 'localhost' || hostname === '127.0.0.1') {
            return 'http://localhost:5000';
        }
        return `${window.location.protocol}//${hostname}`;
    })();
    
    // Check and refresh token if needed
    async function ensureValidToken() {
        const token = localStorage.getItem('access_token');
        const refreshToken = localStorage.getItem('refresh_token');
        
        if (!token || !refreshToken) {
            console.log('[Stripe Auth Fix] No tokens found');
            return false;
        }
        
        // Try to decode token to check expiry (basic check)
        try {
            const payload = JSON.parse(atob(token.split('.')[1]));
            const exp = payload.exp * 1000; // Convert to milliseconds
            const now = Date.now();
            
            // If token expires in less than 5 minutes, refresh it
            if (exp - now < 5 * 60 * 1000) {
                console.log('[Stripe Auth Fix] Token expiring soon, refreshing...');
                return await refreshAccessToken();
            }
            
            return true;
        } catch (e) {
            console.log('[Stripe Auth Fix] Token decode failed, attempting refresh...');
            return await refreshAccessToken();
        }
    }
    
    // Refresh the access token
    async function refreshAccessToken() {
        const refreshToken = localStorage.getItem('refresh_token');
        if (!refreshToken) {
            console.log('[Stripe Auth Fix] No refresh token available');
            return false;
        }
        
        try {
            const response = await fetch(`${API_BASE}/api/auth/refresh`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    refresh_token: refreshToken
                })
            });
            
            if (!response.ok) {
                console.log('[Stripe Auth Fix] Token refresh failed:', response.status);
                // If refresh fails, user needs to login again
                localStorage.clear();
                window.location.href = '/login.html';
                return false;
            }
            
            const data = await response.json();
            console.log('[Stripe Auth Fix] Token refreshed successfully');
            
            // Update tokens
            localStorage.setItem('access_token', data.access_token);
            if (data.refresh_token) {
                localStorage.setItem('refresh_token', data.refresh_token);
            }
            
            return true;
        } catch (error) {
            console.error('[Stripe Auth Fix] Refresh error:', error);
            return false;
        }
    }
    
    // Override fetch to ensure valid token
    const originalFetch = window.fetch;
    window.fetch = async function(...args) {
        const [url, options = {}] = args;
        
        // Only intercept Stripe API calls
        if (typeof url === 'string' && url.includes('/api/stripe/')) {
            console.log('[Stripe Auth Fix] Intercepting Stripe API call:', url);
            
            // Ensure we have a valid token
            const hasValidToken = await ensureValidToken();
            if (!hasValidToken) {
                console.log('[Stripe Auth Fix] No valid token, redirecting to login...');
                window.location.href = '/login.html';
                throw new Error('Authentication required');
            }
            
            // Update authorization header with fresh token
            const token = localStorage.getItem('access_token');
            options.headers = {
                ...options.headers,
                'Authorization': `Bearer ${token}`
            };
        }
        
        return originalFetch.apply(this, [url, options]);
    };
    
    // Also check token validity on page load
    document.addEventListener('DOMContentLoaded', async () => {
        if (window.location.pathname.includes('pricing.html')) {
            console.log('[Stripe Auth Fix] Checking token validity on pricing page...');
            await ensureValidToken();
        }
    });
})();