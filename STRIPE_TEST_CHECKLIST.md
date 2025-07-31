# Stripe Integration Test Checklist

## Pre-Test Setup
- [ ] Open Chrome in Incognito Mode (Cmd+Shift+N)
- [ ] Open Developer Console (Cmd+Option+J)
- [ ] Clear site data: Application > Storage > Clear site data

## Test Flow

### 1. Pricing Page Initial Load
Navigate to: https://bankcsvconverter.com/pricing.html

Expected Console Output:
```
[Auth Fixed] Initializing robust authentication...
[Auth Fixed] Checking authentication state...
[Auth Fixed] No authentication data found
[Stripe Complete] Starting...
[Stripe Complete] On pricing page, setting up buy buttons...
[Stripe Complete] Found buttons: 3
```

### 2. Click Buy Button
Click any "Buy" button (e.g., Starter plan)

Expected Console Output:
```
[Stripe Complete] Buy clicked for plan: starter
[Stripe Complete] Not authenticated, saving state and redirecting...
```

Expected Behavior:
- Redirected to /login.html
- SessionStorage should contain:
  - `redirect_after_stripe`: "https://bankcsvconverter.com/pricing.html"
  - `stripe_plan`: "starter"

### 3. Login Page
On login page, check console for:
```
[Force Auth] Initializing...
[Auth Login Fix] Initializing...
[Auth Login Fix] Found saved redirect: https://bankcsvconverter.com/pricing.html
```

### 4. Login Process
Enter credentials and submit

Expected Console Output:
```
[Force Auth] Login form submitted
[Force Auth] Login API call successful
[Force Auth] Storing access_token
[Force Auth] Storing refresh_token
[Force Auth] Storing user data
[Force Auth] Redirecting to: /pricing.html
```

### 5. Back on Pricing Page
After redirect, check for:
```
[Stripe Complete] Found saved plan after login: starter
[Stripe Complete] Auto-clicking plan button...
[Stripe Complete] Buy clicked for plan: starter
[Stripe Complete] Authenticated, proceeding with checkout...
[Stripe Complete] Making API call to create checkout session...
[Stripe Complete] Success! Redirecting to Stripe checkout...
```

## Debug Commands

Paste these in console to check state:

### Check Authentication State
```javascript
console.log('Auth State:', {
    access_token: localStorage.getItem('access_token') ? 'EXISTS' : 'MISSING',
    refresh_token: localStorage.getItem('refresh_token') ? 'EXISTS' : 'MISSING',
    user_data: localStorage.getItem('user_data') ? 'EXISTS' : 'MISSING'
});
```

### Check Session Storage
```javascript
console.log('Session Storage:', {
    redirect_after_stripe: sessionStorage.getItem('redirect_after_stripe'),
    stripe_plan: sessionStorage.getItem('stripe_plan')
});
```

### Force Clear Everything
```javascript
localStorage.clear();
sessionStorage.clear();
console.log('All storage cleared');
```

## Common Issues

1. **Still redirecting to dashboard after login**
   - Check if `[Force Auth] Redirecting to:` shows pricing URL
   - Verify sessionStorage has redirect URL before login

2. **401 Error on Stripe API**
   - Check if tokens exist after login
   - Look for `[Force Auth] Storing access_token` message

3. **Buy button not auto-clicking**
   - Check for `[Stripe Complete] Found saved plan after login`
   - Verify stripe_plan is in sessionStorage

## Success Criteria
- [ ] Click Buy → Redirected to login
- [ ] Login → Redirected back to pricing (NOT dashboard)
- [ ] Buy button auto-clicks
- [ ] Redirected to Stripe checkout page