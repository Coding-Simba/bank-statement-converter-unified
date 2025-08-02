/**
 * Simple Stripe Integration - Works with any auth system
 */

const STRIPE_API_BASE = (() => {
    const hostname = window.location.hostname;
    return hostname === 'localhost' || hostname === '127.0.0.1'
        ? 'http://localhost:5000/api/stripe'
        : `${window.location.protocol}//${hostname}/api/stripe`;
})();

console.log('[Stripe] Simple integration loading...');

// Initialize when DOM is ready
function initializeStripe() {
    console.log('[Stripe] Initializing simple Stripe integration...');
    
    // Setup pricing buttons
    const buttons = document.querySelectorAll('.pricing-cta.primary');
    console.log('[Stripe] Found buy buttons:', buttons.length);
    
    buttons.forEach((button, index) => {
        // Get plan from data attribute or infer from position
        const plan = button.dataset.plan || ['starter', 'professional', 'business'][index];
        
        console.log(`[Stripe] Setting up button for plan: ${plan}`);
        
        button.addEventListener('click', async (e) => {
            e.preventDefault();
            console.log(`[Stripe] Buy button clicked for plan: ${plan}`);
            
            // Check authentication - try multiple methods
            let isAuth = false;
            
            // Method 1: Check localStorage for token
            if (localStorage.getItem('access_token')) {
                isAuth = true;
                console.log('[Stripe] Auth detected via localStorage token');
            }
            
            // Method 2: Check CookieAuth if available
            if (!isAuth && window.CookieAuth && window.CookieAuth.isAuthenticated) {
                isAuth = window.CookieAuth.isAuthenticated();
                console.log('[Stripe] Auth detected via CookieAuth');
            }
            
            // Method 3: Check UnifiedAuth if available
            if (!isAuth && window.UnifiedAuth && window.UnifiedAuth.isAuthenticated) {
                isAuth = window.UnifiedAuth.isAuthenticated();
                console.log('[Stripe] Auth detected via UnifiedAuth');
            }
            
            if (!isAuth) {
                console.log('[Stripe] User not authenticated, redirecting to signup...');
                window.location.href = `/signup.html?plan=${plan}&redirect=/pricing.html`;
                return;
            }
            
            // Get billing period
            const toggle = document.getElementById('pricingToggle');
            const isYearly = toggle && toggle.classList.contains('active');
            const billingPeriod = isYearly ? 'yearly' : 'monthly';
            
            console.log(`[Stripe] Creating checkout for ${plan} - ${billingPeriod}`);
            
            // Update button state
            const originalText = button.textContent;
            button.textContent = 'Processing...';
            button.disabled = true;
            button.style.opacity = '0.7';
            
            try {
                // Prepare request based on auth method
                const headers = {
                    'Content-Type': 'application/json'
                };
                
                // Add auth header if using JWT
                const token = localStorage.getItem('access_token');
                if (token) {
                    headers['Authorization'] = `Bearer ${token}`;
                }
                
                // Make request (cookies will be included automatically)
                const response = await fetch(`${STRIPE_API_BASE}/create-checkout-session`, {
                    method: 'POST',
                    credentials: 'include', // Include cookies
                    headers: headers,
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
                console.error('[Stripe] Error:', error);
                alert(`Error: ${error.message}`);
                
                // Restore button
                button.textContent = originalText;
                button.disabled = false;
                button.style.opacity = '';
            }
        });
    });
    
    // Handle payment success
    const params = new URLSearchParams(window.location.search);
    if (params.get('payment') === 'success') {
        console.log('[Stripe] Payment successful!');
        
        const message = document.createElement('div');
        message.style.cssText = `
            background: #10b981;
            color: white;
            padding: 16px;
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

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeStripe);
} else {
    // DOM already loaded
    initializeStripe();
}

// Also initialize when auth systems are ready
window.addEventListener('unifiedauth:ready', initializeStripe);
window.addEventListener('cookie-auth-ready', initializeStripe);

console.log('[Stripe] Simple integration loaded');