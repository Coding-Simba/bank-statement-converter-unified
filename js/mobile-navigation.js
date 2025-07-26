// Mobile Navigation JavaScript

(function() {
    'use strict';
    
    // Configuration
    const config = {
        menuWidth: 300,
        animationDuration: 300,
        breakpoint: 768,
        swipeThreshold: 50,
        edgeSwipeArea: 20
    };
    
    // State
    let isMenuOpen = false;
    let touchStartX = 0;
    let touchEndX = 0;
    let isAnimating = false;
    let scrollPosition = 0;
    
    // Initialize mobile navigation
    function initMobileNav() {
        // Create mobile menu elements if they don't exist
        if (!document.querySelector('.mobile-menu-toggle')) {
            createMobileMenuElements();
        }
        
        // Set up event listeners
        setupEventListeners();
        
        // Set up swipe gestures
        setupSwipeGestures();
        
        // Handle window resize
        handleResize();
        
        // Mark current page as active
        markCurrentPage();
        
        // Initialize ARIA attributes
        initializeAccessibility();
    }
    
    // Create mobile menu HTML structure
    function createMobileMenuElements() {
        // Create hamburger button
        const toggleButton = document.createElement('button');
        toggleButton.className = 'mobile-menu-toggle';
        toggleButton.setAttribute('aria-label', 'Toggle mobile menu');
        toggleButton.setAttribute('aria-expanded', 'false');
        toggleButton.setAttribute('aria-controls', 'mobile-menu');
        toggleButton.innerHTML = `
            <span class="hamburger-line"></span>
            <span class="hamburger-line"></span>
            <span class="hamburger-line"></span>
        `;
        
        // Create overlay
        const overlay = document.createElement('div');
        overlay.className = 'mobile-menu-overlay';
        
        // Create mobile menu
        const mobileMenu = document.createElement('div');
        mobileMenu.className = 'mobile-menu';
        mobileMenu.id = 'mobile-menu';
        mobileMenu.setAttribute('role', 'navigation');
        mobileMenu.setAttribute('aria-label', 'Mobile navigation');
        mobileMenu.setAttribute('aria-hidden', 'true');
        
        // Build menu content
        mobileMenu.innerHTML = `
            <div class="mobile-menu-header">
                <a href="/" class="mobile-logo">
                    <i class="fas fa-file-invoice"></i>
                    <span>BankCSVConverter</span>
                </a>
                <button class="mobile-menu-close" aria-label="Close menu">
                    <i class="fas fa-times"></i>
                </button>
            </div>
            <nav class="mobile-nav">
                <a href="/" class="mobile-nav-item">
                    <i class="fas fa-home"></i>
                    <span>Home</span>
                </a>
                <a href="/features.html" class="mobile-nav-item">
                    <i class="fas fa-star"></i>
                    <span>Features</span>
                </a>
                <a href="/how-it-works.html" class="mobile-nav-item">
                    <i class="fas fa-cogs"></i>
                    <span>How It Works</span>
                </a>
                <a href="/pricing.html" class="mobile-nav-item">
                    <i class="fas fa-tag"></i>
                    <span>Pricing</span>
                </a>
                
                <div class="mobile-nav-separator"></div>
                
                <div class="mobile-nav-section">Resources</div>
                <a href="/blog.html" class="mobile-nav-item">
                    <i class="fas fa-blog"></i>
                    <span>Blog</span>
                </a>
                <a href="/help.html" class="mobile-nav-item">
                    <i class="fas fa-question-circle"></i>
                    <span>Help Center</span>
                </a>
                
                <div class="mobile-nav-separator"></div>
                
                <div class="mobile-nav-section">Company</div>
                <a href="/about.html" class="mobile-nav-item">
                    <i class="fas fa-info-circle"></i>
                    <span>About</span>
                </a>
                <a href="/contact.html" class="mobile-nav-item">
                    <i class="fas fa-envelope"></i>
                    <span>Contact</span>
                </a>
                <a href="/careers.html" class="mobile-nav-item">
                    <i class="fas fa-briefcase"></i>
                    <span>Careers</span>
                </a>
                
                <div class="mobile-nav-separator"></div>
                
                <div class="mobile-nav-section">Legal</div>
                <a href="/privacy.html" class="mobile-nav-item">
                    <i class="fas fa-shield-alt"></i>
                    <span>Privacy Policy</span>
                </a>
                <a href="/terms.html" class="mobile-nav-item">
                    <i class="fas fa-file-contract"></i>
                    <span>Terms of Service</span>
                </a>
                <a href="/pages/security.html" class="mobile-nav-item">
                    <i class="fas fa-lock"></i>
                    <span>Security</span>
                </a>
            </nav>
            <div class="mobile-menu-cta">
                <a href="/dashboard.html" class="mobile-cta-btn primary">
                    <i class="fas fa-sign-in-alt"></i>
                    <span>Sign In</span>
                </a>
                <a href="/pricing.html" class="mobile-cta-btn secondary">
                    <i class="fas fa-rocket"></i>
                    <span>Get Started</span>
                </a>
            </div>
        `;
        
        // Insert toggle button in the navbar
        const navbar = document.querySelector('.navbar, nav, header');
        if (navbar) {
            navbar.appendChild(toggleButton);
        } else {
            document.body.appendChild(toggleButton);
        }
        
        // Append overlay and menu to body
        document.body.appendChild(overlay);
        document.body.appendChild(mobileMenu);
    }
    
    // Set up event listeners
    function setupEventListeners() {
        const toggleButton = document.querySelector('.mobile-menu-toggle');
        const overlay = document.querySelector('.mobile-menu-overlay');
        const mobileMenu = document.querySelector('.mobile-menu');
        const closeButton = document.querySelector('.mobile-menu-close');
        const menuLinks = document.querySelectorAll('.mobile-nav-item');
        
        // Toggle button click
        if (toggleButton) {
            toggleButton.addEventListener('click', (e) => {
                e.stopPropagation();
                toggleMenu();
            });
        }
        
        // Close button click
        if (closeButton) {
            closeButton.addEventListener('click', (e) => {
                e.stopPropagation();
                closeMenu();
            });
        }
        
        // Overlay click
        if (overlay) {
            overlay.addEventListener('click', closeMenu);
        }
        
        // Menu link clicks
        menuLinks.forEach(link => {
            link.addEventListener('click', (e) => {
                // Close menu after clicking a link
                // Unless it has a submenu
                if (!link.classList.contains('has-submenu')) {
                    // Small delay for smooth transition
                    setTimeout(() => closeMenu(), 100);
                } else {
                    e.preventDefault();
                    toggleSubmenu(link);
                }
            });
        });
        
        // Escape key to close menu
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && isMenuOpen) {
                closeMenu();
            }
        });
        
        // Prevent body scroll when menu is open
        document.addEventListener('touchmove', (e) => {
            if (isMenuOpen && !mobileMenu.contains(e.target)) {
                e.preventDefault();
            }
        }, { passive: false });
    }
    
    // Set up swipe gestures
    function setupSwipeGestures() {
        const mobileMenu = document.querySelector('.mobile-menu');
        
        if (!mobileMenu) return;
        
        // Touch events for swipe
        mobileMenu.addEventListener('touchstart', handleTouchStart, { passive: true });
        mobileMenu.addEventListener('touchmove', handleTouchMove, { passive: true });
        mobileMenu.addEventListener('touchend', handleTouchEnd);
        
        // Edge swipe to open
        document.addEventListener('touchstart', (e) => {
            if (e.touches[0].clientX > window.innerWidth - 20 && !isMenuOpen) {
                touchStartX = e.touches[0].clientX;
            }
        }, { passive: true });
        
        document.addEventListener('touchmove', (e) => {
            if (touchStartX > window.innerWidth - 20 && !isMenuOpen) {
                const touchX = e.touches[0].clientX;
                if (touchStartX - touchX > 50) {
                    openMenu();
                    touchStartX = 0;
                }
            }
        }, { passive: true });
    }
    
    // Touch event handlers
    function handleTouchStart(e) {
        touchStartX = e.touches[0].clientX;
    }
    
    function handleTouchMove(e) {
        if (!isMenuOpen) return;
        
        const touchX = e.touches[0].clientX;
        const diffX = touchX - touchStartX;
        
        // Only allow swiping right (to close)
        if (diffX > 0) {
            const menu = document.querySelector('.mobile-menu');
            const translateX = Math.min(diffX, config.menuWidth);
            menu.style.transform = `translateX(${translateX - config.menuWidth}px)`;
        }
    }
    
    function handleTouchEnd(e) {
        if (!isMenuOpen) return;
        
        const menu = document.querySelector('.mobile-menu');
        touchEndX = e.changedTouches[0].clientX;
        const diffX = touchEndX - touchStartX;
        
        // If swiped more than 50px, close menu
        if (diffX > 50) {
            closeMenu();
        } else {
            // Reset position
            menu.style.transform = `translateX(-${config.menuWidth}px)`;
        }
    }
    
    // Toggle menu open/close
    function toggleMenu() {
        if (isMenuOpen) {
            closeMenu();
        } else {
            openMenu();
        }
    }
    
    // Open menu
    function openMenu() {
        if (isAnimating || isMenuOpen) return;
        
        const toggleButton = document.querySelector('.mobile-menu-toggle');
        const overlay = document.querySelector('.mobile-menu-overlay');
        const mobileMenu = document.querySelector('.mobile-menu');
        
        isAnimating = true;
        isMenuOpen = true;
        
        // Save scroll position
        scrollPosition = window.pageYOffset;
        
        // Update ARIA
        toggleButton.setAttribute('aria-expanded', 'true');
        mobileMenu.setAttribute('aria-hidden', 'false');
        
        // Add classes
        requestAnimationFrame(() => {
            toggleButton.classList.add('active');
            overlay.classList.add('active');
            mobileMenu.classList.add('active');
            document.body.classList.add('mobile-menu-open');
            
            // Lock body scroll
            document.body.style.position = 'fixed';
            document.body.style.top = `-${scrollPosition}px`;
            document.body.style.width = '100%';
            
            // Focus management
            setTimeout(() => {
                const firstLink = mobileMenu.querySelector('.mobile-nav-item');
                if (firstLink) firstLink.focus();
                isAnimating = false;
            }, config.animationDuration);
        });
        
        // Trap focus within menu
        trapFocus(mobileMenu);
        
        // Announce to screen readers
        announceToScreenReader('Mobile menu opened');
    }
    
    // Close menu
    function closeMenu() {
        if (isAnimating || !isMenuOpen) return;
        
        const toggleButton = document.querySelector('.mobile-menu-toggle');
        const overlay = document.querySelector('.mobile-menu-overlay');
        const mobileMenu = document.querySelector('.mobile-menu');
        
        isAnimating = true;
        isMenuOpen = false;
        
        // Update ARIA
        toggleButton.setAttribute('aria-expanded', 'false');
        mobileMenu.setAttribute('aria-hidden', 'true');
        
        // Remove classes
        toggleButton.classList.remove('active');
        overlay.classList.remove('active');
        mobileMenu.classList.remove('active');
        
        // Restore body scroll
        document.body.style.position = '';
        document.body.style.top = '';
        document.body.style.width = '';
        window.scrollTo(0, scrollPosition);
        
        // Reset transform
        mobileMenu.style.transform = '';
        
        // Remove body class after animation
        setTimeout(() => {
            document.body.classList.remove('mobile-menu-open');
            isAnimating = false;
            
            // Return focus to toggle button
            toggleButton.focus();
        }, config.animationDuration);
        
        // Announce to screen readers
        announceToScreenReader('Mobile menu closed');
    }
    
    // Toggle submenu
    function toggleSubmenu(link) {
        const submenu = link.nextElementSibling;
        if (submenu && submenu.classList.contains('mobile-nav-submenu')) {
            link.classList.toggle('expanded');
            submenu.classList.toggle('active');
        }
    }
    
    // Mark current page as active
    function markCurrentPage() {
        const currentPath = window.location.pathname.toLowerCase();
        const menuLinks = document.querySelectorAll('.mobile-nav-item');
        
        menuLinks.forEach(link => {
            if (!link.href) return;
            
            const linkPath = new URL(link.href).pathname.toLowerCase();
            
            // Check for exact match or index variations
            if (linkPath === currentPath || 
                (currentPath === '/' && linkPath === '/index.html') ||
                (currentPath === '/index.html' && linkPath === '/') ||
                (currentPath.endsWith('/') && linkPath === currentPath.slice(0, -1)) ||
                (linkPath.endsWith('/') && currentPath === linkPath.slice(0, -1))) {
                link.classList.add('active');
                link.setAttribute('aria-current', 'page');
            }
        });
    }
    
    // Handle window resize
    function handleResize() {
        let resizeTimer;
        
        window.addEventListener('resize', () => {
            clearTimeout(resizeTimer);
            resizeTimer = setTimeout(() => {
                if (window.innerWidth > config.breakpoint && isMenuOpen) {
                    closeMenu();
                }
            }, 250);
        });
    }
    
    // Focus trap for accessibility
    function trapFocus(element) {
        const focusableElements = element.querySelectorAll(
            'a[href], button, textarea, input[type="text"], input[type="radio"], input[type="checkbox"], select'
        );
        const firstFocusableElement = focusableElements[0];
        const lastFocusableElement = focusableElements[focusableElements.length - 1];
        
        element.addEventListener('keydown', (e) => {
            if (e.key === 'Tab') {
                if (e.shiftKey) { // Shift + Tab
                    if (document.activeElement === firstFocusableElement) {
                        lastFocusableElement.focus();
                        e.preventDefault();
                    }
                } else { // Tab
                    if (document.activeElement === lastFocusableElement) {
                        firstFocusableElement.focus();
                        e.preventDefault();
                    }
                }
            }
        });
    }
    
    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initMobileNav);
    } else {
        initMobileNav();
    }
    
    // Initialize accessibility features
    function initializeAccessibility() {
        // Create screen reader announcement element
        const announcer = document.createElement('div');
        announcer.className = 'sr-only';
        announcer.setAttribute('aria-live', 'polite');
        announcer.setAttribute('aria-atomic', 'true');
        document.body.appendChild(announcer);
    }
    
    // Announce to screen readers
    function announceToScreenReader(message) {
        const announcer = document.querySelector('.sr-only[aria-live]');
        if (announcer) {
            announcer.textContent = message;
            // Clear after announcement
            setTimeout(() => {
                announcer.textContent = '';
            }, 1000);
        }
    }
    
    // Export for use in other scripts
    window.mobileNav = {
        open: openMenu,
        close: closeMenu,
        toggle: toggleMenu,
        isOpen: () => isMenuOpen
    };
})();