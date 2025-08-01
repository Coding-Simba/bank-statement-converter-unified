# Context Findings

## Current State Analysis

### Working Backend Components
1. **Authentication System**
   - Dual auth system (JWT + Cookie-based)
   - OAuth integration (Google, Microsoft)
   - CSRF protection
   - Session management
   
2. **PDF Conversion System**
   - Multiple parsers (Universal, Camelot, PyMuPDF)
   - OCR capabilities for image-based PDFs
   - Validation interface
   - Rate limiting

3. **Payment Integration**
   - Complete Stripe integration
   - Subscription management
   - Usage-based billing
   - Customer portal access

4. **Database Models**
   - User model with subscription info
   - Statement tracking with expiration
   - Usage logging and analytics
   - Session management

### Critical Missing Endpoints

1. **`GET /api/user/statistics`** (HIGH PRIORITY)
   - Expected by `js/modern-dashboard.js` line 52
   - Should return: `{todayConversions, totalConversions, remainingToday}`
   - Data exists in database, just needs endpoint

2. **`GET /api/statements/recent`** (HIGH PRIORITY)
   - Expected by `js/modern-dashboard.js` line 85
   - Should return paginated list of recent statements
   - Can leverage existing `/api/user/statements` logic

3. **`DELETE /api/statement/{id}`** (HIGH PRIORITY)
   - Expected by `js/modern-dashboard.js` line 182
   - Needs authorization check and soft delete

4. **`GET /api/auth/me`** (CRITICAL - Currently Broken)
   - Expected by `js/modern-dashboard.js` line 21
   - File exists at `/backend/api/auth_verify.py` but has import errors
   - Lines 5-7 have incorrect imports

### Files Requiring Modification

1. **`/backend/api/auth_verify.py`**
   - Fix imports on lines 5-7
   - Currently importing from non-existent modules

2. **`/backend/main.py`**
   - Add new router imports for statistics and recent statements
   - Currently missing several expected routers

### New Files to Create

1. **`/backend/api/user_statistics.py`**
   - Implement daily/total conversion counts
   - Calculate remaining conversions based on plan
   - Use existing GenerationTracking model

2. **`/backend/api/statements_recent.py`**
   - Paginated recent statements endpoint
   - Include file metadata and validation status
   - Filter by user/session

3. **`/backend/api/statement_delete.py`**
   - Soft delete functionality
   - Authorization checks
   - Update statistics after deletion

### Implementation Patterns to Follow

1. **Authentication Pattern**
   ```python
   from ..dependencies import get_current_user
   user = Depends(get_current_user)
   ```

2. **Database Session Pattern**
   ```python
   from ..database import get_db
   db: Session = Depends(get_db)
   ```

3. **Error Handling Pattern**
   ```python
   from fastapi import HTTPException
   raise HTTPException(status_code=404, detail="Statement not found")
   ```

4. **Response Model Pattern**
   ```python
   from pydantic import BaseModel
   class StatisticsResponse(BaseModel):
       todayConversions: int
       totalConversions: int
       remainingToday: int
   ```

### Related Features Analysis

1. **Analytics Integration**
   - Existing `/api/analyze-transactions` endpoint
   - Can be displayed in dashboard insights section
   - Already returns category breakdowns and patterns

2. **Export Functionality**
   - Can leverage existing PDF/Excel report generation
   - Need to add usage history export endpoint
   - Use existing report generation utilities

3. **Subscription Display**
   - Data available in User model
   - Stripe integration provides real-time status
   - Need to expose via statistics endpoint

### Technical Constraints

1. **Rate Limiting**
   - Anonymous users: 3 conversions/day
   - Free users: 5 conversions/day
   - Paid users: Based on plan

2. **File Expiration**
   - Files deleted after 1 hour
   - Need to handle expired files gracefully

3. **Session Management**
   - Support both authenticated and anonymous users
   - Session tracking for anonymous conversions

### Integration Points

1. **Frontend Expectations**
   - Modern dashboard uses Bearer token auth
   - Expects specific response formats
   - 60-second auto-refresh for statistics

2. **Database Queries**
   - Use SQLAlchemy ORM patterns
   - Implement proper joins for performance
   - Consider query optimization for statistics

3. **Middleware Integration**
   - CORS already configured
   - Auth middleware in place
   - Error handling middleware active