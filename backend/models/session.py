"""Session model for tracking active user sessions."""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text
from sqlalchemy.orm import relationship
from models.database import Base


class Session(Base):
    """User session tracking model."""
    __tablename__ = "sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    session_id = Column(String(255), unique=True, nullable=False, index=True)
    
    # Device information
    device_info = Column(Text, nullable=True)  # User agent string
    device_type = Column(String(50), nullable=True)  # desktop, mobile, tablet
    browser = Column(String(50), nullable=True)  # Chrome, Firefox, Safari, etc.
    os = Column(String(50), nullable=True)  # Windows, macOS, Linux, iOS, Android
    
    # Network information
    ip_address = Column(String(50), nullable=True)
    
    # Session metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_accessed = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    
    # Session flags
    is_remember_me = Column(Boolean, default=False, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="sessions")
    
    def update_last_accessed(self):
        """Update the last accessed timestamp."""
        self.last_accessed = datetime.utcnow()
    
    def is_expired(self):
        """Check if the session has expired."""
        return datetime.utcnow() > self.expires_at
    
    def revoke(self):
        """Revoke the session."""
        self.is_active = False
        self.expires_at = datetime.utcnow()