# Authentication Fix Solution Summary

## Problem
The user reports that clicking Buy buttons on the pricing page redirects to signup even when logged in.

## Root Cause Analysis
1. The site uses multiple authentication systems:
   - `auth-global.js` - Manages navigation UI based on localStorage
   - `auth.js` - Provides BankAuth module with TokenManager
   - `stripe-integration.js` - Handles Buy button clicks

2. The authentication check in stripe-integration.js may be failing because:
   - It's checking BankAuth.TokenManager.isAuthenticated() which might return false
   - The token exists in localStorage but BankAuth doesn't recognize it
   - There's a timing issue with script loading

## Solution

### Option 1: Simple Fix (Recommended)
Update stripe-integration.js to check localStorage directly instead of relying on BankAuth:

```javascript
// In buy button click handler
const token = localStorage.getItem('access_token');
if (!token) {
    window.location.href = `/signup.html?plan=${plan}&redirect=/pricing.html`;
    return;
}
// Proceed with Stripe checkout
```

### Option 2: Fix BankAuth Integration
Ensure BankAuth.TokenManager properly reads from localStorage:

```javascript
// In auth.js TokenManager
isAuthenticated: function() {
    const token = this.getAccessToken();
    return !!token && !this.isTokenExpired(token);
}

getAccessToken: function() {
    return localStorage.getItem('access_token');
}
```

## Implementation

The simplest and most reliable fix is to update stripe-integration.js to use localStorage directly. This is what auth-global.js does and it works reliably.

Here's the complete fixed stripe-integration.js:

```javascript
// Stripe Integration - Fixed to use localStorage directly
document.addEventListener('DOMContentLoaded', () => {
    const buttons = document.querySelectorAll('.pricing-cta.primary');
    const plans = ['starter', 'professional', 'business'];
    
    buttons.forEach((button, index) => {
        const plan = plans[index];
        if (!plan) return;
        
        button.addEventListener('click', async (e) => {
            e.preventDefault();
            
            // Check authentication using localStorage directly
            const token = localStorage.getItem('access_token');
            
            if (!token) {
                // Not authenticated - redirect to signup
                window.location.href = `/signup.html?plan=${plan}&redirect=/pricing.html`;
                return;
            }
            
            // User is authenticated - create Stripe checkout
            const toggle = document.getElementById('pricingToggle');
            const billingPeriod = toggle?.classList.contains('active') ? 'yearly' : 'monthly';
            
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
                
                if (response.ok && data.checkout_url) {
                    window.location.href = data.checkout_url;
                } else {
                    throw new Error(data.detail || 'Checkout failed');
                }
            } catch (error) {
                alert('Unable to start checkout: ' + error.message);
            }
        });
    });
});
```

## Testing

1. Login at /login.html
2. Check localStorage has token: `localStorage.getItem('access_token')`
3. Go to /pricing.html
4. Click any Buy button
5. Should redirect to Stripe checkout, not signup

## Why This Works

- `auth-global.js` successfully uses localStorage to determine auth state
- The navigation UI updates correctly based on localStorage
- Using the same approach in stripe-integration.js ensures consistency
- No dependency on BankAuth module loading or initialization timing