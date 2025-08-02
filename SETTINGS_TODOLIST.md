# Settings Page Backend Integration Todo List

## Overview
The settings page (https://bankcsvconverter.com/settings.html) has many features that are not connected to the backend. This document outlines all the required tasks to make the settings page fully functional.

## Current Issues

### 1. API Path Mismatch
- **Problem**: Frontend uses `/v2/api/*` but backend endpoints are at `/api/*`
- **Files**: `settings-unified.js`, backend API routes
- **Solution**: Update frontend to use correct API paths or add v2 routes

### 2. Missing Functionality

#### Profile Section (profileForm)
- [ ] Profile update not saving to backend
- [ ] Email change verification not implemented
- [ ] Timezone changes not persisting
- [ ] Company field not updating

#### Security Section
- [ ] Password change form not connected
- [ ] Password strength indicator not functional
- [ ] 2FA enable/disable buttons not working
- [ ] Login history not tracking/displaying
- [ ] No session management system

#### Notifications Section (notificationsForm)
- [ ] Form field IDs don't match backend expectations
- [ ] Email preferences not saving
- [ ] Missing backend fields for all notification types

#### Billing & Plan Section
- [ ] Current plan not fetching from backend
- [ ] Usage stats endpoint missing
- [ ] Monthly usage progress bar not updating
- [ ] Payment method management not connected to Stripe
- [ ] Billing history endpoint missing
- [ ] "Add Payment Method" button not functional

#### Preferences Section (preferencesForm)
- [ ] No backend endpoint for conversion preferences
- [ ] Default export format not saving
- [ ] Date format preference not persisting
- [ ] Auto-download setting not stored
- [ ] Save history toggle not functional
- [ ] Analytics toggle not connected

#### Danger Zone Section
- [ ] Export data button not triggering download
- [ ] Delete account modal not properly implemented
- [ ] Delete confirmation input validation missing

## Backend Endpoints Status

### Existing Endpoints
✅ `/api/user/profile` - GET/PUT
✅ `/api/user/password` - PUT
✅ `/api/user/2fa/*` - POST (enable/verify/disable)
✅ `/api/user/notifications` - GET/PUT
✅ `/api/user/account` - DELETE
✅ `/api/user/export-data` - POST
✅ `/api/stripe/customer-portal` - POST

### Missing Endpoints
❌ `/api/user/sessions` - GET (login history)
❌ `/api/user/preferences` - GET/PUT (conversion settings)
❌ `/api/user/usage-stats` - GET
❌ `/api/user/billing-history` - GET
❌ `/api/user/payment-methods` - GET/POST/DELETE

## Frontend Issues

### JavaScript Integration
1. **settings-unified.js** references non-existent form IDs:
   - `marketingEmails` → should be `emailMarketing`
   - `productUpdates` → should be `emailUpdates`
   - `usageAlerts` → should be `emailSecurity`
   - `shareUsageData` → should be `analytics`
   - `includeHeaders` → not in HTML
   - `defaultFormat` exists but wrong options

2. **Missing Event Handlers**:
   - Password form submit
   - 2FA toggle button
   - Preferences form submit
   - Export data button
   - Delete account button
   - Add payment method button
   - Settings panel navigation

3. **Navigation Issues**:
   - Panel switching uses `.tab-button` but HTML has `.settings-nav-item`
   - Content panels use wrong IDs in JS vs HTML

## Implementation Tasks

### High Priority
1. Fix API path configuration (v2/api vs api)
2. Create unified backend integration
3. Implement password change functionality
4. Add 2FA management
5. Connect Stripe customer portal
6. Implement account deletion flow

### Medium Priority
7. Add login history tracking
8. Create preferences endpoint
9. Implement usage statistics
10. Add billing history
11. Fix notification preferences
12. Add settings panel navigation
13. Implement form validations
14. Add success/error notifications

### Low Priority
15. Password strength indicator
16. Auto-save preferences
17. Enhanced UI animations
18. Keyboard navigation

## Database Schema Requirements

### New Tables/Columns Needed
1. **login_sessions** table:
   - user_id
   - ip_address
   - user_agent
   - location
   - created_at
   - success

2. **user_preferences** table or columns:
   - default_export_format
   - date_format
   - auto_download
   - save_history
   - analytics_enabled

3. **Users table additions**:
   - notification_preferences (JSON)
   - conversion_preferences (JSON)

## File Structure

```
/js/
├── settings-unified.js (needs major updates)
├── auth-cookie.js (authentication)
└── api-config.js (API configuration)

/backend/api/
├── user_settings.py (has most endpoints)
├── user_export.py (export functionality)
├── stripe_payments.py (billing integration)
└── [NEW] user_preferences.py (needed)
└── [NEW] user_sessions.py (needed)
```

## Testing Requirements

1. Test all form submissions
2. Verify data persistence
3. Check error handling
4. Test Stripe integration
5. Verify 2FA flow
6. Test account deletion
7. Validate export functionality

## Security Considerations

1. Password change requires current password
2. 2FA disable requires valid token
3. Account deletion needs email confirmation
4. API endpoints need proper authentication
5. CSRF protection for all mutations
6. Rate limiting for sensitive operations

## Estimated Timeline

- **Week 1**: Fix critical path issues (API paths, authentication)
- **Week 2**: Implement core functionality (profile, password, 2FA)
- **Week 3**: Add billing and preferences
- **Week 4**: Complete remaining features and testing

## Success Criteria

1. All forms save data to backend
2. All settings persist across sessions
3. Stripe integration works for billing
4. 2FA can be enabled/disabled
5. Account export downloads user data
6. Account deletion works with confirmation
7. All panels navigate correctly
8. Proper error/success notifications