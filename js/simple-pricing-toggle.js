// Simple Pricing Toggle - Guaranteed to Work
(function() {
    'use strict';
    
    // Wait for DOM
    function init() {
        console.log('[SimplePricingToggle] Initializing...');
        
        // Create new toggle UI
        const toggleContainer = document.getElementById('newPricingToggle');
        if (!toggleContainer) {
            console.error('[SimplePricingToggle] Container not found!');
            return;
        }
        
        // Create toggle elements
        toggleContainer.innerHTML = `
            <div style="display: flex; align-items: center; justify-content: center; gap: 20px; margin: 40px 0;">
                <button id="monthlyBtn" style="
                    padding: 12px 24px;
                    font-size: 16px;
                    font-weight: 600;
                    border: 2px solid #0066ff;
                    background: #0066ff;
                    color: white;
                    border-radius: 8px;
                    cursor: pointer;
                    transition: all 0.2s;
                    outline: none;
                ">Monthly</button>
                
                <button id="yearlyBtn" style="
                    padding: 12px 24px;
                    font-size: 16px;
                    font-weight: 600;
                    border: 2px solid #e5e7eb;
                    background: white;
                    color: #6b7280;
                    border-radius: 8px;
                    cursor: pointer;
                    transition: all 0.2s;
                    outline: none;
                ">Yearly <span style="background: #10b981; color: white; padding: 2px 8px; border-radius: 4px; font-size: 12px; margin-left: 8px;">Save 20%</span></button>
            </div>
        `;
        
        // Get button references
        const monthlyBtn = document.getElementById('monthlyBtn');
        const yearlyBtn = document.getElementById('yearlyBtn');
        
        // State
        let isYearly = false;
        
        // Update function
        function updatePricing(yearly) {
            isYearly = yearly;
            console.log(`[SimplePricingToggle] Switching to ${yearly ? 'Yearly' : 'Monthly'}`);
            
            // Update button styles
            if (yearly) {
                // Yearly active
                yearlyBtn.style.background = '#0066ff';
                yearlyBtn.style.borderColor = '#0066ff';
                yearlyBtn.style.color = 'white';
                
                monthlyBtn.style.background = 'white';
                monthlyBtn.style.borderColor = '#e5e7eb';
                monthlyBtn.style.color = '#6b7280';
            } else {
                // Monthly active
                monthlyBtn.style.background = '#0066ff';
                monthlyBtn.style.borderColor = '#0066ff';
                monthlyBtn.style.color = 'white';
                
                yearlyBtn.style.background = 'white';
                yearlyBtn.style.borderColor = '#e5e7eb';
                yearlyBtn.style.color = '#6b7280';
            }
            
            // Update prices
            const priceElements = document.querySelectorAll('.price-value');
            priceElements.forEach(el => {
                const monthlyPrice = el.getAttribute('data-monthly');
                const yearlyPrice = el.getAttribute('data-yearly');
                if (monthlyPrice && yearlyPrice) {
                    el.textContent = yearly ? yearlyPrice : monthlyPrice;
                }
            });
            
            // Update annual price displays
            const annualPrices = document.querySelectorAll('.annual-price');
            annualPrices.forEach(el => {
                el.style.display = yearly ? 'block' : 'none';
            });
            
            // Update old toggle if it exists (for compatibility)
            const oldToggle = document.getElementById('pricingToggle');
            if (oldToggle) {
                if (yearly) {
                    oldToggle.classList.add('active');
                } else {
                    oldToggle.classList.remove('active');
                }
            }
            
            // Dispatch event for other scripts
            window.dispatchEvent(new CustomEvent('pricingToggleChanged', { 
                detail: { isYearly: yearly } 
            }));
        }
        
        // Add click handlers
        monthlyBtn.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            updatePricing(false);
        });
        
        yearlyBtn.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            updatePricing(true);
        });
        
        // Add hover effects
        function addHoverEffect(btn) {
            btn.addEventListener('mouseenter', function() {
                if (this.style.background === 'white' || this.style.background === 'rgb(255, 255, 255)') {
                    this.style.background = '#f3f4f6';
                }
            });
            
            btn.addEventListener('mouseleave', function() {
                if (this.style.background === '#f3f4f6' || this.style.background === 'rgb(243, 244, 246)') {
                    this.style.background = 'white';
                }
            });
        }
        
        addHoverEffect(monthlyBtn);
        addHoverEffect(yearlyBtn);
        
        // Initialize with monthly
        updatePricing(false);
        
        // Make functions globally available for debugging
        window.SimplePricingToggle = {
            updatePricing: updatePricing,
            isYearly: () => isYearly
        };
        
        console.log('[SimplePricingToggle] Initialization complete!');
    }
    
    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();