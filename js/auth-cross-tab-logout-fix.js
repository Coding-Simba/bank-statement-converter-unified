/**
 * Cross-Tab Logout Fix for Unified Authentication System
 * 
 * This file contains improvements to handle logout across multiple tabs properly.
 * It adds proper cross-tab communication and synchronization.
 */

(function() {
    'use strict';
    
    // Check if UnifiedAuth exists
    if (!window.UnifiedAuth) {
        console.error('[CrossTabLogout] UnifiedAuth not found. Load auth-unified.js first.');
        return;
    }
    
    // Store original logout function
    const originalLogout = window.UnifiedAuth.logout.bind(window.UnifiedAuth);
    
    // Enhanced logout function with cross-tab support
    window.UnifiedAuth.logout = async function(skipRedirect = false) {
        console.log('[CrossTabLogout] Initiating logout...');
        
        try {
            // 1. Call the backend logout API
            await fetch(`${this.API_BASE || window.location.protocol + '//' + window.location.hostname}/v2/api/auth/logout`, {
                method: 'POST',
                credentials: 'include',
                headers: {
                    'X-CSRF-Token': this.csrfToken
                }
            });
            console.log('[CrossTabLogout] Backend logout successful');
        } catch (error) {
            console.error('[CrossTabLogout] Backend logout error:', error);
        }
        
        // 2. Clear local state
        this.user = null;
        this.clearTokenRefresh();
        
        // 3. Broadcast logout to other tabs BEFORE clearing localStorage
        broadcastLogout();
        
        // 4. Clear localStorage (this will trigger storage events in other tabs)
        localStorage.removeItem('user');
        localStorage.removeItem('user_data');
        
        // 5. Update UI
        this.updateUI();
        
        // 6. Optional redirect (can be skipped for cross-tab scenarios)
        if (!skipRedirect) {
            // Small delay to ensure other tabs receive the message
            setTimeout(() => {
                window.location.href = '/';
            }, 100);
        }
        
        console.log('[CrossTabLogout] Logout complete');
    };
    
    // Broadcast logout message to other tabs
    function broadcastLogout() {
        console.log('[CrossTabLogout] Broadcasting logout to other tabs...');
        
        // Method 1: BroadcastChannel (modern browsers)
        if (typeof BroadcastChannel !== 'undefined') {
            try {
                const channel = new BroadcastChannel('auth-channel');
                channel.postMessage({
                    type: 'LOGOUT',
                    timestamp: Date.now()
                });
                channel.close();
                console.log('[CrossTabLogout] Broadcast via BroadcastChannel sent');
            } catch (error) {
                console.error('[CrossTabLogout] BroadcastChannel error:', error);
            }
        }
        
        // Method 2: localStorage event (fallback for older browsers)
        try {
            // Set a temporary logout signal
            localStorage.setItem('logout-signal', Date.now().toString());
            // Remove it immediately to trigger storage event
            setTimeout(() => {
                localStorage.removeItem('logout-signal');
            }, 50);
            console.log('[CrossTabLogout] localStorage signal sent');
        } catch (error) {
            console.error('[CrossTabLogout] localStorage signal error:', error);
        }
        
        // Method 3: Custom event for same-tab components
        try {
            window.dispatchEvent(new CustomEvent('authLogout', {
                detail: { timestamp: Date.now() }
            }));
            console.log('[CrossTabLogout] Custom event dispatched');
        } catch (error) {
            console.error('[CrossTabLogout] Custom event error:', error);
        }
    }
    
    // Listen for logout messages from other tabs
    function setupCrossTabLogoutListeners() {
        console.log('[CrossTabLogout] Setting up cross-tab listeners...');
        
        // Method 1: BroadcastChannel listener
        if (typeof BroadcastChannel !== 'undefined') {
            try {
                const channel = new BroadcastChannel('auth-channel');
                channel.addEventListener('message', (event) => {
                    if (event.data.type === 'LOGOUT') {
                        console.log('[CrossTabLogout] Received logout broadcast from another tab');
                        handleCrossTabLogout();
                    }
                });
            } catch (error) {
                console.error('[CrossTabLogout] BroadcastChannel listener error:', error);
            }
        }
        
        // Method 2: Storage event listener
        window.addEventListener('storage', (event) => {
            // User data removed
            if (event.key === 'user' && event.oldValue && !event.newValue) {
                console.log('[CrossTabLogout] Detected user data removal in another tab');
                handleCrossTabLogout();
            }
            
            // Logout signal
            if (event.key === 'logout-signal') {
                console.log('[CrossTabLogout] Received logout signal from another tab');
                handleCrossTabLogout();
            }
        });
        
        // Method 3: Listen for auth state changes
        window.addEventListener('authStateChanged', (event) => {
            if (!event.detail.authenticated && window.UnifiedAuth.user) {
                console.log('[CrossTabLogout] Auth state changed to unauthenticated');
                // This might be from another tab's logout
            }
        });
        
        console.log('[CrossTabLogout] Cross-tab listeners setup complete');
    }
    
    // Handle logout initiated from another tab
    function handleCrossTabLogout() {
        console.log('[CrossTabLogout] Processing cross-tab logout...');
        
        // Clear local auth state without calling API (already called by initiating tab)
        if (window.UnifiedAuth.user) {
            window.UnifiedAuth.user = null;
            window.UnifiedAuth.clearTokenRefresh();
            
            // Clear localStorage if not already cleared
            if (localStorage.getItem('user')) {
                localStorage.removeItem('user');
            }
            if (localStorage.getItem('user_data')) {
                localStorage.removeItem('user_data');
            }
            
            // Update UI
            window.UnifiedAuth.updateUI();
            
            // Show notification to user
            showLogoutNotification();
            
            // Redirect if on a protected page
            if (isProtectedPage()) {
                setTimeout(() => {
                    window.location.href = '/?redirect=' + encodeURIComponent(window.location.pathname);
                }, 2000); // Give user time to see the notification
            }
        }
    }
    
    // Check if current page requires authentication
    function isProtectedPage() {
        const protectedPaths = [
            '/dashboard',
            '/settings',
            '/profile',
            '/account'
        ];
        
        const currentPath = window.location.pathname.toLowerCase();
        return protectedPaths.some(path => currentPath.includes(path));
    }
    
    // Show logout notification to user
    function showLogoutNotification() {
        console.log('[CrossTabLogout] Showing logout notification...');
        
        // Create notification element
        const notification = document.createElement('div');
        notification.innerHTML = `
            <div style="
                position: fixed;
                top: 20px;
                right: 20px;
                background: #dc3545;
                color: white;
                padding: 15px 20px;
                border-radius: 5px;
                box-shadow: 0 4px 12px rgba(0,0,0,0.3);
                z-index: 10000;
                font-family: Arial, sans-serif;
                font-size: 14px;
                max-width: 300px;
            ">
                <strong>🚪 Logged Out</strong><br>
                You have been logged out from another tab.
                <div style="margin-top: 10px; font-size: 12px; opacity: 0.9;">
                    Redirecting to login page...
                </div>
            </div>
        `;
        
        document.body.appendChild(notification);
        
        // Auto-remove notification
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 5000);
    }
    
    // Enhanced auth check that considers cross-tab state
    const originalCheckAuth = window.UnifiedAuth.checkAuth.bind(window.UnifiedAuth);
    window.UnifiedAuth.checkAuth = async function() {
        // Check localStorage first for cross-tab sync
        const cachedUser = localStorage.getItem('user');
        if (!cachedUser && this.user) {
            // User data was cleared in another tab
            console.log('[CrossTabLogout] Detected logout from localStorage check');
            this.user = null;
            this.updateUI();
            return;
        }
        
        // Proceed with normal auth check
        return await originalCheckAuth();
    };
    
    // Initialize cross-tab logout system
    function initializeCrossTabLogout() {
        console.log('[CrossTabLogout] Initializing cross-tab logout system...');
        
        // Setup listeners
        setupCrossTabLogoutListeners();
        
        // Add periodic sync check (fallback)
        setInterval(() => {
            const cachedUser = localStorage.getItem('user');
            if (!cachedUser && window.UnifiedAuth.user) {
                console.log('[CrossTabLogout] Periodic sync detected logout');
                handleCrossTabLogout();
            }
        }, 5000); // Check every 5 seconds
        
        console.log('[CrossTabLogout] Cross-tab logout system initialized');
    }
    
    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initializeCrossTabLogout);
    } else {
        initializeCrossTabLogout();
    }
    
    // Expose utility functions for testing
    window.CrossTabLogout = {
        broadcastLogout,
        handleCrossTabLogout,
        showLogoutNotification,
        isProtectedPage
    };
    
    console.log('[CrossTabLogout] Cross-tab logout enhancement loaded');
    
})();