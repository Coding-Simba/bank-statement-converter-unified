# User Account System Documentation

## Overview

The BankCSVConverter now includes a comprehensive user account system with the following features:

- **Generation Limits**: 3 PDFs/day (anonymous), 10 PDFs/day (free account), unlimited (premium)
- **Statement Storage**: Converted statements saved for 1 hour for registered users
- **Feedback System**: Users can rate conversions and earn extra generations
- **JWT Authentication**: Secure token-based authentication
- **User Dashboard**: View saved statements and track usage

## Architecture

### Backend (FastAPI + SQLite)

```
backend/
├── main.py                 # FastAPI application entry point
├── init_db.py             # Database initialization script
├── requirements.txt       # Python dependencies
├── test_api.py           # API testing script
├── test_setup.py         # Quick setup verification
├── models/
│   └── database.py       # SQLAlchemy models and database setup
├── api/
│   ├── auth.py          # Authentication endpoints
│   ├── statements.py    # Statement conversion endpoints
│   └── feedback.py      # Feedback system endpoints
├── utils/
│   └── auth.py          # JWT and authentication utilities
└── middleware/
    └── auth_middleware.py # Authentication middleware
```

### Frontend Components

```
js/
├── auth.js              # Authentication module (API client)
├── ui-components.js     # UI components (modals, feedback, etc.)
├── dashboard.js         # Dashboard page functionality
└── main-with-auth.js    # Updated main script with auth

css/
├── ui-components.css    # Component styles
└── dashboard.css        # Dashboard styles

dashboard.html          # User dashboard page
index.html             # Updated homepage with auth UI
```

## Account Types & Limits

| Account Type | Daily Limit | Statement Storage | Special Features |
|--------------|-------------|-------------------|------------------|
| Anonymous    | 3 PDFs      | No                | No signup needed |
| Free Account | 10 PDFs     | 1 hour            | Earn extra via feedback |
| Premium      | Unlimited   | Extended          | Coming soon |

## Getting Started

### 1. Install Backend Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 2. Initialize Database

```bash
python init_db.py
```

### 3. Run Backend Server

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 5000
```

### 4. Test the Setup

```bash
python test_setup.py
```

## API Endpoints

### Authentication

- `POST /api/auth/register` - Create new account
- `POST /api/auth/login` - Login to existing account
- `GET /api/auth/profile` - Get user profile
- `POST /api/auth/refresh` - Refresh access token
- `GET /api/auth/session` - Get/create anonymous session

### Statements

- `GET /api/check-limit` - Check conversion limits
- `POST /api/convert` - Convert PDF to CSV
- `GET /api/user/statements` - Get saved statements
- `GET /api/statement/{id}/download` - Download converted file

### Feedback

- `POST /api/feedback` - Submit feedback
- `GET /api/feedback/stats` - Get feedback statistics

## Frontend Integration

### Check Conversion Limits

```javascript
// The UI automatically checks and displays limits
UploadLimitUI.checkAndShow();
```

### Show Login/Register Modal

```javascript
// Show login modal
AuthModal.showModal('login');

// Show register modal
AuthModal.showModal('register');
```

### Authentication State

```javascript
// Check if user is authenticated
const isAuth = await Auth.isAuthenticated();

// Get current user
const user = await Auth.getCurrentUser();
```

### Feedback System

After a successful conversion, the feedback component automatically appears:

```javascript
FeedbackComponent.show(statementId);
```

Free users see: "Rate your experience and get 2 extra conversions today!"

## Security Features

1. **Password Security**
   - Bcrypt hashing with salt rounds
   - Minimum 8 characters required
   - Must contain uppercase, lowercase, and number

2. **JWT Tokens**
   - Access token: 30 minutes expiry
   - Refresh token: 7 days expiry
   - Automatic token refresh

3. **Rate Limiting**
   - IP-based tracking for anonymous users
   - Session-based fallback
   - Daily reset at midnight

4. **File Security**
   - Unique filenames with UUID
   - Automatic deletion after 1 hour
   - Secure file storage directory

## Database Schema

### Users Table
- `id`: Primary key
- `email`: Unique email address
- `password_hash`: Bcrypt hashed password
- `account_type`: free/premium
- `daily_generations`: Generation counter
- `last_generation_reset`: Last reset timestamp
- `created_at`: Account creation date

### Statements Table
- `id`: Primary key
- `user_id`: Foreign key to users
- `filename`: Original filename
- `file_path`: Server storage path
- `created_at`: Upload timestamp
- `expires_at`: Deletion timestamp

### Feedback Table
- `id`: Primary key
- `user_id`: Foreign key to users
- `statement_id`: Foreign key to statements
- `rating`: 1-5 star rating
- `comment`: Optional feedback text
- `bonus_granted`: Extra generations given
- `created_at`: Feedback timestamp

### Generation Tracking Table
- `id`: Primary key
- `identifier`: IP address or session ID
- `generation_count`: Daily counter
- `date`: Current date
- `last_updated`: Last generation time

## Maintenance

### Clean Expired Statements

The system automatically deletes expired statements. To manually clean:

```python
from backend.models.database import cleanup_expired_statements
cleanup_expired_statements()
```

### Reset Daily Limits

Limits reset automatically at midnight. To manually reset:

```python
from backend.models.database import reset_daily_limits
reset_daily_limits()
```

## Troubleshooting

### Backend Won't Start
- Ensure Python 3.7+ is installed
- Check all dependencies: `pip install -r requirements.txt`
- Verify port 5000 is available

### Database Errors
- Run `python init_db.py` to reinitialize
- Check file permissions on `statements.db`

### Authentication Issues
- Clear browser localStorage
- Check JWT secret key is set
- Verify CORS settings for your domain

### File Upload Errors
- Ensure `uploads/` directory exists and is writable
- Check file size limits
- Verify PDF mime type validation

## Future Enhancements

1. **Premium Tiers**
   - Multiple subscription levels
   - Batch processing
   - API access
   - Extended storage

2. **Enhanced Features**
   - Email verification
   - Password reset
   - Social login
   - Export history

3. **Admin Dashboard**
   - User management
   - Usage analytics
   - System monitoring
   - Feedback review

## Support

For issues or questions:
- Check the test scripts for examples
- Review API documentation
- Submit issues to the repository