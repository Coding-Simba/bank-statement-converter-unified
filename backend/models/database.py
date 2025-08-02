"""Database configuration and models for the bank statement converter."""

from datetime import datetime, timedelta
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Float, Text, ForeignKey, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, scoped_session
from sqlalchemy.sql import func
import os
from pathlib import Path
import json

# Database configuration
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATABASE_PATH = BASE_DIR / 'data' / 'bank_converter.db'
DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)

DATABASE_URL = f"sqlite:///{DATABASE_PATH}"

# Create engine and session
engine = create_engine(DATABASE_URL, echo=False, connect_args={"check_same_thread": False})
SessionLocal = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))

# Base class for models
Base = declarative_base()

class User(Base):
    """User model for authentication and account management."""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=True)  # Nullable for OAuth users
    full_name = Column(String(255), nullable=True)
    company_name = Column(String(255), nullable=True)
    account_type = Column(String(50), default="free", nullable=False)  # no_account, free, premium
    subscription_status = Column(String(50), default="free", nullable=False)  # free, trial, active, cancelled, expired
    subscription_plan = Column(String(50), nullable=True)  # starter, professional, business
    subscription_expires_at = Column(DateTime, nullable=True)
    stripe_customer_id = Column(String(255), unique=True, nullable=True)
    auth_provider = Column(String(50), default="email", nullable=False)  # email, google, microsoft
    provider_user_id = Column(String(255), nullable=True)  # OAuth provider's user ID
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    daily_generations = Column(Integer, default=0, nullable=False)
    last_generation_reset = Column(DateTime, default=datetime.utcnow, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    email_verified = Column(Boolean, default=False, nullable=False)
    email_verification_token = Column(String(255), nullable=True)
    password_reset_token = Column(String(255), nullable=True)
    password_reset_expires = Column(DateTime, nullable=True)
    refresh_token_family = Column(String(255), nullable=True)  # For refresh token rotation
    refresh_token_version = Column(Integer, default=1, nullable=False)  # Token version tracking
    
    # Settings fields
    timezone = Column(String(50), default="UTC", nullable=False)
    two_factor_secret = Column(String(255), nullable=True)
    two_factor_enabled = Column(Boolean, default=False, nullable=False)
    two_factor_backup_codes = Column(Text, nullable=True)  # JSON array of backup codes
    api_key = Column(String(255), unique=True, nullable=True)
    api_key_created_at = Column(DateTime, nullable=True)
    notification_preferences = Column(Text, nullable=True)  # JSON object
    pending_email = Column(String(255), nullable=True)
    pending_email_token = Column(String(255), nullable=True)
    pending_email_expires = Column(DateTime, nullable=True)
    
    # Relationships
    statements = relationship("Statement", back_populates="user", cascade="all, delete-orphan")
    feedback = relationship("Feedback", back_populates="user", cascade="all, delete-orphan")
    subscriptions = relationship("Subscription", back_populates="user", cascade="all, delete-orphan")
    usage_logs = relationship("UsageLog", back_populates="user", cascade="all, delete-orphan")
    payments = relationship("Payment", back_populates="user", cascade="all, delete-orphan")
    # sessions = relationship("Session", back_populates="user", cascade="all, delete-orphan")  # Commented to avoid circular dependency
    
    def reset_daily_limit_if_needed(self):
        """Reset daily generation count if a new day has started."""
        now = datetime.utcnow()
        if self.last_generation_reset.date() < now.date():
            self.daily_generations = 0
            self.last_generation_reset = now
            return True
        return False
    
    def can_generate(self):
        """Check if user can generate based on their account type and daily limit."""
        self.reset_daily_limit_if_needed()
        
        if self.account_type == "premium":
            return True
        elif self.account_type == "free":
            return self.daily_generations < 10
        else:  # no_account
            return self.daily_generations < 3
    
    def get_daily_limit(self):
        """Get the daily generation limit based on account type."""
        limits = {
            "no_account": 3,
            "free": 10,
            "premium": float('inf')
        }
        return limits.get(self.account_type, 3)
    
    def get_notification_preferences(self):
        """Get notification preferences as a dictionary."""
        if self.notification_preferences:
            try:
                return json.loads(self.notification_preferences)
            except json.JSONDecodeError:
                pass
        # Return defaults if not set or invalid
        return {
            "security_alerts": True,
            "product_updates": True,
            "usage_reports": False,
            "marketing_emails": False
        }
    
    def set_notification_preferences(self, preferences):
        """Set notification preferences from a dictionary."""
        self.notification_preferences = json.dumps(preferences)
    
    def get_backup_codes(self):
        """Get 2FA backup codes as a list."""
        if self.two_factor_backup_codes:
            try:
                return json.loads(self.two_factor_backup_codes)
            except json.JSONDecodeError:
                pass
        return []
    
    def set_backup_codes(self, codes):
        """Set 2FA backup codes from a list."""
        self.two_factor_backup_codes = json.dumps(codes)


class Statement(Base):
    """Statement model for storing converted bank statements."""
    __tablename__ = "statements"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # Nullable for anonymous users
    session_id = Column(String(255), nullable=True, index=True)  # For tracking anonymous users
    filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer, nullable=True)
    original_filename = Column(String(255), nullable=True)
    bank = Column(String(255), nullable=True)
    validated = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False)
    deleted_at = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="statements")
    feedback = relationship("Feedback", back_populates="statement", cascade="all, delete-orphan")
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Set expiration to 1 hour from creation if not specified
        if not self.expires_at:
            self.expires_at = datetime.utcnow() + timedelta(hours=1)
    
    def is_expired(self):
        """Check if the statement has expired."""
        return datetime.utcnow() > self.expires_at
    
    def mark_deleted(self):
        """Mark the statement as deleted."""
        self.is_deleted = True


