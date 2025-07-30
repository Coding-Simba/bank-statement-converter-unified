// Stripe Integration - Minimal Fix Using localStorage Directly

document.addEventListener('DOMContentLoaded', () => {
    console.log('[Stripe] Initializing payment buttons...');
    
    // Get all buy buttons
    const buttons = document.querySelectorAll('.pricing-cta.primary');
    const plans = ['starter', 'professional', 'business'];
    
    buttons.forEach((button, index) => {
        const plan = plans[index];
        if (!plan) return;
        
        // Remove any existing handlers by cloning
        const newButton = button.cloneNode(true);
        button.parentNode.replaceChild(newButton, button);
        
        // Add click handler
        newButton.addEventListener('click', async (e) => {
            e.preventDefault();
            e.stopPropagation();
            
            console.log('[Stripe] Buy clicked for:', plan);
            
            // Check authentication using localStorage (same as auth-global.js)
            const token = localStorage.getItem('access_token');
            
            if (!token) {
                console.log('[Stripe] No token, redirecting to signup');
                window.location.href = `/signup.html?plan=${plan}&redirect=/pricing.html`;
                return;
            }
            
            console.log('[Stripe] Token found, creating checkout session');
            
            // Get billing period
            const toggle = document.getElementById('pricingToggle');
            const billingPeriod = toggle?.classList.contains('active') ? 'yearly' : 'monthly';
            
            // Show loading
            const originalText = newButton.textContent;
            newButton.textContent = 'Processing...';
            newButton.disabled = true;
            
            try {
                const response = await fetch('/api/stripe/create-checkout-session', {
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
                
                const data = await response.json();
                console.log('[Stripe] Response:', data);
                
                if (response.ok && data.checkout_url) {
                    console.log('[Stripe] Redirecting to:', data.checkout_url);
                    window.location.href = data.checkout_url;
                } else {
                    throw new Error(data.detail || 'Checkout failed');
                }
            } catch (error) {
                console.error('[Stripe] Error:', error);
                alert('Unable to start checkout. Please try again.');
                
                // Restore button
                newButton.textContent = originalText;
                newButton.disabled = false;
            }
        });
    });
    
    // Check subscription status if logged in
    const token = localStorage.getItem('access_token');
    if (token) {
        checkSubscriptionStatus(token);
    }
});

// Check subscription status
async function checkSubscriptionStatus(token) {
    try {
        const response = await fetch('/api/stripe/subscription-status', {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        
        if (response.ok) {
            const status = await response.json();
            console.log('[Stripe] Subscription:', status);
            
            if (status.plan && status.plan !== 'free') {
                displaySubscriptionInfo(status, token);
            }
        }
    } catch (error) {
        console.error('[Stripe] Error checking subscription:', error);
    }
}

// Display subscription info
function displaySubscriptionInfo(status, token) {
    const hero = document.querySelector('.hero');
    if (!hero) return;
    
    const div = document.createElement('div');
    div.style.cssText = 'margin: 2rem 0; padding: 2rem; background: #f0f9ff; border-radius: 12px; text-align: center;';
    div.innerHTML = `
        <p style="font-size: 1.8rem; color: #0066ff; margin-bottom: 1rem;">
            Current Plan: <strong>${status.plan.charAt(0).toUpperCase() + status.plan.slice(1)}</strong>
        </p>
        <p style="font-size: 1.6rem; color: #6b7280; margin-bottom: 2rem;">
            ${status.pages_used || 0} / ${status.pages_limit || '∞'} pages used
        </p>
        <button onclick="manageSubscription('${token}')" style="
            background: #0066ff; color: white; padding: 1rem 2rem;
            border: none; border-radius: 8px; font-size: 1.6rem;
            font-weight: 600; cursor: pointer;
        ">Manage Subscription</button>
    `;
    hero.appendChild(div);
}

// Manage subscription
window.manageSubscription = async function(token) {
    try {
        const response = await fetch('/api/stripe/customer-portal', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({ return_url: '/dashboard.html' })
        });
        
        const data = await response.json();
        if (data.portal_url) {
            window.location.href = data.portal_url;
        }
    } catch (error) {
        alert('Unable to open subscription management.');
    }
};