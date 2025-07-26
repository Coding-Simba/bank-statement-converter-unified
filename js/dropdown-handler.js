// Improved Dropdown Handler with better hover management

(function() {
    'use strict';

    // Initialize dropdown functionality
    function initDropdowns() {
        const dropdowns = document.querySelectorAll('.dropdown');
        
        dropdowns.forEach(dropdown => {
            const toggle = dropdown.querySelector('.dropdown-toggle');
            const menu = dropdown.querySelector('.dropdown-menu');
            let hoverTimeout;
            let isOpen = false;

            if (!toggle || !menu) return;

            // For desktop - improved hover handling
            if (window.innerWidth > 768) {
                // Mouse enter on dropdown container
                dropdown.addEventListener('mouseenter', function() {
                    clearTimeout(hoverTimeout);
                    openDropdown();
                });

                // Mouse leave from dropdown container
                dropdown.addEventListener('mouseleave', function() {
                    // Add delay before closing to allow cursor to move to menu
                    hoverTimeout = setTimeout(() => {
                        closeDropdown();
                    }, 100); // 100ms delay gives time to move cursor
                });

                // Keep menu open when hovering over it
                menu.addEventListener('mouseenter', function() {
                    clearTimeout(hoverTimeout);
                });

                menu.addEventListener('mouseleave', function() {
                    // Check if cursor is still over the dropdown button
                    hoverTimeout = setTimeout(() => {
                        if (!dropdown.matches(':hover')) {
                            closeDropdown();
                        }
                    }, 100);
                });
            }

            // Click handling for mobile and accessibility
            toggle.addEventListener('click', function(e) {
                e.preventDefault();
                e.stopPropagation();
                
                if (isOpen) {
                    closeDropdown();
                } else {
                    closeAllDropdowns();
                    openDropdown();
                }
            });

            // Click on menu items
            menu.addEventListener('click', function(e) {
                if (e.target.classList.contains('dropdown-item')) {
                    closeDropdown();
                }
            });

            function openDropdown() {
                dropdown.classList.add('is-open');
                isOpen = true;
                toggle.setAttribute('aria-expanded', 'true');
            }

            function closeDropdown() {
                dropdown.classList.remove('is-open');
                isOpen = false;
                toggle.setAttribute('aria-expanded', 'false');
            }
        });

        // Close dropdowns when clicking outside
        document.addEventListener('click', function(e) {
            if (!e.target.closest('.dropdown')) {
                closeAllDropdowns();
            }
        });

        // Close dropdowns on escape key
        document.addEventListener('keydown', function(e) {
            if (e.key === 'Escape') {
                closeAllDropdowns();
            }
        });
    }

    function closeAllDropdowns() {
        document.querySelectorAll('.dropdown.is-open').forEach(dropdown => {
            dropdown.classList.remove('is-open');
            dropdown.querySelector('.dropdown-toggle').setAttribute('aria-expanded', 'false');
        });
    }

    // Alternative: Pure CSS solution with JavaScript enhancement
    function enhanceDropdownWithBridge() {
        const dropdowns = document.querySelectorAll('.dropdown');
        
        dropdowns.forEach(dropdown => {
            const menu = dropdown.querySelector('.dropdown-menu');
            if (!menu) return;

            // Create invisible bridge element
            const bridge = document.createElement('div');
            bridge.className = 'dropdown-bridge';
            bridge.style.cssText = `
                position: absolute;
                top: 100%;
                left: 0;
                right: 0;
                height: 20px;
                background: transparent;
                pointer-events: none;
            `;
            
            dropdown.appendChild(bridge);
        });
    }

    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function() {
            initDropdowns();
            enhanceDropdownWithBridge();
        });
    } else {
        initDropdowns();
        enhanceDropdownWithBridge();
    }

    // Reinitialize on window resize
    let resizeTimeout;
    window.addEventListener('resize', function() {
        clearTimeout(resizeTimeout);
        resizeTimeout = setTimeout(function() {
            initDropdowns();
        }, 250);
    });

})();