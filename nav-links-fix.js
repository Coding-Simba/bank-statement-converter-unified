// Fix for navigation links
document.addEventListener('DOMContentLoaded', () => {
    // Ensure all navigation links work properly
    const allLinks = document.querySelectorAll('a[href^="/"]');
    
    allLinks.forEach(link => {
        // Skip if it's already been processed
        if (link.dataset.navFixed) return;
        
        link.dataset.navFixed = 'true';
        
        // Remove any parent event handlers that might interfere
        link.addEventListener('click', (e) => {
            // Stop propagation to prevent parent handlers
            e.stopPropagation();
            
            // For internal links, let them navigate normally
            const href = link.getAttribute('href');
            if (href && !href.startsWith('#')) {
                // Don't prevent default - let the browser navigate
                return true;
            }
        }, true); // Use capture phase to run before other handlers
    });
    
    // Specifically fix pricing links
    document.querySelectorAll('a[href="/pricing.html"]').forEach(link => {
        link.addEventListener('click', (e) => {
            e.stopPropagation();
            window.location.href = '/pricing.html';
        }, true);
    });
});