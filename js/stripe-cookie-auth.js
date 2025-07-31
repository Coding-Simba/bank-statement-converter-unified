/**
 * Stripe integration using cookie-based authentication
 */

(function() {
    console.log('[Stripe Cookie Auth] Initializing...');
    
    // Only run on pricing page
    if (!window.location.pathname.includes('pricing')) {
        return;
    }
    
    async function setupBuyButtons() {
        // Wait for auth service to initialize
        if (!window.authService) {
            setTimeout(setupBuyButtons, 100);
            return;
        }
        
        await window.authService.initialize();
        
        console.log('[Stripe Cookie Auth] Setting up buy buttons...');
        
        const buttons = document.querySelectorAll('.pricing-cta.primary');
        const plans = ['starter', 'professional', 'business'];
        
        buttons.forEach((button, index) => {
            if (!button.textContent.toLowerCase().includes('buy')) {
                return;
            }
            
            const plan = plans[index];
            if (!plan) return;
            
            // Remove href to prevent navigation
            button.removeAttribute('href');
            button.style.cursor = 'pointer';
            
            button.addEventListener('click', async function(e) {
                e.preventDefault();
                e.stopPropagation();
                
                console.log(`[Stripe Cookie Auth] Buy clicked for plan: ${plan}`);
                
                // Check if authenticated
                if (!window.authService.isAuthenticated()) {
                    console.log('[Stripe Cookie Auth] Not authenticated, redirecting to login...');
                    
                    // Save state for after login
                    sessionStorage.setItem('redirect_after_stripe', window.location.href);
                    sessionStorage.setItem('stripe_plan', plan);
                    
                    window.location.href = '/login.html?redirect=' + encodeURIComponent(window.location.href);
                    return;
                }
                
                console.log('[Stripe Cookie Auth] User authenticated, creating checkout session...');
                
                // Get billing period
                const toggleElement = document.getElementById('pricingToggle');
                const billingPeriod = toggleElement?.classList.contains('active') ? 'yearly' : 'monthly';
                
                // Update button state
                const originalText = this.textContent;
                this.textContent = 'Processing...';
                this.disabled = true;
                this.style.opacity = '0.7';
                
                try {
                    // Use auth service for authenticated request
                    const response = await window.authService.fetch('/api/stripe/create-checkout-session', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({
                            plan: plan,
                            billing_period: billingPeriod
                        })
                    });
                    
                    console.log('[Stripe Cookie Auth] Response status:', response.status);
                    
                    if (response.ok) {
                        const data = await response.json();
                        console.log('[Stripe Cookie Auth] Checkout session created, redirecting...');
                        
                        if (data.checkout_url) {
                            window.location.href = data.checkout_url;
                        } else {
                            throw new Error('No checkout URL received');
                        }
                    } else {
                        const error = await response.json();
                        throw new Error(error.detail || 'Failed to create checkout session');
                    }
                } catch (error) {
                    console.error('[Stripe Cookie Auth] Error:', error);
                    alert('Unable to process payment. Please try again or contact support.');
                    
                    // Restore button
                    this.textContent = originalText;
                    this.disabled = false;
                    this.style.opacity = '1';
                }
            });
        });
        
        // Check for auto-click after login
        const savedPlan = sessionStorage.getItem('stripe_plan');
        if (savedPlan && window.authService.isAuthenticated()) {
            console.log('[Stripe Cookie Auth] Auto-clicking saved plan:', savedPlan);
            
            // Clear saved state
            sessionStorage.removeItem('stripe_plan');
            sessionStorage.removeItem('redirect_after_stripe');
            
            // Auto-click the button
            setTimeout(() => {
                const planIndex = plans.indexOf(savedPlan);
                if (planIndex !== -1) {
                    const button = buttons[planIndex];
                    if (button && button.textContent.toLowerCase().includes('buy')) {
                        console.log('[Stripe Cookie Auth] Triggering auto-click...');
                        button.click();
                    }
                }
            }, 1000);
        }
    }
    
    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', setupBuyButtons);
    } else {
        setupBuyButtons();
    }
})();