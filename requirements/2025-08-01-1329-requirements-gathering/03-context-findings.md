# Context Findings

**Date:** 2025-08-01  
**Time:** 13:34

## Architecture Overview
- **Frontend**: HTML pages with vanilla JavaScript, using auth-unified.js for authentication
- **Backend**: FastAPI (Python) running on port 5000
- **Production**: Deployed on AWS Lightsail (3.235.19.83) with Cloudflare (bankcsvconverter.com)
- **Authentication**: HTTP-only cookie-based JWT authentication system
- **Payment**: Stripe integration for subscription plans

## Key Files for Testing

### Authentication Files
- **signup.html** - User registration page
- **login.html** - User login page
- **js/auth-unified.js** - Main authentication script handling cookies and persistence
- **backend/api/auth_cookie.py** - Cookie-based auth endpoints

### Payment Integration
- **pricing.html** - Pricing plans page
- **js/simple_stripe_handler.js** - Stripe payment handling
- **js/stripe-cookie-auth.js** - Stripe with auth integration
- **backend/api/stripe_payments.py** - Stripe backend endpoints

### User Pages
- **dashboard.html** - User dashboard after login
- **convert-pdf.html** - Main PDF conversion tool
- **analyze-transactions.html** - Transaction analysis tool
- **settings.html** - User account settings

## Authentication Flow Details
1. User registers via signup.html
2. Auth-unified.js handles form submission to backend
3. Backend creates JWT token stored as HTTP-only cookie
4. Frontend caches user data in localStorage for UI updates
5. Token refresh happens automatically every 25 minutes

## Stripe Integration Flow
1. User selects plan on pricing.html
2. JavaScript initiates Stripe checkout
3. After payment, backend updates user subscription
4. User redirected to dashboard with active plan

## Pages to Test for Login Persistence
1. Main pages: index.html, dashboard.html, convert-pdf.html
2. Tool pages: analyze-transactions.html, merge-statements.html, split-by-date.html
3. Info pages: pricing.html, features.html, blog.html
4. Account pages: settings.html

## Known Issues from CLAUDE.md
- Authentication persistence issues were fixed with auth-fixed.js
- Some conflicting auth scripts were removed
- Users were getting logged out when navigating between pages (now fixed)

## Test Considerations
- Production site uses HTTPS and Cloudflare
- Test mode Stripe keys should be used for payment testing
- Cookie domain settings may affect persistence across subdomains
- CSRF token required for authenticated API calls