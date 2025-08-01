# Expert Requirements Questions

## Q6: Should the `/api/user/statistics` endpoint include subscription-specific limits (e.g., 1000 conversions/month for Pro users)?
**Default if unknown:** Yes (better to show plan-specific limits for transparency)

## Q7: When implementing data export, should we include the original PDF files or just the converted CSV data and metadata?
**Default if unknown:** No (only CSV data and metadata to reduce storage/bandwidth requirements)

## Q8: Should the analytics features aggregate data across all user statements or allow filtering by date range?
**Default if unknown:** Yes (date range filtering provides more useful insights)

## Q9: Should deleted statements be soft-deleted (marked as deleted but retained) or hard-deleted from the database?
**Default if unknown:** Yes (soft-delete for audit trail and potential recovery)

## Q10: Should the dashboard show real-time Stripe subscription status or cache it with periodic updates?
**Default if unknown:** No (use cached data with 5-minute updates to reduce Stripe API calls)