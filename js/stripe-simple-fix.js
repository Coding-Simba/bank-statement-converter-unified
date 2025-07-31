// Simple Stripe Fix - Direct API calls without auth.js interference

(function() {
    console.log('[Stripe Simple Fix] Loading...');
    
    // Store original fetch to bypass auth.js
    const originalFetch = window.fetch.bind(window);
    
    // Get API base
    const API_BASE = (() => {
        const hostname = window.location.hostname;
        if (hostname === 'localhost' || hostname === '127.0.0.1') {
            return 'http://localhost:5000';
        }
        return `${window.location.protocol}//${hostname}`;
    })();
    
    // Override stripe integration to use original fetch
    document.addEventListener('DOMContentLoaded', () => {
        // Wait a bit for other scripts to load
        setTimeout(() => {
            console.log('[Stripe Simple Fix] Overriding Stripe buttons...');
            
            const pricingButtons = document.querySelectorAll('.pricing-cta.primary');
            
            pricingButtons.forEach((button, index) => {
                if (!button.textContent.includes('Buy')) return;
                
                const plans = ['starter', 'professional', 'business'];
                const plan = plans[index];
                
                if (!plan) return;
                
                // Remove existing listeners by cloning
                const newButton = button.cloneNode(true);
                button.parentNode.replaceChild(newButton, button);
                
                // Add new click handler
                newButton.addEventListener('click', async (e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    
                    console.log('[Stripe Simple Fix] Buy clicked for:', plan);
                    
                    // Check auth
                    const token = localStorage.getItem('access_token');
                    const userData = localStorage.getItem('user_data') || localStorage.getItem('user');
                    
                    if (!token || !userData) {
                        console.log('[Stripe Simple Fix] Not authenticated, redirecting...');
                        sessionStorage.setItem('intended_plan', plan);
                        sessionStorage.setItem('redirect_after_login', window.location.href);
                        window.location.href = '/login.html';
                        return;
                    }
                    
                    // Get billing period
                    const toggleElement = document.getElementById('pricingToggle');
                    const isYearly = toggleElement && toggleElement.classList.contains('active');
                    const billingPeriod = isYearly ? 'yearly' : 'monthly';
                    
                    // Show loading
                    const originalText = newButton.textContent;
                    newButton.textContent = 'Processing...';
                    newButton.disabled = true;
                    
                    try {
                        console.log('[Stripe Simple Fix] Making direct API call...');
                        
                        // Use original fetch to bypass auth.js
                        const response = await originalFetch(`${API_BASE}/api/stripe/create-checkout-session`, {
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
                        
                        console.log('[Stripe Simple Fix] Response:', response.status);
                        
                        if (response.status === 401) {
                            // Token expired, need to login
                            console.log('[Stripe Simple Fix] Token expired, clearing auth...');
                            localStorage.clear();
                            sessionStorage.setItem('intended_plan', plan);
                            sessionStorage.setItem('redirect_after_login', window.location.href);
                            window.location.href = '/login.html';
                            return;
                        }
                        
                        if (!response.ok) {
                            const error = await response.json();
                            throw new Error(error.detail || 'Failed to create checkout session');
                        }
                        
                        const data = await response.json();
                        console.log('[Stripe Simple Fix] Success! Redirecting to checkout...');
                        
                        if (data.checkout_url) {
                            window.location.href = data.checkout_url;
                        } else {
                            throw new Error('No checkout URL received');
                        }
                        
                    } catch (error) {
                        console.error('[Stripe Simple Fix] Error:', error);
                        alert('Failed to start checkout. Please try logging in again.');
                        
                        // Restore button
                        newButton.textContent = originalText;
                        newButton.disabled = false;
                    }
                });
            });
            
            console.log('[Stripe Simple Fix] Buttons overridden successfully');
        }, 500);
    });
})();