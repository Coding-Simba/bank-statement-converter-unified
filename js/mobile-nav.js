// Mobile Navigation Handler
document.addEventListener('DOMContentLoaded', function() {
    // Create mobile navigation HTML if it doesn't exist
    function initializeMobileNav() {
        const menuToggle = document.getElementById('menuToggle');
        const navMenu = document.querySelector('.nav-menu');
        
        if (!menuToggle || !navMenu) return;
        
        // Create overlay if it doesn't exist
        let overlay = document.querySelector('.mobile-nav-overlay');
        if (!overlay) {
            overlay = document.createElement('div');
            overlay.className = 'mobile-nav-overlay';
            document.body.appendChild(overlay);
        }
        
        // Toggle menu function
        function toggleMenu() {
            const isOpen = navMenu.classList.contains('active');
            
            if (isOpen) {
                closeMenu();
            } else {
                openMenu();
            }
        }
        
        // Open menu
        function openMenu() {
            navMenu.classList.add('active');
            menuToggle.classList.add('active');
            overlay.classList.add('active');
            document.body.style.overflow = 'hidden';
            
            // Animate hamburger to X
            animateHamburger(true);
        }
        
        // Close menu
        function closeMenu() {
            navMenu.classList.remove('active');
            menuToggle.classList.remove('active');
            overlay.classList.remove('active');
            document.body.style.overflow = '';
            
            // Animate X to hamburger
            animateHamburger(false);
        }
        
        // Animate hamburger icon
        function animateHamburger(isOpen) {
            const spans = menuToggle.querySelectorAll('span');
            if (spans.length === 3) {
                if (isOpen) {
                    spans[0].style.transform = 'rotate(45deg) translate(5px, 5px)';
                    spans[1].style.opacity = '0';
                    spans[2].style.transform = 'rotate(-45deg) translate(7px, -6px)';
                } else {
                    spans[0].style.transform = '';
                    spans[1].style.opacity = '';
                    spans[2].style.transform = '';
                }
            }
        }
        
        // Event listeners
        menuToggle.addEventListener('click', function(e) {
            e.stopPropagation();
            toggleMenu();
        });
        
        // Close menu when clicking overlay
        overlay.addEventListener('click', closeMenu);
        
        // Close menu when clicking a link
        const menuLinks = navMenu.querySelectorAll('a');
        menuLinks.forEach(link => {
            link.addEventListener('click', function() {
                // Don't close if it's a dropdown toggle
                if (!this.classList.contains('dropdown-toggle')) {
                    closeMenu();
                }
            });
        });
        
        // Close menu when clicking outside
        document.addEventListener('click', function(event) {
            if (navMenu.classList.contains('active')) {
                const isClickInsideMenu = navMenu.contains(event.target);
                const isClickOnToggle = menuToggle.contains(event.target);
                
                if (!isClickInsideMenu && !isClickOnToggle) {
                    closeMenu();
                }
            }
        });
        
        // Close menu on escape key
        document.addEventListener('keydown', function(event) {
            if (event.key === 'Escape' && navMenu.classList.contains('active')) {
                closeMenu();
            }
        });
        
        // Handle window resize
        let resizeTimer;
        window.addEventListener('resize', function() {
            clearTimeout(resizeTimer);
            resizeTimer = setTimeout(function() {
                if (window.innerWidth > 768 && navMenu.classList.contains('active')) {
                    closeMenu();
                }
            }, 250);
        });
        
        // Prevent scroll when menu is open on iOS
        navMenu.addEventListener('touchmove', function(e) {
            e.preventDefault();
        }, { passive: false });
    }
    
    // Initialize mobile navigation
    initializeMobileNav();
    
    // Reinitialize if navigation is dynamically updated
    window.initializeMobileNav = initializeMobileNav;
});

// Export for use in other scripts
window.MobileNav = {
    close: function() {
        const navMenu = document.querySelector('.nav-menu');
        const menuToggle = document.getElementById('menuToggle');
        const overlay = document.querySelector('.mobile-nav-overlay');
        
        if (navMenu) navMenu.classList.remove('active');
        if (menuToggle) menuToggle.classList.remove('active');
        if (overlay) overlay.classList.remove('active');
        document.body.style.overflow = '';
    }
};