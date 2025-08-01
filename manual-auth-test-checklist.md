# Manual Authentication Test Checklist

**Test Email:** test-20250801-141941@example.com  
**Test Password:** TestPass123!  
**Test URL:** https://bankcsvconverter.com

## Pre-Test Setup
- [ ] Chrome MCP Server running at http://127.0.0.1:12306/mcp
- [ ] Chrome browser with DevTools ready (F12)
- [ ] Clear browser cookies for bankcsvconverter.com

## Test 1: Registration & Auto-Login ✅

### Steps:
1. [ ] Navigate to https://bankcsvconverter.com/signup.html
2. [ ] Fill registration form:
   - Full Name: `Test User`
   - Work Email: `test-20250801-141941@example.com`
   - Password: `TestPass123!`
   - Company: (leave empty)
   - [ ] Check "I agree to the Terms of Service"
3. [ ] Click "Create Account"
4. [ ] Wait for redirect (3-5 seconds)

### Expected Result:
- ✅ Should redirect to `/dashboard.html` (NOT `/login.html`)
- ✅ User email should appear in navigation
- ✅ No login prompt should appear

### Actual Result:
- Redirected to: ________________
- User shown as logged in? Yes / No
- Issues: ________________

## Test 2: Cross-Tab Authentication Persistence 🔄

### Steps:
1. [ ] Keep first tab open (dashboard)
2. [ ] Open new tab (Ctrl+T)
3. [ ] Navigate to https://bankcsvconverter.com/convert-pdf.html
   - User logged in? Yes / No
   - Email shown? Yes / No
4. [ ] Open another new tab
5. [ ] Navigate to https://bankcsvconverter.com/analyze-transactions.html
   - User logged in? Yes / No
   - Email shown? Yes / No
6. [ ] Open another new tab
7. [ ] Navigate to https://bankcsvconverter.com/settings.html
   - User logged in? Yes / No
   - Email shown? Yes / No

### Expected Result:
- ✅ All tabs show user as logged in
- ✅ User email visible in navigation on all pages
- ✅ No login prompts on any page

### Actual Result:
- All tabs authenticated? Yes / No
- Issues: ________________

## Test 3: Cookie Security Check 🔒

### Steps:
1. [ ] Open DevTools (F12)
2. [ ] Go to Application tab
3. [ ] Navigate to Cookies > https://bankcsvconverter.com
4. [ ] Find cookies:
   - `access_token`
   - `refresh_token`

### Expected Result:
Both cookies should have:
- ✅ HttpOnly: ✓
- ✅ Secure: ✓
- ✅ SameSite: Lax

### Actual Result:
- access_token: HttpOnly: ___ Secure: ___ SameSite: ___
- refresh_token: HttpOnly: ___ Secure: ___ SameSite: ___

## Test 4: Cross-Tab Logout Synchronization 🚪

### Steps:
1. [ ] Ensure you have 4 tabs open (from Test 2)
2. [ ] In the Dashboard tab, click logout button/link
3. [ ] Start timer
4. [ ] Watch other tabs for 5 seconds

### Expected Result:
Within 2-5 seconds in other tabs:
- ✅ Alert appears: "You have been logged out from another tab"
- ✅ All tabs redirect to homepage
- ✅ User no longer shown as logged in

### Actual Result:
- Alert shown? Yes / No
- Time to sync: ___ seconds
- All tabs logged out? Yes / No
- Issues: ________________

## Test 5: Protected Page Access (Logged Out) 🔐

### Steps:
1. [ ] Ensure you're logged out
2. [ ] Try to access https://bankcsvconverter.com/dashboard.html
3. [ ] Try to access https://bankcsvconverter.com/settings.html

### Expected Result:
- ✅ Should redirect to login page
- ✅ URL should include redirect parameter

### Actual Result:
- Redirected to login? Yes / No
- Redirect URL preserved? Yes / No

## Network Monitoring (Optional)

In DevTools Network tab, look for these API calls:
- [ ] POST /v2/api/auth/register (during signup)
- [ ] GET /v2/api/auth/check (on page loads)
- [ ] POST /v2/api/auth/logout (during logout)

## Test Summary

| Test | Pass | Fail | Notes |
|------|------|------|-------|
| Registration Auto-Login | ☐ | ☐ | |
| Cross-Tab Persistence | ☐ | ☐ | |
| Cookie Security | ☐ | ☐ | |
| Cross-Tab Logout | ☐ | ☐ | |
| Protected Pages | ☐ | ☐ | |

## Issues Found:
1. ________________
2. ________________
3. ________________

## Screenshots to Capture:
1. After registration (dashboard or login?)
2. Multiple tabs showing authentication
3. DevTools showing cookies
4. Logout alert (if it appears)

---
**Test Completed By:** ________________  
**Date/Time:** ________________