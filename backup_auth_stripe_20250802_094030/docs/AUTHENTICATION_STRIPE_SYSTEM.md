# Bank Statement Converter - Authentication & Stripe System Documentation

## Overview
This backup contains the complete authentication and Stripe payment integration system as of August 2, 2025.

## Authentication System

### Cookie-Based Authentication (Primary)
- **Frontend**: `/js/auth-cookie.js`
- **Backend**: `/backend/api/auth_cookie.py`
- Uses httpOnly secure cookies for authentication
- CSRF protection enabled
- Similar to Google/Facebook authentication

### JWT Authentication (Legacy, for compatibility)
- **Frontend**: `/js/auth-unified.js`
- **Backend**: `/backend/api/auth.py`
- Uses Bearer tokens stored in localStorage
- Being phased out in favor of cookie auth

### Key Files

#### Frontend JavaScript
1. **auth-cookie.js** - Main cookie-based authentication
   - Login/Signup/Logout functionality
   - CSRF token management
   - Automatic auth state checking
   - Cross-tab synchronization

2. **auth-unified.js** - Legacy JWT authentication
   - Bearer token management
   - API request wrappers
   - User state management

3. **api-config.js** - API endpoint configuration
   - Base URL configuration
   - Environment detection

#### Backend Python
1. **api/auth_cookie.py** - Cookie authentication endpoints
   - `/v2/api/auth/login` - Login with cookies
   - `/v2/api/auth/register` - Register new user
   - `/v2/api/auth/logout` - Clear auth cookies
   - `/v2/api/auth/me` - Get current user
   - `/v2/api/auth/refresh` - Refresh tokens
   - `/v2/api/auth/csrf` - Get CSRF token

2. **api/auth.py** - JWT authentication endpoints
   - `/api/auth/login` - JWT login
   - `/api/auth/register` - JWT registration
   - `/api/auth/refresh` - Token refresh

3. **middleware/auth_middleware.py** - JWT authentication middleware
4. **middleware/csrf_middleware.py** - CSRF protection
5. **utils/auth.py** - Authentication utilities
6. **config/jwt_config.py** - JWT configuration

## Stripe Integration

### Key Files

#### Frontend JavaScript
1. **stripe-dual-auth.js** - Works with both auth systems
   - Checks both JWT and cookie authentication
   - Handles monthly/yearly pricing toggle
   - Creates checkout sessions

2. **stripe-cookie-integration.js** - Cookie-only Stripe
3. **stripe-integration.js** - Original Stripe integration
4. **stripe-cookie.js** - Cookie-based Stripe handlers
5. **stripe-simple.js** - Simplified Stripe integration

#### Backend Python
1. **api/stripe_payments.py** - Stripe endpoints
   - `/api/stripe/create-checkout-session` - Create payment session
   - `/api/stripe/webhook` - Handle Stripe webhooks
   - `/api/stripe/subscription-status` - Check subscription
   - `/api/stripe/customer-portal` - Manage subscription

### Configuration
- Uses environment variables for Stripe keys
- Production URLs hardcoded to prevent localhost issues
- Supports both monthly and yearly billing

## HTML Pages
1. **pricing.html** - Pricing page with buy buttons
   - Uses auth-cookie.js
   - Uses stripe-dual-auth.js
   - Monthly/Yearly toggle

2. **login.html** - Login page
3. **signup.html** - Signup page
4. **dashboard.html** - User dashboard
5. **settings.html** - User settings
6. **index.html** - Homepage with auth integration

## Environment Variables (.env)
```
JWT_SECRET_KEY=your-secret-key-here
STRIPE_SECRET_KEY=sk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_STARTER_MONTHLY_PRICE_ID=price_...
STRIPE_STARTER_YEARLY_PRICE_ID=price_...
STRIPE_PROFESSIONAL_MONTHLY_PRICE_ID=price_...
STRIPE_PROFESSIONAL_YEARLY_PRICE_ID=price_...
STRIPE_BUSINESS_MONTHLY_PRICE_ID=price_...
STRIPE_BUSINESS_YEARLY_PRICE_ID=price_...
FRONTEND_URL=https://bankcsvconverter.com
```

## Deployment Notes
1. Backend runs on port 5000
2. systemd service: bankcsv-backend.service
3. Nginx proxies /api and /v2/api to backend
4. Static files served directly by Nginx

## Authentication Flow

### Cookie Auth (Recommended)
1. User visits site → Get CSRF token from `/v2/api/auth/csrf`
2. Login/Signup → Send credentials with CSRF token
3. Backend validates → Sets httpOnly cookies
4. All requests include cookies automatically
5. Refresh handled via refresh endpoint

### JWT Auth (Legacy)
1. Login/Signup → Receive access token
2. Store token in localStorage
3. Include token in Authorization header
4. Refresh when token expires

## Stripe Payment Flow
1. User clicks buy button
2. Check authentication (cookie or JWT)
3. Create checkout session with plan & billing period
4. Redirect to Stripe checkout
5. Handle success/cancel redirects
6. Webhook updates subscription in database

## Security Features
- httpOnly cookies prevent XSS attacks
- CSRF tokens prevent CSRF attacks
- Secure flag on cookies (HTTPS only)
- Token rotation on refresh
- Password hashing with bcrypt
- Email validation
- Rate limiting on auth endpoints

## Testing
- Cookie auth: Use auth-cookie.js methods
- JWT auth: Use auth-unified.js methods
- Stripe: Test mode available with test keys
- Check browser DevTools for auth state

## Common Issues & Solutions
1. **Redirect to localhost**: Fixed by hardcoding production URL
2. **Auth not persisting**: Use localStorage for JWT, cookies for cookie auth
3. **CSRF errors**: Ensure CSRF token is included in requests
4. **Stripe webhooks**: Verify webhook signature