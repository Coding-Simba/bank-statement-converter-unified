// Stripe Integration - Works with both JWT and Cookie Auth

const STRIPE_API_BASE = (() => {
    const hostname = window.location.hostname;
    return hostname === 'localhost' || hostname === '127.0.0.1'
        ? 'http://localhost:5000/api/stripe'
        : `${window.location.protocol}//${hostname}/api/stripe`;
})();

document.addEventListener('DOMContentLoaded', function() {
    console.log('[Stripe] Initializing dual-auth integration...');
    setupPricingButtons();
    handlePaymentSuccess();
});

function setupPricingButtons() {
    const pricingButtons = document.querySelectorAll('.pricing-cta.primary');
    console.log('[Stripe] Found pricing buttons:', pricingButtons.length);
    
    pricingButtons.forEach((button, index) => {
        const plans = ['starter', 'professional', 'business'];
        const plan = button.getAttribute('data-plan') || plans[index];
        
        button.addEventListener('click', async (e) => {
            e.preventDefault();
            console.log('[Stripe] Buy button clicked for plan:', plan);
            
            // Check authentication - multiple methods
            let isAuthenticated = false;
            
            // Method 1: Check localStorage JWT token
            if (localStorage.getItem('access_token')) {
                isAuthenticated = true;
                console.log('[Stripe] Auth detected: JWT token');
            }
            
            // Method 2: Check CookieAuth
            if (!isAuthenticated && window.CookieAuth && window.CookieAuth.isAuthenticated) {
                isAuthenticated = window.CookieAuth.isAuthenticated();
                console.log('[Stripe] Auth detected: CookieAuth');
            }
            
            console.log('[Stripe] Is authenticated:', isAuthenticated);
            
            if (!isAuthenticated) {
                console.log('[Stripe] Not authenticated, redirecting...');
                window.location.href = `/signup.html?plan=${plan}&redirect=/pricing.html`;
                return;
            }
            
            // Get billing period
            const toggle = document.getElementById('pricingToggle');
            const isYearly = toggle && toggle.classList.contains('active');
            const billingPeriod = isYearly ? 'yearly' : 'monthly';
            
            // Show loading
            const originalText = button.textContent;
            button.textContent = 'Processing...';
            button.disabled = true;
            button.style.opacity = '0.7';
            
            try {
                // Prepare headers
                const headers = { 'Content-Type': 'application/json' };
                const token = localStorage.getItem('access_token');
                if (token) {
                    headers['Authorization'] = `Bearer ${token}`;
                }
                
                // Make request
                const response = await fetch(`${STRIPE_API_BASE}/create-checkout-session`, {
                    method: 'POST',
                    credentials: 'include',
                    headers: headers,
                    body: JSON.stringify({
                        plan: plan,
                        billing_period: billingPeriod
                    })
                });
                
                console.log('[Stripe] Response status:', response.status);
                
                if (!response.ok) {
                    const error = await response.json();
                    console.error('[Stripe] API error:', error);
                    throw new Error(error.detail || 'Failed to create checkout session');
                }
                
                const data = await response.json();
                console.log('[Stripe] Checkout session created:', data);
                
                if (data.checkout_url) {
                    window.location.href = data.checkout_url;
                } else {
                    throw new Error('No checkout URL received');
                }
                
            } catch (error) {
                console.error('[Stripe] Error:', error);
                alert('Error: ' + error.message);
                button.textContent = originalText;
                button.disabled = false;
                button.style.opacity = '';
            }
        });
    });
}

function handlePaymentSuccess() {
    const params = new URLSearchParams(window.location.search);
    if (params.get('payment') === 'success') {
        const message = document.createElement('div');
        message.style.cssText = 'background: #10b981; color: white; padding: 20px; text-align: center; margin: 20px 0; border-radius: 8px;';
        message.innerHTML = '<h3>Payment Successful!</h3><p>Thank you for your subscription.</p>';
        
        const container = document.querySelector('.pricing-grid')?.parentElement || document.body;
        container.insertBefore(message, container.firstChild);
        
        window.history.replaceState({}, document.title, window.location.pathname);
    }
}

console.log('[Stripe] Dual-auth integration loaded');