# Settings Backend Requirements Specification

## Problem Statement
The settings page frontend is complete but has no backend functionality. Users cannot update their profile, change passwords, manage security settings, or configure preferences. All forms submit but no data is saved or processed.

## Solution Overview
Implement a comprehensive settings API that handles all user account management features including profile updates, security settings, notification preferences, billing integration, and account deletion.

## Functional Requirements

### 1. Profile Management
- **Endpoint:** `PUT /v2/api/user/profile`
- **Updates:** full_name, company_name, timezone
- **Real-time sync:** Changes reflected immediately across all sessions
- **Email changes:** Require verification through new email address

### 2. Security Settings

#### Password Management
- **Endpoint:** `PUT /v2/api/user/password`
- **Validation:** Current password required, 8+ characters
- **Notification:** Send email alert on password change
- **Session handling:** Invalidate other sessions on password change

#### Two-Factor Authentication
- **Enable:** `POST /v2/api/user/2fa/enable`
- **Disable:** `POST /v2/api/user/2fa/disable`
- **Verify:** `POST /v2/api/user/2fa/verify`
- **Implementation:** TOTP with QR codes, Google Authenticator compatible
- **Backup codes:** Generate 10 single-use recovery codes

#### API Key Management
- **Generate:** `POST /v2/api/user/api-key`
- **Delete:** `DELETE /v2/api/user/api-key`
- **List:** `GET /v2/api/user/api-keys`
- **Format:** 32-character random string with prefix "bcsv_"
- **Scope:** Full user access (no granular permissions initially)

### 3. Notification Preferences
- **Endpoint:** `PUT /v2/api/user/notifications`
- **Categories:**
  - security_alerts (default: true)
  - product_updates (default: true)
  - usage_reports (default: false)
  - marketing_emails (default: false)
- **Storage:** JSON field in database

### 4. Billing Integration
- **Use existing Stripe integration**
- **Endpoint:** `GET /v2/api/user/subscription`
- **Portal:** Redirect to Stripe Customer Portal for management

### 5. Account Management
- **Delete:** `DELETE /v2/api/user/account`
- **Process:**
  1. Require password confirmation
  2. Send confirmation email
  3. Delete immediately upon confirmation
  4. No grace period for recovery

## Technical Requirements

### Database Schema Updates
```sql
ALTER TABLE users ADD COLUMN timezone VARCHAR(50) DEFAULT 'UTC';
ALTER TABLE users ADD COLUMN two_factor_secret VARCHAR(255);
ALTER TABLE users ADD COLUMN two_factor_enabled BOOLEAN DEFAULT FALSE;
ALTER TABLE users ADD COLUMN api_key VARCHAR(255) UNIQUE;
ALTER TABLE users ADD COLUMN api_key_created_at TIMESTAMP;
ALTER TABLE users ADD COLUMN notification_preferences JSON DEFAULT '{"security_alerts": true, "product_updates": true, "usage_reports": false, "marketing_emails": false}';
ALTER TABLE users ADD COLUMN pending_email VARCHAR(255);
ALTER TABLE users ADD COLUMN pending_email_token VARCHAR(255);
ALTER TABLE users ADD COLUMN pending_email_expires TIMESTAMP;
```

### New Dependencies
```python
# requirements.txt additions
pyotp==2.9.0  # TOTP implementation
qrcode==7.4.2  # QR code generation
sendgrid==6.11.0  # Email service (or alternative)
python-multipart==0.0.6  # Form data handling
```

### Email Templates Needed
1. Password changed notification
2. Email verification (for email changes)
3. 2FA enabled/disabled notification
4. Account deletion confirmation
5. API key generated notification

### Security Considerations
- Rate limit sensitive endpoints (5 attempts per hour)
- Require current password for all security changes
- Log security events for audit trail
- Use secure random for API keys and tokens
- Hash API keys before storing (store only last 4 chars in plain)

## Implementation Hints

### File Structure
```
backend/
├── api/
│   └── user_settings.py  # Main settings endpoints
├── utils/
│   ├── email.py          # Email service wrapper
│   └── two_factor.py     # 2FA utilities
├── templates/
│   └── email/            # Email HTML templates
└── migrations/
    └── add_settings_fields.py
```

### Router Registration (main.py)
```python
from api.user_settings import router as user_settings_router
app.include_router(user_settings_router, prefix="/v2")
```

### Authentication Pattern
```python
@router.put("/api/user/profile")
async def update_profile(
    request: ProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Implementation
```

### Email Service Pattern
```python
async def send_email(to: str, subject: str, template: str, data: dict):
    # Use SendGrid or AWS SES
    # Handle errors gracefully
    # Log email sends
```

## Acceptance Criteria

### Profile Management
- [ ] Users can update name, company, timezone
- [ ] Email changes require verification
- [ ] Changes sync across all sessions
- [ ] Form shows current values on load

### Security
- [ ] Password changes work with email notification
- [ ] 2FA can be enabled/disabled with QR code
- [ ] API keys can be generated and revoked
- [ ] All changes require password confirmation

### Notifications
- [ ] Granular preference controls work
- [ ] Settings persist and load correctly
- [ ] Email notifications respect preferences

### Account
- [ ] Account deletion requires confirmation
- [ ] All user data is properly removed
- [ ] Stripe subscription is cancelled

## Assumptions
- Email service will use SendGrid (API key needed)
- No SMS 2FA initially (TOTP only)
- No API key scopes in v1
- No soft delete/recovery period
- Frontend already handles loading states and errors

## Next Steps
1. Set up email service configuration
2. Create database migration script
3. Implement user_settings.py endpoints
4. Add email templates
5. Update frontend API endpoints to /v2/api/user/*
6. Test all flows end-to-end