# Complete File Inventory - Authentication & Stripe System

## Frontend Files

### JavaScript - Authentication
- `/js/auth-cookie.js` - Primary cookie-based auth system
- `/js/auth-unified.js` - Legacy JWT auth system
- `/js/auth-no-redirect.js` - Auth without page redirects
- `/js/api-config.js` - API configuration

### JavaScript - Stripe Integration
- `/js/stripe-dual-auth.js` - Works with both auth systems (CURRENT)
- `/js/stripe-cookie-integration.js` - Cookie-only Stripe
- `/js/stripe-cookie.js` - Cookie-based Stripe handlers
- `/js/stripe-integration.js` - Original Stripe integration
- `/js/stripe-integration-fixed.js` - Fixed version
- `/js/stripe-integration-fix.js` - Another fix version
- `/js/stripe-simple.js` - Simplified Stripe
- `/js/stripe-fixed.js` - Fixed Stripe handlers

### HTML Pages
- `/pricing.html` - Pricing page with Stripe integration
- `/login.html` - Login page
- `/signup.html` - Signup page  
- `/dashboard.html` - User dashboard
- `/settings.html` - User settings
- `/index.html` - Homepage

## Backend Files

### API Endpoints
- `/backend/api/auth.py` - JWT authentication endpoints
- `/backend/api/auth_cookie.py` - Cookie authentication endpoints
- `/backend/api/stripe_payments.py` - Stripe payment endpoints

### Middleware
- `/backend/middleware/auth_middleware.py` - JWT auth middleware
- `/backend/middleware/csrf_middleware.py` - CSRF protection

### Utilities & Config
- `/backend/utils/auth.py` - Auth helper functions
- `/backend/config/jwt_config.py` - JWT configuration
- `/backend/models/database.py` - User model (partial)

### Main Application
- `/backend/main.py` - FastAPI application setup

## Configuration Files

### Environment Variables
- `/backend/.env` - Contains all secrets and API keys

### Service Configuration  
- `/etc/systemd/system/bankcsv-backend.service` - Backend service

### Nginx Configuration
- Proxies `/api/*` to backend port 5000
- Proxies `/v2/api/*` to backend port 5000

## Database Schema (Relevant Tables)

### Users Table
- id
- email
- password_hash
- full_name
- company_name
- account_type
- stripe_customer_id
- created_at
- is_active
- email_verified
- refresh_token_family
- refresh_token_version

### Subscriptions Table
- id
- user_id
- stripe_subscription_id
- stripe_price_id
- status
- current_period_start
- current_period_end
- created_at
- updated_at

## Active Versions on Production

As of August 2, 2025:
- Authentication: Using dual system (Cookie + JWT)
- Frontend Auth: `auth-cookie.js` for new sessions
- Stripe Integration: `stripe-dual-auth.js`
- Backend: Cookie auth at `/v2/api/auth/*`, JWT at `/api/auth/*`

## Git Repository Structure
```
bank-statement-converter-unified/
├── js/
│   ├── auth-*.js
│   └── stripe-*.js
├── backend/
│   ├── api/
│   ├── middleware/
│   ├── utils/
│   └── config/
├── *.html
└── backup_auth_stripe_20250802_094030/
    └── (this backup)
```