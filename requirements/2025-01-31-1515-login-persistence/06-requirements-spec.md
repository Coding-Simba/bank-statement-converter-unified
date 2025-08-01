# Requirements Specification: Login Persistence Fix

## Problem Statement

Users are experiencing authentication issues where they are randomly logged out when navigating between pages or refreshing the browser. The current authentication system uses localStorage to store JWT tokens, which is vulnerable to XSS attacks and doesn't provide reliable persistence. Multiple conflicting authentication scripts are causing race conditions and inconsistent behavior.

## Solution Overview

Implement a modern, secure authentication system using HTTP-only cookies for JWT storage, with proper "Remember Me" functionality and session management. This will ensure users remain logged in until they explicitly log out, with authentication persisting across page refreshes, browser restarts, and navigation throughout the website.

## Functional Requirements

### 1. Cookie-Based Authentication
- **FR1.1**: Replace all localStorage token storage with HTTP-only cookies
- **FR1.2**: Implement CSRF protection for all authenticated requests
- **FR1.3**: Set cookie domain to `.bankcsvconverter.com` for cross-subdomain support
- **FR1.4**: Ensure cookies work with both HTTP (development) and HTTPS (production)

### 2. Remember Me Functionality
- **FR2.1**: Process the existing "Remember Me" checkbox on login form
- **FR2.2**: Set refresh token expiry to 90 days when "Remember Me" is checked
- **FR2.3**: Set refresh token expiry to 24 hours when "Remember Me" is not checked
- **FR2.4**: Store remember me preference in user session data

### 3. Token Management
- **FR3.1**: Set access token expiry to 15 minutes (security best practice)
- **FR3.2**: Implement automatic token refresh before expiration
- **FR3.3**: Support refresh token rotation for enhanced security
- **FR3.4**: Handle token refresh failures gracefully with re-authentication

### 4. Session Management
- **FR4.1**: Track active sessions per user with device/browser information
- **FR4.2**: Display active sessions in user settings/dashboard
- **FR4.3**: Allow users to revoke specific sessions
- **FR4.4**: Support multiple concurrent sessions per user
- **FR4.5**: Do NOT invalidate other sessions on password change

### 5. Authentication Persistence
- **FR5.1**: Maintain authentication across all pages on the domain
- **FR5.2**: Persist authentication through browser refresh
- **FR5.3**: Persist authentication through browser restart (with remember me)
- **FR5.4**: Only clear authentication on explicit logout

## Technical Requirements

### Backend Changes

#### 1. Update Authentication Endpoints (`/backend/api/auth.py`)
- Modify login endpoint to accept and process `remember_me` parameter
- Return tokens in HTTP-only cookies instead of response body
- Add session tracking with device fingerprinting

#### 2. Configure Cookie Settings (`/backend/api/auth_cookie.py`)
- Set `COOKIE_DOMAIN = ".bankcsvconverter.com"`
- Configure different token lifetimes based on remember me
- Ensure proper cookie security flags (HttpOnly, Secure, SameSite)

#### 3. Update Token Utilities (`/backend/utils/auth.py`)
- Change `ACCESS_TOKEN_EXPIRE_MINUTES` to 15
- Add `REFRESH_TOKEN_EXPIRE_HOURS = 24` (default)
- Add `REFRESH_TOKEN_EXPIRE_DAYS_REMEMBER = 90`

#### 4. Extend User Model (`/backend/models/database.py`)
- Add `sessions` relationship for tracking active sessions
- Create Session model with fields:
  - `user_id`, `session_id`, `device_info`, `ip_address`
  - `created_at`, `last_accessed`, `expires_at`
  - `is_remember_me`, `is_active`

#### 5. Update CORS Configuration (`/backend/main.py`)
- Ensure `allow_credentials=True` is set
- Add production domain to allowed origins

### Frontend Changes

#### 1. Create Unified Auth Script (`/js/auth-unified.js`)
- Consolidate all authentication logic
- Use `credentials: 'include'` for all API calls
- Implement automatic token refresh
- Handle CSRF token management

#### 2. Update Login Form Handler (`/login.html`)
- Capture "Remember Me" checkbox value
- Pass `remember_me` parameter to login API
- Remove all localStorage token storage

#### 3. Remove Conflicting Scripts
- Delete: `auth-fixed.js`, `auth-persistent.js`, `auth-universal.js`
- Keep only: `auth-unified.js` as the single auth script

#### 4. Update All HTML Pages
- Replace multiple auth script includes with single `auth-unified.js`
- Ensure consistent authentication handling across all pages

#### 5. Create Session Management UI
- Add "Active Sessions" section to user settings/dashboard
- Display session list with device info and last activity
- Add "Revoke" button for each session
- Show "Remember Me" status for each session

### API Changes

#### 1. Login Endpoint
```python
POST /api/auth/login
Body: {
    "email": "user@example.com",
    "password": "password123",
    "remember_me": true
}
Response: {
    "user": { ...user data... }
    // No tokens in response - they're in cookies
}
```

#### 2. New Session Endpoints
```python
GET /api/auth/sessions - List user's active sessions
DELETE /api/auth/sessions/{session_id} - Revoke specific session
```

## Implementation Hints

### 1. Cookie Configuration Pattern
```python
response.set_cookie(
    key="refresh_token",
    value=refresh_token,
    httponly=True,
    secure=request.url.scheme == "https",
    samesite="lax",
    max_age=90 * 24 * 60 * 60 if remember_me else 24 * 60 * 60,
    path="/",
    domain=".bankcsvconverter.com"
)
```

### 2. Frontend API Call Pattern
```javascript
const response = await fetch('/api/endpoint', {
    method: 'POST',
    credentials: 'include',  // Critical for cookies
    headers: {
        'Content-Type': 'application/json',
        'X-CSRF-Token': getCsrfToken()
    },
    body: JSON.stringify(data)
});
```

### 3. Token Refresh Pattern
```javascript
// Check token expiry before each request
if (tokenExpiresIn < 5 * 60 * 1000) { // 5 minutes
    await refreshToken();
}
```

## Acceptance Criteria

1. **Login Persistence**
   - [ ] User remains logged in when navigating between pages
   - [ ] User remains logged in after browser refresh
   - [ ] User remains logged in after browser restart (with remember me)
   - [ ] User is only logged out when clicking "Log out"

2. **Remember Me**
   - [ ] Checkbox value is processed correctly
   - [ ] Token expiry changes based on remember me selection
   - [ ] Remember me sessions last 90 days
   - [ ] Non-remember me sessions last 24 hours

3. **Security**
   - [ ] No tokens stored in localStorage
   - [ ] All tokens in HTTP-only cookies
   - [ ] CSRF protection implemented
   - [ ] Refresh token rotation working

4. **Session Management**
   - [ ] Users can view active sessions
   - [ ] Users can revoke specific sessions
   - [ ] Multiple devices can be logged in simultaneously
   - [ ] Session info shows device and last activity

5. **Migration**
   - [ ] All old auth scripts removed
   - [ ] Single unified auth script deployed
   - [ ] No breaking changes for existing users
   - [ ] Clean migration from localStorage to cookies

## Assumptions

1. **Compliance**: 90-day maximum session lifetime meets GDPR/CCPA requirements
2. **Browser Support**: All target browsers support secure cookies
3. **Infrastructure**: Nginx properly configured to proxy cookie headers
4. **Domain**: Production uses HTTPS for secure cookies
5. **Database**: Can add session tracking table without issues