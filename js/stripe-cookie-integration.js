// Stripe Integration for Cookie-Based Auth System

// API Base URL
const STRIPE_API_BASE = (() => {
    const hostname = window.location.hostname;
    return hostname === 'localhost' || hostname === '127.0.0.1'
        ? 'http://localhost:5000/api/stripe'
        : `${window.location.protocol}//${hostname}/api/stripe`;
})();

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    console.log('[Stripe Cookie] Initializing...');
    
    // Setup pricing buttons
    setupPricingButtons();
    
    // Handle payment success
    handlePaymentSuccess();
});

function setupPricingButtons() {
    const pricingButtons = document.querySelectorAll('.pricing-cta.primary');
    console.log('[Stripe Cookie] Found pricing buttons:', pricingButtons.length);
    
    pricingButtons.forEach((button, index) => {
        const plans = ['starter', 'professional', 'business'];
        const plan = button.getAttribute('data-plan') || plans[index];
        console.log(`[Stripe Cookie] Setting up button ${index} for plan: ${plan}`);
        
        button.addEventListener('click', async (e) => {
            e.preventDefault();
            console.log(`[Stripe Cookie] Buy button clicked for plan: ${plan}`);
            
            // Check if user is authenticated using CookieAuth
            let isAuthenticated = false;
            if (window.CookieAuth && window.CookieAuth.isAuthenticated) {
                isAuthenticated = window.CookieAuth.isAuthenticated();
            }
            
            console.log('[Stripe Cookie] Is authenticated:', isAuthenticated);
            
            if (!isAuthenticated) {
                console.log('[Stripe Cookie] User not authenticated, redirecting to signup...');
                window.location.href = `/signup.html?plan=${plan}&redirect=/pricing.html`;
                return;
            }
            
            // Get billing period
            const toggleElement = document.getElementById('pricingToggle');
            const isYearly = toggleElement && toggleElement.classList.contains('active');
            const billingPeriod = isYearly ? 'yearly' : 'monthly';
            
            console.log('[Stripe Cookie] Billing period:', billingPeriod);
            
            // Show loading state
            const originalText = button.textContent;
            button.textContent = 'Processing...';
            button.disabled = true;
            button.style.opacity = '0.7';
            
            try {
                // Make request using cookie auth
                const response = await makeAuthenticatedRequest(`${STRIPE_API_BASE}/create-checkout-session`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        plan: plan,
                        billing_period: billingPeriod
                    })
                });
                
                console.log('[Stripe Cookie] Response status:', response.status);
                
                if (!response.ok) {
                    const error = await response.json();
                    console.error('[Stripe Cookie] API error:', error);
                    throw new Error(error.detail || 'Failed to create checkout session');
                }
                
                const data = await response.json();
                console.log('[Stripe Cookie] Checkout session created:', data);
                
                if (data.checkout_url) {
                    window.location.href = data.checkout_url;
                } else {
                    throw new Error('No checkout URL received');
                }
                
            } catch (error) {
                console.error('[Stripe Cookie] Checkout error:', error);
                alert('Failed to start checkout: ' + error.message);
                
                // Restore button state
                button.textContent = originalText;
                button.disabled = false;
                button.style.opacity = '';
            }
        });
    });
}

async function makeAuthenticatedRequest(url, options = {}) {
    // Use CookieAuth's makeRequest if available
    if (window.CookieAuth && window.CookieAuth.makeRequest) {
        console.log('[Stripe Cookie] Using CookieAuth.makeRequest');
        return window.CookieAuth.makeRequest(url, options);
    }
    
    // Otherwise, make a standard fetch with credentials
    console.log('[Stripe Cookie] Using standard fetch with credentials');
    return fetch(url, {
        ...options,
        credentials: 'include', // Always include cookies
        headers: {
            ...options.headers,
            'X-CSRF-Token': window.CookieAuth?.csrfToken || ''
        }
    });
}

function handlePaymentSuccess() {
    const params = new URLSearchParams(window.location.search);
    if (params.get('payment') === 'success') {
        console.log('[Stripe Cookie] Payment successful!');
        
        const message = document.createElement('div');
        message.style.cssText = `
            background: #10b981;
            color: white;
            padding: 20px;
            border-radius: 8px;
            margin: 20px auto;
            max-width: 600px;
            text-align: center;
        `;
        message.innerHTML = `
            <h3 style="margin: 0 0 8px 0;">Payment Successful!</h3>
            <p style="margin: 0;">Thank you for your subscription. Your account has been upgraded.</p>
        `;
        
        const container = document.querySelector('.pricing-grid')?.parentElement || 
                         document.querySelector('.container') || 
                         document.body;
        
        if (container) {
            container.insertBefore(message, container.firstChild);
        }
        
        // Clean URL
        window.history.replaceState({}, document.title, window.location.pathname);
    }
}

console.log('[Stripe Cookie] Integration loaded');