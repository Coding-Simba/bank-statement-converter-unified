# Detail Questions

Based on the codebase analysis, these are the most pressing questions to clarify expected system behavior.

## Q6: Should we completely remove localStorage-based authentication and migrate all users to cookie-based auth immediately?
**Default if unknown:** No (gradual migration is safer to avoid breaking existing sessions)

## Q7: Should the "Remember Me" checkbox extend the refresh token lifetime to 90 days (vs 24 hours without it)?
**Default if unknown:** Yes (industry standard for remember me is 30-90 days)

## Q8: Should we invalidate all existing sessions when a user changes their password?
**Default if unknown:** Yes (security best practice to prevent unauthorized access)

## Q9: Should we display active sessions to users and allow them to revoke specific devices/sessions?
**Default if unknown:** No (adds complexity, can be added in future phase)

## Q10: Should the cookie domain be set to ".bankcsvconverter.com" to work across all subdomains?
**Default if unknown:** Yes (enables consistent auth across www and non-www versions)