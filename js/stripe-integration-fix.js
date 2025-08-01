// Stripe Integration for Pricing Page - FIXED

// Use v2 API endpoints to match UnifiedAuth
const STRIPE_API_BASE = (() => {
    const hostname = window.location.hostname;
    const isLocal = hostname === 'localhost' || hostname === '127.0.0.1';
    const base = isLocal ? 'http://localhost:5000' : `${window.location.protocol}//${hostname}`;
    return `${base}/api/stripe`; // Note: Stripe endpoints are under /api/stripe, not /v2/api/stripe
})();

// Initialize Stripe integration
document.addEventListener('DOMContentLoaded', async () => {
    console.log('Stripe integration initializing...');
    
    // FIX: Wait for UnifiedAuth to initialize
    const waitForAuth = async () => {
        let attempts = 0;
        while (attempts < 50) { // Wait up to 5 seconds
            if (window.UnifiedAuth && window.UnifiedAuth.initialized) {
                break;
            }
            await new Promise(resolve => setTimeout(resolve, 100));
            attempts++;
        }
    };
    
    await waitForAuth();
    
    console.log('UnifiedAuth available:', typeof window.UnifiedAuth !== 'undefined');
    
    // Check if user is authenticated
    const isAuthenticated = window.UnifiedAuth && window.UnifiedAuth.isAuthenticated();
    console.log('User authenticated:', isAuthenticated);
    
    // Get all pricing buttons
    const pricingButtons = document.querySelectorAll('.pricing-cta.primary');
    
    console.log('Found pricing buttons:', pricingButtons.length);
    
    pricingButtons.forEach((button, index) => {
        // Determine the plan based on button position
        const plans = ['starter', 'professional', 'business'];
        const plan = plans[index];
        console.log(`Setting up button ${index} for plan: ${plan}`);
        
        if (plan) {
            button.addEventListener('click', async (e) => {
                e.preventDefault();
                console.log('Buy button clicked for plan:', plan);
                
                // Check if user is authenticated (re-check at click time)
                const isAuthenticatedNow = window.UnifiedAuth && window.UnifiedAuth.isAuthenticated();
                
                if (!isAuthenticatedNow) {
                    // Redirect to signup with plan information
                    console.log('User not authenticated, redirecting to signup...');
                    sessionStorage.setItem('intended_plan', plan);
                    sessionStorage.setItem('redirect_after_login', '/pricing.html');
                    window.location.href = `/signup.html?plan=${plan}&redirect=/pricing.html`;
                    return;
                }
                
                // Get billing period (monthly or yearly)
                const toggleElement = document.getElementById('pricingToggle');
                const isYearly = toggleElement && toggleElement.classList.contains('active');
                const billingPeriod = isYearly ? 'yearly' : 'monthly';
                
                console.log('Toggle state:', toggleElement?.classList.toString());
                console.log('Is yearly?', isYearly);
                console.log('Billing period:', billingPeriod);
                
                // Show loading state
                const originalText = button.textContent;
                button.textContent = 'Processing...';
                button.disabled = true;
                
                try {
                    // Log what we're sending
                    const payload = {
                        plan: plan,
                        billing_period: billingPeriod
                    };
                    console.log('Sending to Stripe API:', payload);
                    console.log('API URL:', `${STRIPE_API_BASE}/create-checkout-session`);
                    
                    // Create checkout session
                    const response = await window.UnifiedAuth.makeAuthenticatedRequest(`${STRIPE_API_BASE}/create-checkout-session`, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify(payload)
                    });
                    
                    console.log('Stripe API response status:', response.status);
                    
                    if (!response.ok) {
                        const error = await response.json();
                        console.error('Stripe API error:', error);
                        throw new Error(error.detail || 'Failed to create checkout session');
                    }
                    
                    const data = await response.json();
                    console.log('Checkout session created:', data);
                    
                    // Redirect to Stripe Checkout
                    if (data.checkout_url) {
                        console.log('Redirecting to Stripe checkout:', data.checkout_url);
                        window.location.href = data.checkout_url;
                    } else {
                        throw new Error('No checkout URL received');
                    }
                    
                } catch (error) {
                    console.error('Checkout error:', error);
                    alert('Failed to start checkout process. Please try again.');
                    
                    // Restore button state
                    button.textContent = originalText;
                    button.disabled = false;
                }
            });
        }
    });
    
    // Add manage subscription button for authenticated users
    if (isAuthenticated) {
        checkSubscriptionStatus();
    }
});

