// Auth check fix - Add this to pages that need authentication

(function() {
    // Store original page content
    const originalDisplay = document.body.style.display;
    document.body.style.display = 'none';
    
    // Wait for UnifiedAuth to be ready
    function checkAuthAndProceed() {
        if (!window.UnifiedAuth) {
            // Auth script not loaded yet, wait
            setTimeout(checkAuthAndProceed, 100);
            return;
        }
        
        // Wait for initialization
        if (!window.UnifiedAuth.initialized) {
            setTimeout(checkAuthAndProceed, 100);
            return;
        }
        
        // Check authentication
        if (window.UnifiedAuth.isAuthenticated()) {
            // User is authenticated, show page
            document.body.style.display = originalDisplay;
            console.log('User authenticated, showing page');
            
            // Fire custom event for other scripts
            document.dispatchEvent(new Event('authReady'));
        } else {
            // Not authenticated, redirect to login
            const currentPath = window.location.pathname.replace(/^\//, '');
            window.location.href = '/login.html?redirect=' + encodeURIComponent(currentPath);
        }
    }
    
    // Start checking
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', checkAuthAndProceed);
    } else {
        checkAuthAndProceed();
    }
})();