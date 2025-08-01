# E2E Stripe Checkout Test - Manual Testing Guide

## Test Setup
- User: test-20250801-134232@example.com (already logged in)
- Target: https://bankcsvconverter.com/pricing.html
- Goal: Test complete Stripe checkout flow

## Current Pricing Plans (as of current pricing.html)
- **Starter**: $30/month (not $9.99 as mentioned)
- **Professional**: $60/month (Featured/Most Popular)
- **Business**: $99/month

**Note**: The pricing page doesn't have a "Pro" plan at $9.99/mo. The closest is "Professional" at $60/mo.

## Manual Test Steps

### Step 1: Navigate to Pricing Page
1. Open browser and go to: `https://bankcsvconverter.com/pricing.html`
2. **Take Screenshot**: Save as `01_pricing_page_loaded.png`
3. Verify user is logged in (check for any auth indicators)

### Step 2: Analyze Pricing Plans
1. Identify the three plans on the page:
   - Starter ($30/mo)
   - Professional ($60/mo) - Featured
   - Business ($99/mo)
2. **Take Screenshot**: Save as `02_pricing_plans_overview.png`

### Step 3: Test Professional Plan (closest to requested Pro plan)
1. Click on the "Buy" button for the **Professional** plan ($60/mo)
2. **Monitor Network Traffic**: Open DevTools Network tab before clicking
3. Look for requests to:
   - `/api/stripe/create-checkout-session`
   - Any authentication headers
4. **Take Screenshot**: Save as `03_professional_buy_clicked.png`

### Step 4: Monitor Stripe Checkout Session Creation
Watch for these network requests:
```
POST /api/stripe/create-checkout-session
Headers:
- Authorization: Bearer [token]
- Content-Type: application/json

Body:
{
  "plan": "professional",
  "billing_period": "monthly"
}
```

### Step 5: Stripe Checkout Page
1. Should redirect to Stripe checkout page
2. **Take Screenshot**: Save as `04_stripe_checkout_page.png`
3. Fill in test card details:
   - **Card Number**: 4242 4242 4242 4242
   - **Expiry**: 12/25
   - **CVC**: 123
   - **ZIP**: 10001

### Step 6: Complete Payment
1. Click "Pay" or "Subscribe" button
2. **Take Screenshot**: Save as `05_payment_processing.png`
3. Wait for payment to complete

### Step 7: Post-Payment Monitoring
1. Monitor for redirect back to site
2. Look for success parameters in URL (e.g., `?session_id=...`)
3. **Take Screenshot**: Save as `06_payment_success.png`

### Step 8: Verify Subscription Status
1. Check if redirected to dashboard or shows success message
2. Look for subscription status display
3. **Take Screenshot**: Save as `07_subscription_active.png`

## Expected Network Flow

### 1. Initial Checkout Request
```javascript
fetch('/api/stripe/create-checkout-session', {
  method: 'POST',
  headers: {
    'Authorization': 'Bearer [access_token]',
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    plan: 'professional',
    billing_period: 'monthly'
  })
})
```

### 2. Expected Response
```json
{
  "checkout_url": "https://checkout.stripe.com/pay/cs_test_...",
  "session_id": "cs_test_..."
}
```

### 3. Post-Payment Callback
After successful payment, Stripe should redirect to:
```
https://bankcsvconverter.com/pricing.html?session_id=cs_test_...
```

## Potential Issues to Watch For

1. **Authentication Issues**:
   - Token not present in Authorization header
   - User not authenticated, redirected to signup

2. **API Errors**:
   - 401 Unauthorized
   - 404 Not Found (endpoint doesn't exist)
   - 500 Internal Server Error

3. **Stripe Configuration Issues**:
   - Invalid Stripe keys
   - Webhook not configured properly
   - Wrong redirect URLs

4. **Frontend Issues**:
   - JavaScript errors in console
   - Button not responding to clicks
   - Wrong plan data being sent

## Debug Information to Collect

### Browser Console Logs
Look for these console messages:
```
Stripe integration initializing...
BankAuth available: true
User authenticated: true
Found pricing buttons: 3
Setting up button 0 for plan: starter
Setting up button 1 for plan: professional
Setting up button 2 for plan: business
Buy button clicked for plan: professional
Sending to Stripe API: {plan: "professional", billing_period: "monthly"}
```

### Network Request Details
Monitor these endpoints:
- `/api/stripe/create-checkout-session`
- `/api/stripe/subscription-status`
- `/api/stripe/customer-portal`

### Error Scenarios
If errors occur, capture:
1. Console error messages
2. Network response status and body
3. User-facing error messages
4. Screenshots of error states

## Alternative Test Plans

Since the pricing page doesn't have a $9.99 Pro plan, you can:

1. **Test Starter Plan** ($30/mo) instead
2. **Modify pricing.html** to add a $9.99 Pro plan temporarily
3. **Test with yearly billing** (toggle the switch first)

## Success Criteria

- ✅ User can click pricing plan buy button
- ✅ Stripe checkout session is created successfully
- ✅ User is redirected to Stripe checkout page
- ✅ Test card payment completes successfully
- ✅ User is redirected back to site with success indication
- ✅ Subscription status is updated and visible

## Automated Testing Script (Optional)

If you want to create an automated version later, use tools like:
- **Playwright** or **Puppeteer** for browser automation
- **Cypress** for E2E testing
- **Selenium** for cross-browser testing

This would allow you to automate the entire flow programmatically.