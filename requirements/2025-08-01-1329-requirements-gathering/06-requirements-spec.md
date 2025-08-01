# E2E Testing Requirements Specification

**Date:** 2025-08-01  
**Time:** 13:37

## Problem Statement
The bank statement converter application needs comprehensive end-to-end testing to verify that:
1. User registration flow works correctly
2. Payment processing through Stripe functions properly
3. Authentication persists across the entire website and new tabs
4. Logout properly clears authentication across all tabs

## Solution Overview
Perform automated browser testing using Chrome MCP Server to simulate real user interactions and verify the complete user journey from registration through payment to authenticated usage.

## Functional Requirements

### 1. User Registration Test
- Navigate to https://bankcsvconverter.com/signup.html
- Generate unique test email: test-[timestamp]@example.com
- Fill registration form with test data
- Submit form and verify successful registration
- Confirm redirect to dashboard or login page

### 2. Stripe Payment Test
- Navigate to pricing page
- Select a subscription plan (Pro or Business)
- Click purchase/subscribe button
- Enter Stripe test card: 4242 4242 4242 4242
- Complete checkout flow
- Verify subscription activation

### 3. Authentication Persistence Test
- After login, open multiple tabs to different pages:
  - Dashboard (/dashboard.html)
  - PDF Converter (/convert-pdf.html)
  - Transaction Analyzer (/analyze-transactions.html)
  - Settings (/settings.html)
- Verify user remains logged in on all pages
- Check that user info displays correctly
- Confirm auth cookies are present and marked HttpOnly/Secure

### 4. Cross-Tab Logout Test
- With multiple tabs open and logged in
- Perform logout action in one tab
- Verify all other tabs reflect logged out state
- Confirm cookies are cleared

## Technical Requirements

### Browser Automation Setup
- Use Chrome MCP Server with streamable HTTP connection
- Connect to http://127.0.0.1:12306/mcp
- Utilize screenshot tool for visual verification
- Use network monitoring to verify API calls

### Test Data
- Email format: test-YYYYMMDD-HHMMSS@example.com
- Password: TestPass123!
- Name: Test User
- Stripe test card: 4242 4242 4242 4242
- Expiry: Any future date
- CVC: Any 3 digits
- ZIP: Any valid ZIP

### Cookie Verification
- Check for presence of auth cookies
- Verify HttpOnly flag is set
- Verify Secure flag is set (on HTTPS)
- Confirm SameSite attribute

## Implementation Hints

### Key Selectors
- Registration form: Look for signup form inputs
- Login elements: Email/password fields
- Stripe iframe: Payment form embedded in pricing page
- Logout button: Usually in navigation or dropdown

### API Endpoints to Monitor
- POST /v2/auth/register
- POST /v2/auth/login
- POST /v2/auth/logout
- GET /v2/auth/verify
- POST /v2/stripe/create-checkout-session

### Expected Behaviors
- Successful registration returns JWT cookie
- Login redirects to dashboard
- Stripe checkout opens in modal or new tab
- Logout clears all auth state

## Acceptance Criteria

1. **Registration Success**
   - New account created with unique email
   - User data stored in backend
   - Auth cookie set

2. **Payment Processing**
   - Stripe checkout completes without errors
   - Subscription status updated
   - User has access to paid features

3. **Authentication Persistence**
   - User stays logged in across all pages
   - New tabs recognize auth state
   - No unexpected logouts

4. **Proper Logout**
   - All tabs reflect logout state
   - Cookies cleared completely
   - Redirect to home/login page

## Assumptions
- Chrome MCP Server is properly installed and running
- Test is performed on production site (bankcsvconverter.com)
- Stripe is in test mode on the site
- Network connection is stable

## Documentation Requirements
- Screenshot key steps (registration, payment, logged-in state)
- Log any errors or unexpected behaviors
- Note response times for critical operations
- Document any UI/UX issues discovered