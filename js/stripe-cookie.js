/**
 * Stripe Integration with Cookie Authentication
 * Works with httpOnly cookies for secure payment processing
 */

const STRIPE_API_BASE = (() => {
    const hostname = window.location.hostname;
    return hostname === 'localhost' || hostname === '127.0.0.1'
        ? 'http://localhost:5000/api/stripe'
        : `${window.location.protocol}//${hostname}/api/stripe`;
})();

console.log('[Stripe] Loading with cookie auth...');

// Wait for DOM and auth to be ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeStripe);
} else {
    initializeStripe();
}

function initializeStripe() {
    console.log('[Stripe] Initializing...');
    
    // Setup pricing buttons
    setupPricingButtons();
    
    // Handle payment success
    handlePaymentSuccess();
}

function setupPricingButtons() {
    const buttons = document.querySelectorAll('.pricing-cta.primary');
    console.log('[Stripe] Found pricing buttons:', buttons.length);
    
    buttons.forEach((button, index) => {
        const card = button.closest('.pricing-card');
        const planElement = card?.querySelector('[data-plan]') || card;
        const plan = button.dataset.plan || planElement.dataset.plan || 
                    card?.className.match(/plan-(\w+)/)?.[1] || 
                    ['starter', 'professional', 'business'][index];
        
        console.log(`[Stripe] Setting up button ${index} for plan: ${plan}`);
        
        button.addEventListener('click', async (e) => {
            e.preventDefault();
            console.log(`[Stripe] Buy button clicked for plan: ${plan}`);
            
            // Check if user is authenticated (cookie will be sent automatically)
            const isAuth = window.CookieAuth && window.CookieAuth.isAuthenticated();
            
            if (!isAuth) {
                console.log('[Stripe] User not authenticated, redirecting to signup...');
                window.location.href = `/signup.html?plan=${plan}&redirect=/pricing.html`;
                return;
            }
            
            // Get billing period
            const toggle = document.getElementById('pricingToggle');
            const isYearly = toggle && toggle.classList.contains('active');
            const billingPeriod = isYearly ? 'yearly' : 'monthly';
            
            console.log(`[Stripe] Billing period: ${billingPeriod}`);
            
            // Update button state
            const originalText = button.textContent;
            button.textContent = 'Processing...';
            button.disabled = true;
            button.style.opacity = '0.7';
            
            try {
                await createCheckoutSession(plan, billingPeriod);
            } catch (error) {
                console.error('[Stripe] Checkout error:', error);
                alert(`Error: ${error.message}`);
                
                // Restore button
                button.textContent = originalText;
                button.disabled = false;
                button.style.opacity = '';
            }
        });
    });
}

async function createCheckoutSession(plan, billingPeriod) {
    console.log('[Stripe] Creating checkout session:', { plan, billingPeriod });
    
    try {
        // Use cookie auth - no need for Bearer token
        const response = await fetch(`${STRIPE_API_BASE}/create-checkout-session`, {
            method: 'POST',
            credentials: 'include', // This sends cookies
            headers: {
                'Content-Type': 'application/json',
                'X-CSRF-Token': window.CookieAuth?.csrfToken || ''
            },
            body: JSON.stringify({
                plan: plan,
                billing_period: billingPeriod
            })
        });
        
        if (!response.ok) {
            let errorMessage = 'Failed to create checkout session';
            try {
                const error = await response.json();
                errorMessage = error.detail || errorMessage;
            } catch (e) {
                errorMessage = `Server error: ${response.status}`;
            }
            throw new Error(errorMessage);
        }
        
        const data = await response.json();
        console.log('[Stripe] Checkout session created:', data);
        
        if (data.checkout_url) {
            window.location.href = data.checkout_url;
        } else {
            throw new Error('No checkout URL received');
        }
    } catch (error) {
        console.error('[Stripe] Checkout session error:', error);
        throw error;
    }
}

function handlePaymentSuccess() {
    const params = new URLSearchParams(window.location.search);
    if (params.get('payment') === 'success') {
        console.log('[Stripe] Payment successful!');
        
        // Show success message
        const message = document.createElement('div');
        message.className = 'alert alert-success';
        message.style.cssText = `
            background: #d4edda;
            border: 1px solid #c3e6cb;
            color: #155724;
            padding: 1rem;
            border-radius: 0.5rem;
            margin: 1rem 0;
            text-align: center;
        `;
        message.innerHTML = `
            <h3>Payment Successful!</h3>
            <p>Thank you for your subscription. You now have access to all premium features.</p>
        `;
        
        const container = document.querySelector('.pricing-container') || 
                         document.querySelector('main') || 
                         document.body;
        
        if (container) {
            container.insertBefore(message, container.firstChild);
        }
        
        // Remove success parameter from URL
        window.history.replaceState({}, document.title, window.location.pathname);
    }
}

console.log('[Stripe] Cookie-based Stripe integration loaded');