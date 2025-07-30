# Fix Authentication Flow - Complete Solution

## Problem Analysis

The user reports that clicking Buy buttons redirects to signup even when logged in. After analyzing the code, I've identified several issues:

1. **Script Loading Order**: `stripe-integration.js` may be loading before `auth.js`, causing `window.BankAuth` to be undefined
2. **Authentication Check Timing**: The authentication check happens at page load, not at button click time
3. **Token Management**: There may be inconsistency between localStorage and BankAuth.TokenManager
4. **Event Handler Conflicts**: Multiple event handlers may be interfering with each other

## Solution

### 1. Update pricing.html to ensure correct script loading order

```html
<!-- At the bottom of pricing.html, before closing </body> -->
<script src="/js/api-config.js"></script>
<script src="/js/auth.js"></script>
<script>
    // Wait for auth.js to initialize
    if (typeof window.BankAuth === 'undefined') {
        console.error('BankAuth not loaded! Authentication will not work properly.');
    }
</script>
<script src="/js/stripe-integration.js?v=6"></script>
```

### 2. Update stripe-integration.js with the working version

The working version includes:
- Proper authentication checking at button click time
- Extensive logging for debugging
- Fallback to localStorage if BankAuth is not available
- Better error handling

### 3. Update auth.js to ensure it exports BankAuth properly

Make sure auth.js ends with:
```javascript
window.BankAuth = {
    TokenManager: TokenManager,
    AuthUI: AuthUI,
    init: init
};
```

### 4. Test the fix

1. Clear browser cache and localStorage
2. Login at https://bankcsvconverter.com/login.html
3. Navigate to https://bankcsvconverter.com/pricing.html
4. Open browser console and run:
   ```javascript
   localStorage.getItem('access_token')  // Should return token
   window.BankAuth.TokenManager.isAuthenticated()  // Should return true
   ```
5. Click any Buy button - should redirect to Stripe, not signup

## Deployment Steps

1. SSH to server and backup current files:
   ```bash
   cd /home/ubuntu/bank-statement-converter/frontend
   cp js/stripe-integration.js js/stripe-integration-backup.js
   cp pricing.html pricing-backup.html
   ```

2. Upload the working stripe-integration.js:
   ```bash
   # Copy stripe-integration-working.js to js/stripe-integration.js
   ```

3. Update pricing.html to ensure correct script order

4. Clear CloudFlare cache if needed

5. Test immediately after deployment

## Verification

Run this in browser console on pricing page:
```javascript
// Check auth state
console.log('Token:', localStorage.getItem('access_token'));
console.log('BankAuth:', typeof window.BankAuth);
console.log('Authenticated:', window.BankAuth?.TokenManager?.isAuthenticated());

// Test buy button
document.querySelector('.pricing-cta.primary').click();
// Should either go to Stripe (if logged in) or signup (if not)
```