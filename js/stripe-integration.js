// Stripe Integration for Pricing Page

// Get API base URL
const getApiBase = () => {
    if (window.API_CONFIG) {
        return window.API_CONFIG.getBaseUrl();
    }
    // Fallback to dynamic detection
    if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
        return 'http://localhost:5000';
    }
    return `${window.location.protocol}//${window.location.hostname}`;
};

const STRIPE_API_BASE = getApiBase() + '/api/stripe';

// Initialize Stripe integration
document.addEventListener('DOMContentLoaded', () => {
    // Check if user is authenticated
    const isAuthenticated = window.BankAuth && window.BankAuth.TokenManager.isAuthenticated();
    
    // Get all pricing buttons
    const pricingButtons = document.querySelectorAll('.pricing-cta.primary');
    
    pricingButtons.forEach((button, index) => {
        // Determine the plan based on button position
        const plans = ['starter', 'professional', 'business'];
        const plan = plans[index];
        
        if (plan) {
            button.addEventListener('click', async (e) => {
                e.preventDefault();
                
                // Check if user is authenticated
                if (!isAuthenticated) {
                    // Redirect to signup with plan information
                    window.location.href = `/signup.html?plan=${plan}&redirect=/pricing.html`;
                    return;
                }
                
                // Get billing period (monthly or yearly)
                const isYearly = document.getElementById('pricingToggle').classList.contains('active');
                const billingPeriod = isYearly ? 'yearly' : 'monthly';
                
                // Show loading state
                const originalText = button.textContent;
                button.textContent = 'Processing...';
                button.disabled = true;
                
                try {
                    // Create checkout session
                    const response = await fetch(`${STRIPE_API_BASE}/create-checkout-session`, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'Authorization': `Bearer ${window.BankAuth.TokenManager.getAccessToken()}`
                        },
                        body: JSON.stringify({
                            plan: plan,
                            billing_period: billingPeriod
                        })
                    });
                    
                    if (!response.ok) {
                        const error = await response.json();
                        throw new Error(error.detail || 'Failed to create checkout session');
                    }
                    
                    const data = await response.json();
                    
                    // Redirect to Stripe Checkout
                    window.location.href = data.checkout_url;
                    
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
        const response = await fetch(`${STRIPE_API_BASE}/subscription-status`, {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${window.BankAuth.TokenManager.getAccessToken()}`
            }
        });
        
        if (response.ok) {
            const status = await response.json();
            
            // If user has an active subscription, show manage button
            if (status.plan !== 'free') {
                displayManageSubscriptionButton(status);
            }
        }
    } catch (error) {
        console.error('Error checking subscription status:', error);
    }
}

// Display manage subscription button
function displayManageSubscriptionButton(status) {
    const heroSection = document.querySelector('.hero');
    if (heroSection) {
        const manageDiv = document.createElement('div');
        manageDiv.className = 'subscription-status';
        manageDiv.style.cssText = 'margin-top: 2rem; padding: 2rem; background: #f0f9ff; border-radius: 12px; text-align: center;';
        
        manageDiv.innerHTML = `
            <p style="font-size: 1.8rem; color: #0066ff; margin-bottom: 1rem;">
                Current Plan: <strong>${status.plan.charAt(0).toUpperCase() + status.plan.slice(1)}</strong>
            </p>
            <p style="font-size: 1.6rem; color: #6b7280; margin-bottom: 2rem;">
                ${status.pages_used} / ${status.pages_limit} pages used this month
            </p>
            <button id="manageSubscription" style="
                background: #0066ff;
                color: white;
                padding: 1.2rem 2.4rem;
                border: none;
                border-radius: 8px;
                font-size: 1.6rem;
                font-weight: 600;
                cursor: pointer;
                transition: all 0.2s;
            ">Manage Subscription</button>
        `;
        
        heroSection.appendChild(manageDiv);
        
        // Add click handler for manage button
        document.getElementById('manageSubscription').addEventListener('click', async () => {
            const button = document.getElementById('manageSubscription');
            button.textContent = 'Loading...';
            button.disabled = true;
            
            try {
                const response = await fetch(`${STRIPE_API_BASE}/customer-portal`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${window.BankAuth.TokenManager.getAccessToken()}`
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
        });
    }
}

// Handle successful payment return
if (window.location.search.includes('session_id=')) {
    const urlParams = new URLSearchParams(window.location.search);
    const sessionId = urlParams.get('session_id');
    
    if (sessionId) {
        // Show success message
        const heroSection = document.querySelector('.hero');
        if (heroSection) {
            const successDiv = document.createElement('div');
            successDiv.style.cssText = 'margin-top: 2rem; padding: 2rem; background: #d1fae5; border-radius: 12px; text-align: center; color: #065f46;';
            successDiv.innerHTML = '<h3 style="font-size: 2.4rem; margin-bottom: 1rem;">🎉 Payment Successful!</h3><p style="font-size: 1.8rem;">Your subscription is now active. Redirecting to dashboard...</p>';
            heroSection.appendChild(successDiv);
            
            // Redirect to dashboard after 3 seconds
            setTimeout(() => {
                window.location.href = '/dashboard.html';
            }, 3000);
        }
    }
}