# Requirements Specification: Modern Dashboard Backend Implementation

## Problem Statement
The modern dashboard interface (`dashboard-modern.html`) has been created but lacks backend functionality. All features are currently non-functional and need complete backend integration to provide users with a working dashboard experience.

## Solution Overview
Implement all missing backend API endpoints required by the modern dashboard, fix broken authentication endpoints, and ensure proper data flow between frontend and backend systems while maintaining existing authentication, payment, and PDF conversion functionality.

## Functional Requirements

### 1. User Statistics Display
- **Endpoint**: `GET /api/user/statistics`
- **Purpose**: Provide real-time usage statistics for dashboard display
- **Response Format**:
  ```json
  {
    "todayConversions": 3,
    "totalConversions": 47,
    "remainingToday": 2,
    "planLimits": {
      "daily": 5,
      "monthly": 150,
      "usedThisMonth": 47
    },
    "accountType": "free"
  }
  ```

### 2. Recent Conversions Management
- **Endpoint**: `GET /api/statements/recent`
- **Purpose**: Display user's recent PDF conversions
- **Features**:
  - Pagination support (limit parameter)
  - Include file metadata (size, bank, creation time)
  - Show validation status
  - Filter by date range (optional)
- **Response includes**: id, original_filename, bank, file_size, created_at, validated

### 3. Statement Deletion
- **Endpoint**: `DELETE /api/statement/{id}`
- **Purpose**: Allow users to delete their conversions
- **Implementation**: Soft delete (add `deleted_at` timestamp)
- **Authorization**: User can only delete their own statements

### 4. Authentication Fix
- **Fix**: `/api/auth/me` endpoint
- **Issue**: Import errors in `/backend/api/auth_verify.py`
- **Solution**: Correct import paths and ensure proper user data return

### 5. Analytics Integration
- **Leverage existing**: `/api/analyze-transactions` endpoint
- **Add date filtering**: Support `start_date` and `end_date` parameters
- **Dashboard display**: Show spending patterns and category breakdowns

### 6. Data Export Functionality
- **Endpoint**: `POST /api/user/export-data`
- **Formats**: CSV and JSON
- **Content**: Conversion history, usage statistics, account activity
- **Exclude**: Original PDF files (only metadata)

### 7. Subscription Status Display
- **Cache Strategy**: 5-minute cache for Stripe data
- **Include in**: `/api/user/statistics` response
- **Show**: Current plan, renewal date, usage limits

## Technical Requirements

### 1. Database Schema Updates
```sql
-- Add soft delete to statements table
ALTER TABLE statements ADD COLUMN deleted_at TIMESTAMP NULL;

-- Add index for performance
CREATE INDEX idx_statements_user_deleted ON statements(user_id, deleted_at);
```

### 2. File Structure
```
/backend/api/
├── user_statistics.py      # NEW: User statistics endpoint
├── statements_recent.py    # NEW: Recent statements endpoint  
├── statement_delete.py     # NEW: Statement deletion
├── user_export.py         # NEW: Data export functionality
└── auth_verify.py         # FIX: Import errors
```

### 3. Authentication Middleware
- Use existing `get_current_user` dependency
- Support both JWT and session-based auth
- Handle anonymous users appropriately

### 4. Error Handling
- Return consistent error formats
- Use appropriate HTTP status codes
- Log errors for debugging

### 5. Performance Considerations
- Implement query optimization for statistics
- Use database indexes effectively
- Cache subscription data (5-minute TTL)

## Implementation Hints

### 1. Statistics Calculation Pattern
```python
# Use existing GenerationTracking model
today_count = db.query(GenerationTracking).filter(
    GenerationTracking.user_id == user.id,
    GenerationTracking.date == date.today()
).first()

# Get plan limits from user model
limits = {
    "free": {"daily": 5, "monthly": 150},
    "pro": {"daily": 50, "monthly": 1500},
    "business": {"daily": -1, "monthly": -1}  # Unlimited
}
```

### 2. Recent Statements Query
```python
# Use existing Statement model with eager loading
statements = db.query(Statement).filter(
    Statement.user_id == user.id,
    Statement.deleted_at.is_(None)
).order_by(Statement.created_at.desc()).limit(limit).all()
```

### 3. Soft Delete Implementation
```python
# Don't actually delete, just mark
statement.deleted_at = datetime.utcnow()
db.commit()
```

### 4. Cache Implementation
```python
# Use simple in-memory cache for subscription data
from cachetools import TTLCache
subscription_cache = TTLCache(maxsize=1000, ttl=300)  # 5 minutes
```

## Acceptance Criteria

1. **Dashboard Statistics**
   - [x] Shows today's conversions count
   - [x] Shows total conversions count
   - [x] Shows remaining conversions for today
   - [x] Displays current account type
   - [x] Shows plan-specific limits

2. **Recent Conversions**
   - [x] Lists up to 10 recent conversions
   - [x] Shows file metadata (name, size, bank, date)
   - [x] Indicates validation status
   - [x] Provides download, validate, and delete actions

3. **Statement Management**
   - [x] Users can delete their own statements
   - [x] Deleted statements are soft-deleted
   - [x] Statistics update after deletion

4. **Authentication**
   - [x] `/api/auth/me` returns user information
   - [x] Handles expired tokens gracefully
   - [x] Supports both JWT and cookie auth

5. **Data Export**
   - [x] Exports user data in CSV/JSON format
   - [x] Includes conversion history and statistics
   - [x] Excludes PDF file content

6. **Performance**
   - [x] Dashboard loads in under 2 seconds
   - [x] Statistics are accurate and real-time
   - [x] Subscription data is cached appropriately

## Assumptions

1. **Soft Delete**: Deleted statements are retained for 30 days before permanent deletion
2. **Export Format**: CSV includes headers, JSON is pretty-printed
3. **Rate Limiting**: Existing rate limits apply to all new endpoints
4. **Anonymous Users**: Recent statements show session-based conversions
5. **Time Zone**: All timestamps are UTC, converted client-side

## Dependencies

- Fix import issues in `/backend/api/auth_verify.py` first
- Ensure `/backend/main.py` includes all new routers
- Database migration for soft delete column
- Frontend expects specific response formats (don't change without coordination)