/**
 * WORKING Stripe Integration
 * Uses correct price_id format expected by backend
 */

// API Configuration
const STRIPE_API_BASE = `${window.location.protocol}//${window.location.hostname}/api/stripe`;

// Price ID mapping - these are your actual Stripe price IDs
const PRICE_IDS = {
    starter: {
        monthly: 'price_1RqZtaKwQLBjGTW9w20V3Hst',
        yearly: 'price_1RqZubKwQLBjGTW9deSoEAWV'
    },
    professional: {
        monthly: 'price_1RqZv9KwQLBjGTW9tE0aY9R9',
        yearly: 'price_1RqZvXKwQLBjGTW9jqS3dhr8'
    },
    business: {
        monthly: 'price_1RqZvrKwQLBjGTW9s0sfMhFN',
        yearly: 'price_1RqZwFKwQLBjGTW9JIuiSSm5'
    }
};

console.log('Stripe integration loading...');

function initializeStripe() {
    console.log('Initializing Stripe integration...');
    
    // Check auth
    const isAuth = window.UnifiedAuth && 
                  window.UnifiedAuth.isAuthenticated && 
                  window.UnifiedAuth.isAuthenticated();
    
    console.log('User authenticated:', isAuth);
    
    // Setup buttons
    setupPricingButtons();
    
    // Handle success return
    handlePaymentSuccess();
}

function setupPricingButtons() {
    const buttons = document.querySelectorAll('.pricing-cta.primary');
    console.log('Found pricing buttons:', buttons.length);
    
    buttons.forEach((button, index) => {
        const plan = ['starter', 'professional', 'business'][index];
        button.setAttribute('data-plan', plan);
        
        button.addEventListener('click', async (e) => {
            e.preventDefault();
            console.log('Buy button clicked for plan:', plan);
            
            // Check authentication
            const token = localStorage.getItem('access_token');
            const isAuth = window.UnifiedAuth && 
                          window.UnifiedAuth.isAuthenticated && 
                          window.UnifiedAuth.isAuthenticated();
            
            if (!isAuth || !token) {
                console.log('Not authenticated, redirecting to signup...');
                window.location.href = `/signup.html?plan=${plan}&redirect=/pricing.html`;
                return;
            }
            
            // Get billing period
            const toggle = document.getElementById('pricingToggle');
            const isYearly = toggle && toggle.classList.contains('active');
            const billingPeriod = isYearly ? 'yearly' : 'monthly';
            
            // Get the correct price ID
            const priceId = PRICE_IDS[plan]?.[billingPeriod];
            
            if (!priceId) {
                alert('This plan is not yet configured. Please contact support.');
                return;
            }
            
            console.log('Using price ID:', priceId);
            
            // Update button state
            const originalText = button.textContent;
            button.textContent = 'Processing...';
            button.disabled = true;
            button.style.opacity = '0.7';
            
            try {
                // Create checkout session
                const response = await fetch(`${STRIPE_API_BASE}/create-checkout-session`, {
                    method: 'POST',
                    credentials: 'include',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${token}`
                    },
                    body: JSON.stringify({
                        price_id: priceId,
                        success_url: `${window.location.origin}/pricing.html?payment=success`,
                        cancel_url: `${window.location.origin}/pricing.html?payment=cancelled`
                    })
                });
                
                console.log('Response status:', response.status);
                
                if (!response.ok) {
                    const errorText = await response.text();
                    console.error('Error response:', errorText);
                    
                    let errorMessage = 'Failed to create checkout session';
                    try {
                        const errorData = JSON.parse(errorText);
                        errorMessage = errorData.detail || errorMessage;
                    } catch (e) {
                        errorMessage = `Server error: ${response.status}`;
                    }
                    
                    throw new Error(errorMessage);
                }
                
                const data = await response.json();
                console.log('Checkout session created:', data);
                
                if (data.checkout_url || data.url) {
                    // Redirect to Stripe checkout
                    window.location.href = data.checkout_url || data.url;
                } else {
                    throw new Error('No checkout URL received');
                }
                
            } catch (error) {
                console.error('Checkout error:', error);
                alert(`Error: ${error.message}`);
                
                // Restore button
                button.textContent = originalText;
                button.disabled = false;
                button.style.opacity = '1';
            }
        });
    });
}

function handlePaymentSuccess() {
    const urlParams = new URLSearchParams(window.location.search);
    
    if (urlParams.get('payment') === 'success') {
        // Show success message
        const container = document.querySelector('.hero-section') || document.querySelector('.container');
        if (container) {
            const message = document.createElement('div');
            message.style.cssText = `
                background: #10b981;
                color: white;
                padding: 16px 24px;
                border-radius: 8px;
                margin: 20px auto;
                max-width: 600px;
                text-align: center;
                font-weight: 500;
            `;
            message.textContent = '✅ Payment successful! Your subscription is now active.';
            container.insertBefore(message, container.firstChild);
        }
        
        // Clean URL
        window.history.replaceState({}, document.title, window.location.pathname);
    }
}

// Initialize when ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeStripe);
} else {
    setTimeout(initializeStripe, 100);
}

console.log('Stripe integration loaded');

// IMPORTANT: You need to update the PRICE_IDS object above with your actual Stripe price IDs
// You can find these in your Stripe dashboard under Products > [Your Product] > Pricing
// They look like: price_1AbCdEfGhIjKlMnOpQrStUvW