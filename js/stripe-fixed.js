/**
 * FIXED Stripe Integration
 * Handles pricing page buy buttons with proper auth checking and error handling
 */

// API Configuration with fallbacks
const STRIPE_API_BASE = (() => {
    if (typeof getApiBase === 'function') {
        return getApiBase() + '/api/stripe';
    }
    if (window.API_CONFIG && window.API_CONFIG.getBaseUrl) {
        return window.API_CONFIG.getBaseUrl() + '/api/stripe';
    }
    const protocol = window.location.protocol;
    const hostname = window.location.hostname;
    return hostname === 'localhost' || hostname === '127.0.0.1'
        ? 'http://localhost:5000/api/stripe'
        : `${protocol}//${hostname}/api/stripe`;
})();

console.log('Stripe integration loading...');
console.log('API Base:', STRIPE_API_BASE);

// Wait for both DOM and auth to be ready
function initializeStripe() {
    console.log('Initializing Stripe integration...');
    
    // Check if UnifiedAuth exists
    const authAvailable = typeof window.UnifiedAuth !== 'undefined';
    console.log('UnifiedAuth available:', authAvailable);
    
    // Setup pricing buttons
    setupPricingButtons();
    
    // Check subscription status if authenticated
    if (authAvailable && window.UnifiedAuth.isAuthenticated && window.UnifiedAuth.isAuthenticated()) {
        checkSubscriptionStatus();
    }
    
    // Handle payment success
    handlePaymentSuccess();
}

function setupPricingButtons() {
    const pricingButtons = document.querySelectorAll('.pricing-cta.primary');
    console.log('Found pricing buttons:', pricingButtons.length);
    
    if (pricingButtons.length === 0) {
        console.warn('No pricing buttons found! Looking for .pricing-cta.primary');
        return;
    }
    
    // Map plans to buttons by order
    const plans = ['starter', 'professional', 'business'];
    
    pricingButtons.forEach((button, index) => {
        const plan = plans[index] || 'unknown';
        console.log(`Setting up button ${index} for plan: ${plan}`);
        
        // Add data attribute for easier identification
        button.setAttribute('data-plan', plan);
        
        button.addEventListener('click', async (e) => {
            e.preventDefault();
            console.log(`Buy button clicked for plan: ${plan}`);
            
            // Check authentication - fallback to localStorage if UnifiedAuth is not ready
            const isAuth = (window.UnifiedAuth && 
                          window.UnifiedAuth.isAuthenticated && 
                          window.UnifiedAuth.isAuthenticated()) ||
                          localStorage.getItem('access_token') !== null;
            
            if (!isAuth) {
                console.log('User not authenticated, redirecting to signup...');
                // Check if we're already coming from signup/login to prevent loops
                const referrer = document.referrer;
                if (referrer.includes('/signup.html') || referrer.includes('/login.html')) {
                    console.error('Redirect loop detected! Not redirecting again.');
                    alert('Authentication issue detected. Please try logging in again.');
                    return;
                }
                window.location.href = `/signup.html?plan=${plan}&redirect=/pricing.html`;
                return;
            }
            
            // Get billing period from toggle
            const toggle = document.getElementById('pricingToggle');
            const isYearly = toggle && toggle.classList.contains('active');
            const billingPeriod = isYearly ? 'yearly' : 'monthly';
            
            console.log('Billing period:', billingPeriod);
            
            // Update button state
            const originalText = button.textContent;
            button.textContent = 'Processing...';
            button.style.pointerEvents = 'none';
            button.style.opacity = '0.7';
            
            try {
                await createCheckoutSession(plan, billingPeriod);
            } catch (error) {
                console.error('Checkout error:', error);
                alert(`Error: ${error.message}`);
                
                // Restore button state
                button.textContent = originalText;
                button.style.pointerEvents = '';
                button.style.opacity = '';
            }
        });
    });
}

async function createCheckoutSession(plan, billingPeriod) {
    console.log('Creating checkout session:', { plan, billingPeriod });
    
    // Get access token
    const accessToken = localStorage.getItem('access_token');
    if (!accessToken) {
        throw new Error('Not authenticated. Please log in.');
    }
    
    try {
        const response = await fetch(`${STRIPE_API_BASE}/create-checkout-session`, {
            method: 'POST',
            credentials: 'include',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${accessToken}`
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
                // Response wasn't JSON
                errorMessage = `Server error: ${response.status}`;
            }
            throw new Error(errorMessage);
        }
        
        const data = await response.json();
        console.log('Checkout session created:', data);
        
        if (data.checkout_url) {
            window.location.href = data.checkout_url;
        } else {
            throw new Error('No checkout URL received');
        }
    } catch (error) {
        console.error('Checkout session error:', error);
        throw error;
    }
}

async function checkSubscriptionStatus() {
    console.log('Checking subscription status...');
    
    if (!window.UnifiedAuth || !window.UnifiedAuth.makeAuthenticatedRequest) {
        console.warn('Cannot check subscription: auth not ready');
        return;
    }
    
    try {
        const response = await window.UnifiedAuth.makeAuthenticatedRequest(
            `${STRIPE_API_BASE}/subscription-status`
        );
        
        if (response.ok) {
            const data = await response.json();
            console.log('Subscription status:', data);
            
            if (data.has_active_subscription) {
                updateUIForActiveSubscription(data.subscription);
            }
        }
    } catch (error) {
        console.error('Error checking subscription:', error);
    }
}

function updateUIForActiveSubscription(subscription) {
    const planName = subscription.plan_name.toLowerCase();
    const buttons = document.querySelectorAll('.pricing-cta.primary');
    
    buttons.forEach((button) => {
        const buttonPlan = button.getAttribute('data-plan');
        
        if (buttonPlan === planName) {
            button.textContent = 'Current Plan';
            button.classList.add('disabled');
            button.style.cursor = 'default';
            button.style.opacity = '0.6';
            button.removeEventListener('click', () => {});
            
            // Add active indicator to card
            const card = button.closest('.pricing-card');
            if (card) {
                card.classList.add('active-plan');
            }
        }
    });
}

function handlePaymentSuccess() {
    const urlParams = new URLSearchParams(window.location.search);
    
    if (urlParams.get('payment') === 'success') {
        console.log('Payment successful!');
        
        // Show success message
        const message = document.createElement('div');
        message.className = 'payment-success-message';
        message.innerHTML = `
            <div style="background: #10b981; color: white; padding: 16px; border-radius: 8px; margin: 20px auto; max-width: 600px; text-align: center;">
                <h3 style="margin: 0 0 8px 0;">Payment Successful!</h3>
                <p style="margin: 0;">Thank you for your subscription. Your account has been upgraded.</p>
            </div>
        `;
        
        const container = document.querySelector('.container');
        if (container) {
            container.insertBefore(message, container.firstChild);
        }
        
        // Refresh subscription status
        if (window.UnifiedAuth && window.UnifiedAuth.isAuthenticated && window.UnifiedAuth.isAuthenticated()) {
            checkSubscriptionStatus();
        }
        
        // Remove success parameter from URL
        window.history.replaceState({}, document.title, window.location.pathname);
    }
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeStripe);
} else {
    // DOM already loaded, but wait a bit for auth to initialize
    setTimeout(initializeStripe, 100);
}

// Also initialize when auth is ready
window.addEventListener('unifiedauth:ready', initializeStripe);
window.addEventListener('cookie-auth-ready', initializeStripe);
window.addEventListener('auth-state-changed', initializeStripe);

console.log('Stripe integration script loaded');