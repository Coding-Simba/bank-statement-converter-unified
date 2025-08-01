# Expert Detail Questions

## Q6: Should I test the Stripe checkout flow using the test card 4242 4242 4242 4242?
**Default if unknown:** Yes (this is Stripe's standard test card for successful payments)

## Q7: Do you want me to verify that the auth cookies are marked as HttpOnly and Secure in production?
**Default if unknown:** Yes (security best practice for authentication cookies)

## Q8: Should I test the automatic token refresh by waiting 25+ minutes after login?
**Default if unknown:** No (this would make the test too long; checking immediate persistence is sufficient)

## Q9: Do you want me to test logout functionality to ensure it clears cookies across all tabs?
**Default if unknown:** Yes (proper logout is critical for security)

## Q10: Should I generate a unique test email like test-[timestamp]@example.com for registration?
**Default if unknown:** Yes (avoids conflicts with existing test accounts)