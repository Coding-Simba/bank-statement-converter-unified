/**
 * Bulletproof Standalone Pricing Toggle Implementation
 * 
 * This script is designed to work independently of any other scripts or CSS.
 * It uses:
 * - Unique CSS class names with "v2" suffix to avoid conflicts
 * - Inline styles applied via JavaScript to bypass CSS conflicts
 * - Event capturing to prevent interference from other event handlers
 * - Defensive programming with extensive error checking
 * - Comprehensive logging for debugging
 * 
 * Created: 2025-08-01
 */

(function() {
    'use strict';
    
    // Unique namespace to avoid conflicts
    const NAMESPACE = 'PricingToggleV2_' + Date.now();
    
    // Configuration
    const CONFIG = {
        toggleId: 'pricingToggle',
        monthlyLabelId: 'monthlyLabel', 
        yearlyLabelId: 'yearlyLabel',
        priceValueSelector: '.price-value',
        annualPriceSelector: '.annual-price',
        debugMode: true
    };
    
    // Enhanced logging
    function log(level, message, data = null) {
        if (!CONFIG.debugMode && level === 'debug') return;
        
        const timestamp = new Date().toISOString();
        const prefix = `[${NAMESPACE}][${level.toUpperCase()}][${timestamp}]`;
        
        if (data) {
            console[level](prefix, message, data);
        } else {
            console[level](prefix, message);
        }
    }
    
    // State management
    const state = {
        isYearly: false,
        elements: {},
        initialized: false,
        eventListenersAttached: false
    };
    
    // Defensive element finder with retries
    function findElement(selector, maxRetries = 5, retryDelay = 100) {
        return new Promise((resolve, reject) => {
            let retries = 0;
            
            function attempt() {
                const element = document.getElementById ? document.getElementById(selector) : document.querySelector('#' + selector);
                
                if (element) {
                    log('debug', `Found element: ${selector}`, element);
                    resolve(element);
                    return;
                }
                
                retries++;
                if (retries >= maxRetries) {
                    log('error', `Failed to find element after ${maxRetries} retries: ${selector}`);
                    reject(new Error(`Element not found: ${selector}`));
                    return;
                }
                
                log('debug', `Element not found, retrying (${retries}/${maxRetries}): ${selector}`);
                setTimeout(attempt, retryDelay);
            }
            
            attempt();
        });
    }
    
    // Apply bulletproof inline styles
    function applyInlineStyles() {
        log('info', 'Applying bulletproof inline styles...');
        
        try {
            // Toggle switch styles
            if (state.elements.toggle) {
                const toggle = state.elements.toggle;
                Object.assign(toggle.style, {
                    position: 'relative',
                    width: '56px',
                    height: '32px',
                    backgroundColor: '#e5e7eb',
                    borderRadius: '32px',
                    cursor: 'pointer',
                    transition: 'background-color 0.3s ease',
                    display: 'inline-block',
                    verticalAlign: 'middle',
                    border: 'none',
                    outline: 'none',
                    boxSizing: 'border-box'
                });
                
                // Add active state class with unique name
                toggle.classList.add('pricing-toggle-v2-switch');
            }
            
            // Toggle slider styles
            if (state.elements.slider) {
                const slider = state.elements.slider;
                Object.assign(slider.style, {
                    position: 'absolute',
                    top: '4px',
                    left: '4px',
                    width: '24px',
                    height: '24px',
                    backgroundColor: 'white',
                    borderRadius: '50%',
                    transition: 'transform 0.3s ease',
                    boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
                    pointerEvents: 'none',
                    boxSizing: 'border-box'
                });
                
                slider.classList.add('pricing-toggle-v2-slider');
            }
            
            // Label styles
            [state.elements.monthlyLabel, state.elements.yearlyLabel].forEach(label => {
                if (label) {
                    Object.assign(label.style, {
                        fontSize: '1.6rem',
                        color: '#6b7280',
                        fontWeight: '500',
                        cursor: 'pointer',
                        transition: 'color 0.2s ease',
                        userSelect: 'none',
                        display: 'inline-block',
                        verticalAlign: 'middle'
                    });
                    
                    label.classList.add('pricing-toggle-v2-label');
                }
            });
            
            log('info', 'Inline styles applied successfully');
        } catch (error) {
            log('error', 'Failed to apply inline styles:', error);
        }
    }
    
    // Update visual state with inline styles
    function updateVisualState(isYearly) {
        log('info', `Updating visual state to: ${isYearly ? 'yearly' : 'monthly'}`);
        
        try {
            // Update toggle switch
            if (state.elements.toggle) {
                if (isYearly) {
                    state.elements.toggle.style.backgroundColor = '#0066ff';
                    state.elements.toggle.classList.add('pricing-toggle-v2-active');
                } else {
                    state.elements.toggle.style.backgroundColor = '#e5e7eb';
                    state.elements.toggle.classList.remove('pricing-toggle-v2-active');
                }
            }
            
            // Update slider position
            if (state.elements.slider) {
                if (isYearly) {
                    state.elements.slider.style.transform = 'translateX(24px)';
                } else {
                    state.elements.slider.style.transform = 'translateX(0px)';
                }
            }
            
            // Update labels
            if (state.elements.monthlyLabel) {
                if (isYearly) {
                    state.elements.monthlyLabel.style.color = '#6b7280';
                    state.elements.monthlyLabel.style.fontWeight = '500';
                    state.elements.monthlyLabel.classList.remove('pricing-toggle-v2-active-label');
                } else {
                    state.elements.monthlyLabel.style.color = '#0a0a0a';
                    state.elements.monthlyLabel.style.fontWeight = '600';
                    state.elements.monthlyLabel.classList.add('pricing-toggle-v2-active-label');
                }
            }
            
            if (state.elements.yearlyLabel) {
                if (isYearly) {
                    state.elements.yearlyLabel.style.color = '#0a0a0a';
                    state.elements.yearlyLabel.style.fontWeight = '600';
                    state.elements.yearlyLabel.classList.add('pricing-toggle-v2-active-label');
                } else {
                    state.elements.yearlyLabel.style.color = '#6b7280';
                    state.elements.yearlyLabel.style.fontWeight = '500';
                    state.elements.yearlyLabel.classList.remove('pricing-toggle-v2-active-label');
                }
            }
            
            log('info', 'Visual state updated successfully');
        } catch (error) {
            log('error', 'Failed to update visual state:', error);
        }
    }
    
    // Update pricing display with error handling
    function updatePricingDisplay(isYearly) {
        log('info', `Updating pricing display to: ${isYearly ? 'yearly' : 'monthly'}`);
        
        try {
            // Update state
            state.isYearly = isYearly;
            
            // Update visual state
            updateVisualState(isYearly);
            
            // Update price values
            const priceElements = document.querySelectorAll(CONFIG.priceValueSelector);
            log('debug', `Found ${priceElements.length} price elements`);
            
            priceElements.forEach((element, index) => {
                try {
                    const monthlyPrice = element.getAttribute('data-monthly');
                    const yearlyPrice = element.getAttribute('data-yearly');
                    
                    if (!monthlyPrice || !yearlyPrice) {
                        log('warn', `Missing price data for element ${index}:`, {
                            monthly: monthlyPrice,
                            yearly: yearlyPrice,
                            element: element
                        });
                        return;
                    }
                    
                    const newPrice = isYearly ? yearlyPrice : monthlyPrice;
                    element.textContent = newPrice;
                    element.classList.add('pricing-toggle-v2-updated');
                    
                    log('debug', `Updated price for element ${index}: ${newPrice}`);
                } catch (error) {
                    log('error', `Failed to update price for element ${index}:`, error);
                }
            });
            
            // Update annual price display
            const annualElements = document.querySelectorAll(CONFIG.annualPriceSelector);
            log('debug', `Found ${annualElements.length} annual price elements`);
            
            annualElements.forEach((element, index) => {
                try {
                    element.style.display = isYearly ? 'block' : 'none';
                    element.classList.add('pricing-toggle-v2-updated');
                    log('debug', `Updated annual display for element ${index}: ${isYearly ? 'visible' : 'hidden'}`);
                } catch (error) {
                    log('error', `Failed to update annual display for element ${index}:`, error);
                }
            });
            
            log('info', 'Pricing display updated successfully');
            
            // Trigger custom event for other scripts (if needed)
            try {
                const customEvent = new CustomEvent('pricingToggleV2Changed', {
                    detail: { isYearly: isYearly },
                    bubbles: false,
                    cancelable: false
                });
                document.dispatchEvent(customEvent);
                log('debug', 'Custom event dispatched');
            } catch (error) {
                log('warn', 'Failed to dispatch custom event:', error);
            }
            
        } catch (error) {
            log('error', 'Failed to update pricing display:', error);
        }
    }
    
    // Attach event listeners with conflict prevention
    function attachEventListeners() {
        if (state.eventListenersAttached) {
            log('warn', 'Event listeners already attached, skipping...');
            return;
        }
        
        log('info', 'Attaching event listeners...');
        
        try {
            // Toggle switch click handler
            if (state.elements.toggle) {
                const toggleHandler = function(event) {
                    log('debug', 'Toggle clicked');
                    event.preventDefault();
                    event.stopImmediatePropagation();
                    
                    const newState = !state.isYearly;
                    updatePricingDisplay(newState);
                };
                
                // Use capturing phase to prevent interference
                state.elements.toggle.addEventListener('click', toggleHandler, true);
                state.elements.toggle.addEventListener('touchend', toggleHandler, true);
                
                // Add keyboard accessibility
                state.elements.toggle.setAttribute('tabindex', '0');
                state.elements.toggle.setAttribute('role', 'switch');
                state.elements.toggle.setAttribute('aria-checked', 'false');
                
                const keyHandler = function(event) {
                    if (event.key === 'Enter' || event.key === ' ') {
                        event.preventDefault();
                        event.stopImmediatePropagation();
                        toggleHandler(event);
                    }
                };
                
                state.elements.toggle.addEventListener('keydown', keyHandler, true);
                
                log('debug', 'Toggle event listeners attached');
            }
            
            // Monthly label click handler
            if (state.elements.monthlyLabel) {
                const monthlyHandler = function(event) {
                    log('debug', 'Monthly label clicked');
                    event.preventDefault();
                    event.stopImmediatePropagation();
                    
                    if (state.isYearly) {
                        updatePricingDisplay(false);
                    }
                };
                
                state.elements.monthlyLabel.addEventListener('click', monthlyHandler, true);
                state.elements.monthlyLabel.addEventListener('touchend', monthlyHandler, true);
                
                log('debug', 'Monthly label event listeners attached');
            }
            
            // Yearly label click handler
            if (state.elements.yearlyLabel) {
                const yearlyHandler = function(event) {
                    log('debug', 'Yearly label clicked');
                    event.preventDefault();
                    event.stopImmediatePropagation();
                    
                    if (!state.isYearly) {
                        updatePricingDisplay(true);
                    }
                };
                
                state.elements.yearlyLabel.addEventListener('click', yearlyHandler, true);
                state.elements.yearlyLabel.addEventListener('touchend', yearlyHandler, true);
                
                log('debug', 'Yearly label event listeners attached');
            }
            
            state.eventListenersAttached = true;
            log('info', 'All event listeners attached successfully');
            
        } catch (error) {
            log('error', 'Failed to attach event listeners:', error);
        }
    }
    
    // Initialize the pricing toggle system
    async function initialize() {
        if (state.initialized) {
            log('warn', 'Already initialized, skipping...');
            return;
        }
        
        log('info', 'Initializing pricing toggle system...');
        
        try {
            // Find all required elements
            log('info', 'Finding DOM elements...');
            
            const [toggle, monthlyLabel, yearlyLabel] = await Promise.all([
                findElement(CONFIG.toggleId),
                findElement(CONFIG.monthlyLabelId),
                findElement(CONFIG.yearlyLabelId)
            ]);
            
            // Find slider within toggle
            const slider = toggle.querySelector('.toggle-slider');
            if (!slider) {
                throw new Error('Toggle slider not found within toggle element');
            }
            
            // Store element references
            state.elements = {
                toggle,
                monthlyLabel,
                yearlyLabel,
                slider
            };
            
            log('info', 'All DOM elements found successfully');
            
            // Apply inline styles
            applyInlineStyles();
            
            // Set initial state
            updateVisualState(false); // Start with monthly
            
            // Attach event listeners
            attachEventListeners();
            
            state.initialized = true;
            log('info', 'Pricing toggle system initialized successfully');
            
            // Add global reference for debugging
            if (CONFIG.debugMode) {
                window[NAMESPACE] = {
                    state,
                    updatePricingDisplay,
                    log
                };
                log('debug', `Debug interface available at window.${NAMESPACE}`);
            }
            
        } catch (error) {
            log('error', 'Failed to initialize pricing toggle system:', error);
            
            // Fallback: try to find elements differently
            setTimeout(() => {
                log('info', 'Attempting fallback initialization...');
                initializeFallback();
            }, 1000);
        }
    }
    
    // Fallback initialization with more permissive element finding
    function initializeFallback() {
        log('info', 'Running fallback initialization...');
        
        try {
            // Try alternative selectors
            const toggle = document.querySelector('#pricingToggle, .toggle-switch, [data-toggle="pricing"]');
            const monthlyLabel = document.querySelector('#monthlyLabel, .toggle-label[data-period="monthly"], .monthly-label');
            const yearlyLabel = document.querySelector('#yearlyLabel, .toggle-label[data-period="yearly"], .yearly-label');
            
            if (!toggle || !monthlyLabel || !yearlyLabel) {
                log('error', 'Fallback initialization failed - required elements not found');
                return;
            }
            
            log('info', 'Fallback found elements, proceeding with simplified initialization...');
            
            // Simple click handlers without complex features
            toggle.onclick = function(e) {
                e.preventDefault();
                e.stopPropagation();
                const isCurrentlyActive = toggle.classList.contains('active');
                
                if (isCurrentlyActive) {
                    toggle.classList.remove('active');
                    updateSimplePricing(false);
                } else {
                    toggle.classList.add('active');
                    updateSimplePricing(true);
                }
                
                log('info', `Fallback toggle: ${!isCurrentlyActive ? 'yearly' : 'monthly'}`);
            };
            
            monthlyLabel.onclick = function(e) {
                e.preventDefault();
                toggle.classList.remove('active');
                updateSimplePricing(false);
                log('info', 'Fallback: switched to monthly');
            };
            
            yearlyLabel.onclick = function(e) {
                e.preventDefault();
                toggle.classList.add('active');
                updateSimplePricing(true);
                log('info', 'Fallback: switched to yearly');
            };
            
            log('info', 'Fallback initialization completed');
            
        } catch (error) {
            log('error', 'Fallback initialization failed:', error);
        }
    }
    
    // Simplified pricing update for fallback
    function updateSimplePricing(isYearly) {
        try {
            const priceElements = document.querySelectorAll('.price-value');
            priceElements.forEach(el => {
                const monthly = el.getAttribute('data-monthly');
                const yearly = el.getAttribute('data-yearly');
                if (monthly && yearly) {
                    el.textContent = isYearly ? yearly : monthly;
                }
            });
            
            const annualElements = document.querySelectorAll('.annual-price');
            annualElements.forEach(el => {
                el.style.display = isYearly ? 'block' : 'none';
            });
            
        } catch (error) {
            log('error', 'Simple pricing update failed:', error);
        }
    }
    
    // Wait for DOM to be ready
    function waitForDOM() {
        if (document.readyState === 'loading') {
            log('info', 'DOM not ready, waiting...');
            document.addEventListener('DOMContentLoaded', initialize);
        } else {
            log('info', 'DOM ready, initializing immediately...');
            // Add small delay to ensure all other scripts have loaded
            setTimeout(initialize, 50);
        }
    }
    
    // Start the system
    log('info', 'Starting bulletproof pricing toggle system...');
    waitForDOM();
    
    // Also try initialization after a delay as extra safety
    setTimeout(() => {
        if (!state.initialized) {
            log('info', 'Delayed initialization attempt...');
            initialize();
        }
    }, 2000);
    
})();