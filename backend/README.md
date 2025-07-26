# Bank Statement Converter Backend

This is the backend API for the Bank Statement Converter application, built with FastAPI and SQLAlchemy.

## Features

- **User Authentication**: JWT-based authentication with access and refresh tokens
- **Account Types**: 
  - No Account: 3 PDFs/day (tracked by IP/session)
  - Free Account: 10 PDFs/day
  - Premium: Unlimited conversions
- **Statement Management**: Convert PDFs to CSV with automatic cleanup after 1 hour
- **Rate Limiting**: Daily generation limits based on account type
- **Feedback System**: Users can rate and comment on conversions

## Installation

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Copy `.env.example` to `.env` and configure:
```bash
cp .env.example .env
```

4. Initialize the database:
```bash
python init_db.py
```

## Running the Server

```bash
# Development mode with auto-reload
uvicorn main:app --reload --host 0.0.0.0 --port 5000

# Or using the Python module
python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 5000
```

## API Endpoints

### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login user
- `GET /api/auth/profile` - Get user profile (auth required)
- `POST /api/auth/logout` - Logout user
- `POST /api/auth/refresh` - Refresh access token
- `GET /api/auth/session` - Get/create session for anonymous users

### Statements
- `GET /api/check-limit` - Check generation limit
- `POST /api/convert` - Convert PDF to CSV
- `GET /api/user/statements` - Get user's statements (auth required)
- `GET /api/statement/{id}/download` - Download converted statement

### Feedback
- `POST /api/feedback` - Submit feedback
- `GET /api/feedback/stats` - Get feedback statistics

### Utility
- `GET /` - API information
- `GET /health` - Health check

## Database Schema

### Users Table
- `id`: Primary key
- `email`: Unique email address
- `password_hash`: Bcrypt hashed password
- `account_type`: free/premium
- `daily_generations`: Current day's generation count
- `last_generation_reset`: Last reset timestamp

### Statements Table
- `id`: Primary key
- `user_id`: Foreign key to users (nullable)
- `session_id`: For anonymous users
- `filename`: Generated filename
- `file_path`: Full path to file
- `original_filename`: User's filename
- `expires_at`: Auto-deletion time

### Feedback Table
- `id`: Primary key
- `user_id`: Foreign key to users (nullable)
- `statement_id`: Foreign key to statements
- `rating`: 1-5 star rating
- `comment`: Optional text feedback

### Generation Tracking Table
- `id`: Primary key
- `ip_address`: Client IP
- `session_id`: Session identifier
- `generation_count`: Daily count
- `date`: Current date

## Security

- Passwords are hashed using bcrypt
- JWT tokens for authentication
- Session IDs for anonymous user tracking
- File access validation
- Rate limiting to prevent abuse

## TODO

- Implement actual PDF to CSV conversion logic
- Add admin endpoints
- Implement file virus scanning
- Add comprehensive logging
- Set up automated tests
- Add API documentation (Swagger/ReDoc)
- Implement webhook notifications
- Add background job queue for conversions