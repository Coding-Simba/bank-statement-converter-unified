# Context Findings

## Current Architecture

### 1. Authentication System
- **File:** `/backend/api/auth_cookie.py`
- Uses HTTP-only cookies for authentication
- Has JWT access tokens (15 min) and refresh tokens (24h/90d)
- Current user endpoints:
  - `/api/auth/register`
  - `/api/auth/login`
  - `/api/auth/logout`
  - `/api/auth/refresh`
  - `/api/auth/check`
  - `/api/auth/me`

### 2. Database Models
- **File:** `/backend/models/database.py`
- User model has fields:
  - `email`, `password_hash`, `full_name`, `company_name`
  - `account_type`, `subscription_status`, `subscription_plan`
  - `stripe_customer_id`, `auth_provider`
  - `email_verified`, `email_verification_token`
  - `password_reset_token`, `password_reset_expires`
  - Missing fields needed: `timezone`, `notification_preferences`, `api_key`, `two_factor_secret`

### 3. Stripe Integration
- **File:** `/backend/api/stripe_payments.py`
- Already handles:
  - Checkout sessions
  - Subscription management
  - Webhook processing
  - Customer portal sessions
- Endpoints:
  - `/api/stripe/create-checkout-session`
  - `/api/stripe/customer-portal`
  - `/api/stripe/subscription-status`

### 4. Email Service
- **Finding:** No email service currently implemented
- `email_validator` package is installed but no email sending functionality
- Will need to implement email service for:
  - Security notifications
  - Email verification
  - Password reset

### 5. Settings Features Needed

#### Profile Management
- **Endpoint needed:** `PUT /api/user/profile`
- Update: full_name, company_name, timezone
- Need to add timezone field to User model

#### Security Settings
- **Password Change:** `PUT /api/user/password`
- **2FA:** `POST /api/user/2fa/enable`, `POST /api/user/2fa/disable`
- **API Key:** `POST /api/user/api-key/generate`, `DELETE /api/user/api-key`
- Need to add fields: two_factor_secret, two_factor_enabled, api_key

#### Notification Preferences
- **Endpoint:** `PUT /api/user/notifications`
- Need to add notification_preferences JSON field

#### Account Management
- **Delete Account:** `DELETE /api/user/account`
- **Export Data:** Already exists at `/api/user/export`

### 6. Patterns to Follow
- All routers use FastAPI's APIRouter
- Authentication via `get_current_user` dependency
- Pydantic models for request/response validation
- SQLAlchemy for database operations
- Consistent error handling with HTTPException

### 7. Implementation Order
1. Database migrations for new fields
2. Email service setup
3. User profile endpoints
4. Security endpoints (password, 2FA)
5. Notification preferences
6. Integration with existing Stripe customer portal
7. Account deletion with verification

### 8. Files to Create/Modify
- **Create:** `/backend/api/user_settings.py` - Main settings endpoints
- **Create:** `/backend/utils/email.py` - Email service
- **Create:** `/backend/utils/two_factor.py` - 2FA utilities
- **Modify:** `/backend/models/database.py` - Add new fields
- **Modify:** `/backend/main.py` - Include new router
- **Create:** `/backend/migrations/add_settings_fields.py` - Database migration