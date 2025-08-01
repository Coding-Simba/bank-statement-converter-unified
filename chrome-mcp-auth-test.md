# Chrome MCP Authentication Test Plan

**Date:** 2025-08-01  
**Test Environment:** Production (https://bankcsvconverter.com)

## Prerequisites
- Chrome MCP Server running at http://127.0.0.1:12306/mcp
- Chrome browser with MCP extension installed

## Test Scenarios

### 1. Registration & Auto-Login Test
```
1. Navigate to https://bankcsvconverter.com/signup.html
2. Fill in registration form:
   - Name: Test User
   - Email: test-[timestamp]@example.com
   - Password: TestPass123!
   - Company: (optional)
   - Check terms checkbox
3. Submit form
4. Verify:
   - Should redirect to dashboard (NOT login page)
   - User should be logged in
   - User email should appear in navigation
```

### 2. Cross-Tab Authentication Persistence Test
```
1. After successful login/registration
2. Open new tab and go to https://bankcsvconverter.com/dashboard.html
3. Open another tab and go to https://bankcsvconverter.com/convert-pdf.html
4. Open third tab and go to https://bankcsvconverter.com/analyze-transactions.html
5. Open fourth tab and go to https://bankcsvconverter.com/settings.html
6. Verify in each tab:
   - User remains logged in
   - User email shows in navigation
   - No login prompts appear
```

### 3. Cross-Tab Logout Synchronization Test
```
1. With multiple tabs open (from previous test)
2. In the Dashboard tab, click logout
3. Within 2-5 seconds, check all other tabs:
   - Should show alert: "You have been logged out from another tab"
   - Should redirect to homepage
   - Should not show user info anymore
```

### 4. Cookie Security Verification
```
1. Open Chrome DevTools (F12)
2. Go to Application > Cookies > https://bankcsvconverter.com
3. Look for cookies:
   - access_token
   - refresh_token
4. Verify both cookies have:
   - HttpOnly: ✓ (checkmark)
   - Secure: ✓ (checkmark)
   - SameSite: Lax
```

### 5. Protected Page Access Test
```
1. While logged out, try to access:
   - https://bankcsvconverter.com/dashboard.html
   - https://bankcsvconverter.com/settings.html
2. Verify:
   - Should redirect to login page
   - After login, should redirect back to requested page
```

## Chrome MCP Commands to Use

### Navigate to pages:
- Use the `navigate_to` tool to go to different URLs
- Use the `screenshot` tool to capture page states

### Fill forms:
- Use the `click` tool to click on form fields
- Use the `type` tool to enter text
- Use the `click` tool to submit forms

### Check authentication state:
- Use the `get_page_content` tool to check for user email in navigation
- Use the `screenshot` tool to verify logged-in/logged-out states

### Monitor network:
- Use the `get_network_data` tool to monitor API calls
- Check for /v2/api/auth/register, /v2/api/auth/login, /v2/api/auth/logout

### Check cookies:
- Use Chrome DevTools integration if available
- Or use the `execute_script` tool to check document.cookie

## Expected Results

### ✅ Success Criteria:
1. Registration automatically logs user in
2. All tabs maintain authentication state
3. Logout in one tab affects all tabs
4. Cookies are secure (HttpOnly, Secure)
5. Protected pages redirect when not authenticated

### ❌ Known Issues (Now Fixed):
1. ~~Registration redirected to login~~ → Fixed
2. ~~Different pages showed different auth states~~ → Fixed
3. ~~Logout didn't sync across tabs~~ → Fixed
4. ~~Some pages had no auth protection~~ → Fixed

## Test Execution Steps

1. **Generate unique test email:**
   ```bash
   echo "test-$(date +%Y%m%d-%H%M%S)@example.com"
   ```

2. **Start Chrome MCP test:**
   - Connect to Chrome MCP Server
   - Execute test scenarios in order
   - Document any issues found

3. **Report Results:**
   - Screenshot key states (logged in, logged out, cross-tab sync)
   - Note any errors or unexpected behavior
   - Verify all success criteria are met

## Troubleshooting

If authentication doesn't persist:
1. Check browser console for errors
2. Verify cookies are being set
3. Check network tab for 401 errors
4. Ensure auth-unified.js is loaded on all pages

If cross-tab sync doesn't work:
1. Check browser console for BroadcastChannel errors
2. Verify localStorage events are firing
3. Test in different browser (some browsers block BroadcastChannel)