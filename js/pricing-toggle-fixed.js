// Fixed Pricing Toggle for Production
(function() {
    'use strict';
    
    console.log('[PricingToggle] Initializing fixed version...');
    
    // Wait for DOM
    function init() {
        // Find or create toggle container
        let toggleContainer = document.getElementById('newPricingToggle');
        
        // If container doesn't exist, create it after hero section
        if (!toggleContainer) {
            console.log('[PricingToggle] Container not found, creating it...');
            const heroSection = document.querySelector('.hero');
            if (heroSection && heroSection.parentNode) {
                toggleContainer = document.createElement('div');
                toggleContainer.id = 'newPricingToggle';
                heroSection.parentNode.insertBefore(toggleContainer.nextSibling, heroSection.nextSibling);
            } else {
                console.error('[PricingToggle] Could not find hero section!');
                return;
            }
        }
        
        // Clear existing content and add our toggle
        toggleContainer.innerHTML = `
            <div class="pricing-toggle-container" style="
                display: flex;
                align-items: center;
                justify-content: center;
                margin: 40px auto;
                max-width: 400px;
                padding: 8px;
                background: #f3f4f6;
                border-radius: 12px;
                position: relative;
            ">
                <button class="toggle-btn monthly-btn active" data-period="monthly" style="
                    flex: 1;
                    padding: 12px 24px;
                    font-size: 16px;
                    font-weight: 600;
                    border: none;
                    background: #0066ff;
                    color: white;
                    border-radius: 8px;
                    cursor: pointer;
                    transition: all 0.3s ease;
                    outline: none;
                    position: relative;
                    z-index: 2;
                ">Monthly</button>
                
                <button class="toggle-btn yearly-btn" data-period="yearly" style="
                    flex: 1;
                    padding: 12px 24px;
                    font-size: 16px;
                    font-weight: 600;
                    border: none;
                    background: transparent;
                    color: #6b7280;
                    border-radius: 8px;
                    cursor: pointer;
                    transition: all 0.3s ease;
                    outline: none;
                    position: relative;
                    z-index: 2;
                ">
                    Yearly 
                    <span class="save-badge" style="
                        background: #10b981;
                        color: white;
                        padding: 2px 8px;
                        border-radius: 4px;
                        font-size: 12px;
                        margin-left: 8px;
                        font-weight: 500;
                    ">Save 20%</span>
                </button>
            </div>
        `;
        
        // Add custom styles to override any conflicts
        const style = document.createElement('style');
        style.textContent = `
            #newPricingToggle {
                display: block !important;
                visibility: visible !important;
                opacity: 1 !important;
            }
            
            .pricing-toggle-container {
                display: flex !important;
            }
            
            .toggle-btn {
                font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
            }
            
            .toggle-btn:hover {
                transform: translateY(-1px);
                box-shadow: 0 4px 12px rgba(0, 102, 255, 0.15);
            }
            
            .toggle-btn.active {
                background: #0066ff !important;
                color: white !important;
            }
            
            .toggle-btn:not(.active) {
                background: transparent !important;
                color: #6b7280 !important;
            }
            
            .toggle-btn:not(.active):hover {
                background: rgba(0, 102, 255, 0.05) !important;
            }
            
            @media (max-width: 640px) {
                .pricing-toggle-container {
                    margin: 20px 16px !important;
                }
                
                .toggle-btn {
                    font-size: 14px !important;
                    padding: 10px 16px !important;
                }
                
                .save-badge {
                    display: block !important;
                    margin-left: 0 !important;
                    margin-top: 4px !important;
                }
            }
        `;
        document.head.appendChild(style);
        
        // Get buttons
        const monthlyBtn = document.querySelector('.monthly-btn');
        const yearlyBtn = document.querySelector('.yearly-btn');
        
        if (!monthlyBtn || !yearlyBtn) {
            console.error('[PricingToggle] Buttons not found!');
            return;
        }
        
        // Toggle function
        function updatePricing(period) {
            const isYearly = period === 'yearly';
            console.log(`[PricingToggle] Switching to ${period}`);
            
            // Update button states
            if (isYearly) {
                yearlyBtn.classList.add('active');
                monthlyBtn.classList.remove('active');
            } else {
                monthlyBtn.classList.add('active');
                yearlyBtn.classList.remove('active');
            }
            
            // Update prices
            document.querySelectorAll('.price-value').forEach(el => {
                const monthly = el.getAttribute('data-monthly');
                const yearly = el.getAttribute('data-yearly');
                if (monthly && yearly) {
                    el.textContent = isYearly ? yearly : monthly;
                }
            });
            
            // Update period text
            document.querySelectorAll('.period').forEach(el => {
                el.textContent = isYearly ? '/year' : '/month';
            });
            
            // Show/hide annual price info
            document.querySelectorAll('.annual-price').forEach(el => {
                el.style.display = isYearly ? 'block' : 'none';
            });
            
            // Update old toggle if exists
            const oldToggle = document.getElementById('pricingToggle');
            if (oldToggle) {
                if (isYearly) {
                    oldToggle.classList.add('active');
                } else {
                    oldToggle.classList.remove('active');
                }
            }
            
            // Dispatch event
            window.dispatchEvent(new CustomEvent('pricingToggleChanged', {
                detail: { isYearly }
            }));
        }
        
        // Add click handlers
        monthlyBtn.addEventListener('click', (e) => {
            e.preventDefault();
            updatePricing('monthly');
        });
        
        yearlyBtn.addEventListener('click', (e) => {
            e.preventDefault();
            updatePricing('yearly');
        });
        
        // Initialize with monthly
        updatePricing('monthly');
        
        console.log('[PricingToggle] Fixed toggle initialized successfully!');
    }
    
    // Initialize when ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();