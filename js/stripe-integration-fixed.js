// Fixed Stripe Integration for Pricing Page
// Works with auth-fixed.js authentication system

// Use the existing getApiBase from auth.js or API_CONFIG
const STRIPE_API_BASE = (() => {
    // Check if getApiBase already exists from auth.js
    if (typeof getApiBase !== 'undefined') {
        return getApiBase() + '/api/stripe';
    }
    // Otherwise use API_CONFIG
    if (window.API_CONFIG) {
        return window.API_CONFIG.getBaseUrl() + '/api/stripe';
    }
    // Fallback
    const hostname = window.location.hostname;
    if (hostname === 'localhost' || hostname === '127.0.0.1') {
        return 'http://localhost:5000/api/stripe';
    }
    return `${window.location.protocol}//${hostname}/api/stripe`;
})();

// Check if user is authenticated using localStorage
function isUserAuthenticated() {
    const token = localStorage.getItem('access_token');
    const userData = localStorage.getItem('user_data') || localStorage.getItem('user');
    return !!(token && userData);
}

// Get access token
function getAccessToken() {
    return localStorage.getItem('access_token');
}

// Initialize Stripe integration
document.addEventListener('DOMContentLoaded', () => {
    console.log('[Stripe Fixed] Initializing...');
    
    // Get all pricing buttons
    const pricingButtons = document.querySelectorAll('.pricing-cta.primary');
    
    console.log('[Stripe Fixed] Found pricing buttons:', pricingButtons.length);
    
    pricingButtons.forEach((button, index) => {
        // Skip if button is not a "Buy" button
        if (!button.textContent.includes('Buy')) {
            return;
        }
        
        // Determine the plan based on button position
        const plans = ['starter', 'professional', 'business'];
        const plan = plans[index];
        console.log(`[Stripe Fixed] Setting up button ${index} for plan: ${plan}`);
        
        if (plan) {
            button.addEventListener('click', async (e) => {
                e.preventDefault();
                console.log('[Stripe Fixed] Buy button clicked for plan:', plan);
                
                // Check if user is authenticated
                if (!isUserAuthenticated()) {
                    console.log('[Stripe Fixed] User not authenticated, redirecting to login...');
                    // Store the intended plan and redirect URL
                    sessionStorage.setItem('intended_plan', plan);
                    sessionStorage.setItem('redirect_after_login', window.location.href);
                    // Redirect to login (not signup)
                    window.location.href = `/login.html`;
                    return;
                }
                
                console.log('[Stripe Fixed] User is authenticated, proceeding with checkout...');
                
                // Get billing period (monthly or yearly)
                const toggleElement = document.getElementById('pricingToggle');
                const isYearly = toggleElement && toggleElement.classList.contains('active');
                const billingPeriod = isYearly ? 'yearly' : 'monthly';
                
                console.log('[Stripe Fixed] Billing period:', billingPeriod);
                
                // Show loading state
                const originalText = button.textContent;
                button.textContent = 'Processing...';
                button.disabled = true;
                button.style.opacity = '0.7';
                
                try {
                    // Log what we're sending
                    const payload = {
                        plan: plan,
                        billing_period: billingPeriod
                    };
                    console.log('[Stripe Fixed] Sending to Stripe API:', payload);
                    console.log('[Stripe Fixed] API URL:', `${STRIPE_API_BASE}/create-checkout-session`);
                    
                    // Create checkout session
                    const response = await fetch(`${STRIPE_API_BASE}/create-checkout-session`, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'Authorization': `Bearer ${getAccessToken()}`
                        },
                        body: JSON.stringify(payload)
                    });
                    
                    console.log('[Stripe Fixed] Response status:', response.status);
                    
                    if (!response.ok) {
                        const error = await response.json();
                        console.error('[Stripe Fixed] API error:', error);
                        throw new Error(error.detail || 'Failed to create checkout session');
                    }
                    
                    const data = await response.json();
                    console.log('[Stripe Fixed] Checkout session created:', data);
                    
                    // Redirect to Stripe Checkout
                    if (data.checkout_url) {
                        console.log('[Stripe Fixed] Redirecting to Stripe checkout...');
                        window.location.href = data.checkout_url;
                    } else {
                        throw new Error('No checkout URL received');
                    }
                    
                } catch (error) {
                    console.error('[Stripe Fixed] Checkout error:', error);
                    alert('Failed to start checkout process. Please try again.');
                    
                    // Restore button state
                    button.textContent = originalText;
                    button.disabled = false;
                    button.style.opacity = '1';
                }
            });
        }
    });
    
    // Check if we were redirected here after login
    const intendedPlan = sessionStorage.getItem('intended_plan');
    if (intendedPlan && isUserAuthenticated()) {
        console.log('[Stripe Fixed] Found intended plan after login:', intendedPlan);
        // Clear the session storage
        sessionStorage.removeItem('intended_plan');
        sessionStorage.removeItem('redirect_after_login');
        
        // Find and click the appropriate button
        const planIndex = ['starter', 'professional', 'business'].indexOf(intendedPlan);
        if (planIndex !== -1 && pricingButtons[planIndex]) {
            console.log('[Stripe Fixed] Auto-clicking plan button after login');
            setTimeout(() => {
                pricingButtons[planIndex].click();
            }, 500);
        }
    }
});

// Add styles for loading state
const style = document.createElement('style');
style.textContent = `
    .pricing-cta[disabled] {
        cursor: not-allowed !important;
        transform: none !important;
    }
`;
document.head.appendChild(style);