"""Login session model for tracking user login history."""

from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Index
from sqlalchemy.orm import relationship
from datetime import datetime
from models.database import Base


class LoginSession(Base):
    """Track user login sessions for security and analytics."""
    
    __tablename__ = "login_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # Session information
    session_id = Column(String, unique=True, index=True)
    ip_address = Column(String)
    user_agent = Column(String)
    
    # Location data (optional, can be populated from IP)
    country = Column(String)
    city = Column(String)
    
    # Device information
    device_type = Column(String)  # desktop, mobile, tablet
    browser = Column(String)
    os = Column(String)
    
    # Session status
    is_active = Column(Boolean, default=True)
    login_successful = Column(Boolean, default=True)
    logout_type = Column(String)  # manual, timeout, forced
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    last_activity = Column(DateTime, default=datetime.utcnow)
    logged_out_at = Column(DateTime)
    
    # Security
    suspicious_activity = Column(Boolean, default=False)
    failed_attempts = Column(Integer, default=0)
    
    # Relationships
    user = relationship("User", back_populates="login_sessions")
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_user_sessions', 'user_id', 'created_at'),
        Index('idx_active_sessions', 'user_id', 'is_active'),
        Index('idx_session_activity', 'last_activity'),
    )
    
    def to_dict(self):
        """Convert session to dictionary for API responses."""
        return {
            "id": self.id,
            "session_id": self.session_id[:8] + "..." if self.session_id else None,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "country": self.country,
            "city": self.city,
            "device_type": self.device_type,
            "browser": self.browser,
            "os": self.os,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_activity": self.last_activity.isoformat() if self.last_activity else None,
            "logged_out_at": self.logged_out_at.isoformat() if self.logged_out_at else None,
            "is_current": False  # Will be set by API based on current session
        }
    
    @classmethod
    def parse_user_agent(cls, user_agent_string):
        """Parse user agent to extract device, browser, and OS information."""
        if not user_agent_string:
            return {
                "device_type": "unknown",
                "browser": "unknown",
                "os": "unknown"
            }
        
        # Simple parsing - in production, use a library like user-agents
        device_type = "desktop"
        if "Mobile" in user_agent_string:
            device_type = "mobile"
        elif "Tablet" in user_agent_string or "iPad" in user_agent_string:
            device_type = "tablet"
        
        # Browser detection
        browser = "unknown"
        if "Chrome" in user_agent_string and "Edg" not in user_agent_string:
            browser = "Chrome"
        elif "Firefox" in user_agent_string:
            browser = "Firefox"
        elif "Safari" in user_agent_string and "Chrome" not in user_agent_string:
            browser = "Safari"
        elif "Edg" in user_agent_string:
            browser = "Edge"
        
        # OS detection
        os = "unknown"
        if "Windows" in user_agent_string:
            os = "Windows"
        elif "Mac OS" in user_agent_string or "Macintosh" in user_agent_string:
            os = "macOS"
        elif "Linux" in user_agent_string:
            os = "Linux"
        elif "Android" in user_agent_string:
            os = "Android"
        elif "iOS" in user_agent_string or "iPhone" in user_agent_string:
            os = "iOS"
        
        return {
            "device_type": device_type,
            "browser": browser,
            "os": os
        }