class Feedback(Base):
    """Feedback model for user feedback on converted statements."""
    __tablename__ = "feedback"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    statement_id = Column(Integer, ForeignKey("statements.id"), nullable=True)
    session_id = Column(String(255), nullable=True, index=True)  # For anonymous feedback
    rating = Column(Integer, nullable=False)  # 1-5 star rating
    comment = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="feedback")
    statement = relationship("Statement", back_populates="feedback")


class GenerationTracking(Base):
    """Track generation attempts for rate limiting."""
    __tablename__ = "generation_tracking"
    
    id = Column(Integer, primary_key=True, index=True)
    ip_address = Column(String(45), nullable=True, index=True)  # Support IPv6
    session_id = Column(String(255), nullable=True, index=True)
    generation_count = Column(Integer, default=0, nullable=False)
    date = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_generation = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    @classmethod
    def get_or_create(cls, session, ip_address=None, session_id=None):
        """Get or create a tracking record for today."""
        today = datetime.utcnow().date()
        
        # Try to find existing record
        query = session.query(cls)
        if ip_address:
            query = query.filter_by(ip_address=ip_address)
        if session_id:
            query = query.filter_by(session_id=session_id)
        
        tracking = query.filter(func.date(cls.date) == today).first()
        
        if not tracking:
            tracking = cls(
                ip_address=ip_address,
                session_id=session_id,
                generation_count=0,
                date=datetime.utcnow()
            )
            session.add(tracking)
            session.commit()
        
        return tracking
    
    def can_generate_anonymous(self):
        """Check if anonymous user can generate (3 per day limit)."""
        return self.generation_count < 3
    
    def increment_count(self):
        """Increment the generation count."""
        self.generation_count += 1
        self.last_generation = datetime.utcnow()


class Plan(Base):
    """Plan model for different subscription tiers."""
    __tablename__ = "plans"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False)
    display_name = Column(String(100), nullable=False)
    monthly_pages = Column(Integer, nullable=False)
    monthly_price = Column(Float, nullable=False)
    yearly_price = Column(Float, nullable=True)
    stripe_monthly_price_id = Column(String(255), nullable=True)
    stripe_yearly_price_id = Column(String(255), nullable=True)
    features = Column(Text, nullable=True)  # JSON string of features
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Subscription(Base):
    """User subscription model."""
    __tablename__ = "subscriptions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    stripe_subscription_id = Column(String(255), unique=True, nullable=False)
    stripe_customer_id = Column(String(255), nullable=False)
    plan_id = Column(String(50), nullable=False)  # references plan name
    status = Column(String(50), nullable=False)  # active, canceled, past_due, etc
    current_period_start = Column(DateTime, nullable=False)
    current_period_end = Column(DateTime, nullable=False)
    cancel_at_period_end = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="subscriptions")


class UsageLog(Base):
    """Track page usage for each user."""
    __tablename__ = "usage_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    pages = Column(Integer, default=1)
    statement_id = Column(Integer, ForeignKey("statements.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="usage_logs")
    statement = relationship("Statement")


class Payment(Base):
    """Payment history model."""
    __tablename__ = "payments"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    stripe_payment_intent_id = Column(String(255), unique=True, nullable=False)
    amount = Column(Float, nullable=False)
    currency = Column(String(10), default="usd")
    status = Column(String(50), nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="payments")


# Create tables
def init_db():
    """Initialize the database and create all tables."""
    Base.metadata.create_all(bind=engine)


# Database session management
def get_db():
    """Get a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


if __name__ == "__main__":
    # Initialize database when running this file directly
    init_db()
    print(f"Database initialized at: {DATABASE_PATH}")