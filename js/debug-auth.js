// Debug Authentication Issues
(function() {
    console.log('[Debug Auth] Starting debug...');
    
    // Log all localStorage operations
    const originalSetItem = localStorage.setItem;
    const originalGetItem = localStorage.getItem;
    const originalRemoveItem = localStorage.removeItem;
    
    localStorage.setItem = function(key, value) {
        console.log('[Debug Auth] localStorage.setItem:', key, value ? value.substring(0, 50) + '...' : 'null');
        return originalSetItem.call(this, key, value);
    };
    
    localStorage.getItem = function(key) {
        const value = originalGetItem.call(this, key);
        if (key.includes('token') || key.includes('user')) {
            console.log('[Debug Auth] localStorage.getItem:', key, value ? 'exists' : 'null');
        }
        return value;
    };
    
    localStorage.removeItem = function(key) {
        console.log('[Debug Auth] localStorage.removeItem:', key);
        return originalRemoveItem.call(this, key);
    };
    
    // Check current auth state
    console.log('[Debug Auth] Current auth state:');
    console.log('  access_token:', localStorage.getItem('access_token') ? 'exists' : 'null');
    console.log('  refresh_token:', localStorage.getItem('refresh_token') ? 'exists' : 'null');
    console.log('  user_data:', localStorage.getItem('user_data') ? 'exists' : 'null');
    console.log('  user:', localStorage.getItem('user') ? 'exists' : 'null');
    
    // Monitor fetch calls
    const originalFetch = window.fetch;
    window.fetch = async function(...args) {
        const [url, options] = args;
        if (url && url.includes('/api/')) {
            console.log('[Debug Auth] Fetch:', url, options?.method || 'GET');
            if (options?.headers?.Authorization) {
                console.log('[Debug Auth] Auth header:', options.headers.Authorization.substring(0, 20) + '...');
            }
        }
        
        try {
            const response = await originalFetch.apply(this, args);
            if (url && url.includes('/api/auth/')) {
                console.log('[Debug Auth] Auth response:', url, response.status);
                
                // Clone response to read body
                const cloned = response.clone();
                try {
                    const data = await cloned.json();
                    console.log('[Debug Auth] Response data keys:', Object.keys(data));
                } catch (e) {
                    // Not JSON
                }
            }
            return response;
        } catch (error) {
            console.error('[Debug Auth] Fetch error:', error);
            throw error;
        }
    };
    
    // Log page navigation
    console.log('[Debug Auth] Current page:', window.location.pathname);
    
    // Monitor page unload
    window.addEventListener('beforeunload', () => {
        console.log('[Debug Auth] Page unloading, auth state:');
        console.log('  access_token:', localStorage.getItem('access_token') ? 'exists' : 'null');
    });
})();