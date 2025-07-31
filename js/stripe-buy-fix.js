// Simple Stripe Buy Button Fix
(function() {
    console.log('[Stripe Buy Fix] Loading...');
    
    // Only run on pricing page
    if (!window.location.pathname.includes('pricing.html')) {
        return;
    }
    
    const API_BASE = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
        ? 'http://localhost:5000'
        : `${window.location.protocol}//${window.location.hostname}`;
    
    function setupBuyButtons() {
        console.log('[Stripe Buy Fix] Setting up buy buttons...');
        
        // Get all buy buttons
        const buttons = document.querySelectorAll('.pricing-cta.primary');
        console.log('[Stripe Buy Fix] Found buttons:', buttons.length);
        
        buttons.forEach((button, index) => {
            // Skip if not a buy button
            if (!button.textContent.trim().toLowerCase().includes('buy')) {
                console.log('[Stripe Buy Fix] Skipping non-buy button:', button.textContent);
                return;
            }
            
            const plans = ['starter', 'professional', 'business'];
            const plan = plans[index];
            
            console.log(`[Stripe Buy Fix] Setting up ${plan} button`);
            
            // Remove href="#" to prevent default navigation
            button.removeAttribute('href');
            button.style.cursor = 'pointer';
            
            // Add click handler directly (not replacing the button)
            button.onclick = async function(e) {
                e.preventDefault();
                e.stopPropagation();
                e.stopImmediatePropagation();
                
                console.log(`[Stripe Buy Fix] ${plan} button clicked!`);
                
                // Check auth
                const token = localStorage.getItem('access_token');
                const userData = localStorage.getItem('user_data') || localStorage.getItem('user');
                
                console.log('[Stripe Buy Fix] Auth check:', {
                    hasToken: !!token,
                    hasUserData: !!userData
                });
                
                if (!token || !userData) {
                    console.log('[Stripe Buy Fix] Not authenticated, redirecting to login...');
                    sessionStorage.setItem('redirect_after_stripe', window.location.href);
                    sessionStorage.setItem('stripe_plan', plan);
                    window.location.href = '/login.html';
                    return;
                }
                
                console.log('[Stripe Buy Fix] Authenticated! Creating checkout session...');
                
                // Show loading state
                const originalText = this.textContent;
                this.textContent = 'Processing...';
                this.disabled = true;
                
                try {
                    // Get billing period
                    const toggleElement = document.getElementById('pricingToggle');
                    const billingPeriod = toggleElement?.classList.contains('active') ? 'yearly' : 'monthly';
                    
                    console.log('[Stripe Buy Fix] Calling API with:', { plan, billingPeriod });
                    
                    const response = await fetch(`${API_BASE}/api/stripe/create-checkout-session`, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'Authorization': `Bearer ${token}`
                        },
                        body: JSON.stringify({
                            plan: plan,
                            billing_period: billingPeriod
                        })
                    });
                    
                    console.log('[Stripe Buy Fix] Response status:', response.status);
                    
                    if (response.status === 401) {
                        console.log('[Stripe Buy Fix] Token expired, clearing and redirecting...');
                        localStorage.clear();
                        sessionStorage.setItem('redirect_after_stripe', window.location.href);
                        sessionStorage.setItem('stripe_plan', plan);
                        window.location.href = '/login.html';
                        return;
                    }
                    
                    const data = await response.json();
                    console.log('[Stripe Buy Fix] Response data:', data);
                    
                    if (response.ok && data.checkout_url) {
                        console.log('[Stripe Buy Fix] Success! Redirecting to Stripe...');
                        window.location.href = data.checkout_url;
                    } else {
                        throw new Error(data.detail || 'Failed to create checkout session');
                    }
                    
                } catch (error) {
                    console.error('[Stripe Buy Fix] Error:', error);
                    alert('Unable to process payment. Please try again.');
                    this.textContent = originalText;
                    this.disabled = false;
                }
            };
        });
        
        console.log('[Stripe Buy Fix] Button setup complete');
    }
    
    // Run setup with delay to ensure page is fully loaded
    setTimeout(setupBuyButtons, 1000);
    
    // Also run on DOM ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', setupBuyButtons);
    }
})();