// Check current subscription status
async function checkSubscriptionStatus() {
    try {
        const response = await window.UnifiedAuth.makeAuthenticatedRequest(`${STRIPE_API_BASE}/subscription-status`, {
            method: 'GET'
        });
        
        if (response.ok) {
            const subscription = await response.json();
            console.log('Current subscription:', subscription);
            
            // Update UI based on subscription status
            if (subscription.status === 'active') {
                // Show manage subscription button
                const ctaButtons = document.querySelectorAll('.pricing-cta.primary');
                const planIndex = ['starter', 'professional', 'business'].indexOf(subscription.plan);
                
                if (planIndex >= 0 && ctaButtons[planIndex]) {
                    const button = ctaButtons[planIndex];
                    button.textContent = 'Current Plan';
                    button.disabled = true;
                    button.classList.add('current-plan');
                    
                    // Add manage subscription button
                    const manageBtn = document.createElement('button');
                    manageBtn.className = 'pricing-cta secondary';
                    manageBtn.textContent = 'Manage Subscription';
                    manageBtn.onclick = openCustomerPortal;
                    button.parentElement.appendChild(manageBtn);
                }
            }
        }
    } catch (error) {
        console.error('Error checking subscription:', error);
    }
}

// Open Stripe customer portal
async function openCustomerPortal() {
    try {
        const button = event.target;
        const originalText = button.textContent;
        button.textContent = 'Loading...';
        button.disabled = true;
        
        const response = await window.UnifiedAuth.makeAuthenticatedRequest(`${STRIPE_API_BASE}/customer-portal`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                return_url: '/dashboard.html'
            })
        });
        
        if (!response.ok) {
            throw new Error('Failed to create portal session');
        }
        
        const data = await response.json();
        window.location.href = data.portal_url;
        
    } catch (error) {
        console.error('Portal error:', error);
        alert('Failed to open subscription management. Please try again.');
        button.textContent = 'Manage Subscription';
        button.disabled = false;
    }
}

// Handle successful payment return
if (window.location.search.includes('session_id=')) {
    const urlParams = new URLSearchParams(window.location.search);
    const sessionId = urlParams.get('session_id');
    
    if (sessionId) {
        // Show success message
        const successMessage = document.createElement('div');
        successMessage.className = 'alert alert-success';
        successMessage.innerHTML = `
            <i class="fas fa-check-circle"></i>
            <strong>Payment successful!</strong> Thank you for subscribing. You can now access all premium features.
        `;
        
        const container = document.querySelector('.container') || document.body;
        container.insertBefore(successMessage, container.firstChild);
        
        // Clear URL parameters
        window.history.replaceState({}, document.title, window.location.pathname);
    }
}

// Handle payment cancellation
if (window.location.search.includes('canceled=true')) {
    const cancelMessage = document.createElement('div');
    cancelMessage.className = 'alert alert-warning';
    cancelMessage.innerHTML = `
        <i class="fas fa-exclamation-triangle"></i>
        <strong>Payment canceled.</strong> No charges were made. Feel free to try again when you're ready.
    `;
    
    const container = document.querySelector('.container') || document.body;
    container.insertBefore(cancelMessage, container.firstChild);
    
    // Clear URL parameters
    window.history.replaceState({}, document.title, window.location.pathname);
}

// Pricing toggle functionality (if not already handled)
document.addEventListener('DOMContentLoaded', () => {
    const toggle = document.getElementById('pricingToggle');
    if (toggle && !toggle.hasAttribute('data-initialized')) {
        toggle.setAttribute('data-initialized', 'true');
        
        toggle.addEventListener('click', () => {
            toggle.classList.toggle('active');
            
            // Update prices
            const isYearly = toggle.classList.contains('active');
            document.querySelectorAll('[data-monthly-price]').forEach(el => {
                const monthlyPrice = parseInt(el.getAttribute('data-monthly-price'));
                const yearlyPrice = Math.floor(monthlyPrice * 12 * 0.8); // 20% discount
                
                if (isYearly) {
                    el.textContent = `$${yearlyPrice}/year`;
                } else {
                    el.textContent = `$${monthlyPrice}/month`;
                }
            });
            
            // Update billing period text
            document.querySelectorAll('.billing-period').forEach(el => {
                el.textContent = isYearly ? '/year' : '/month';
            });
        });
    }
});