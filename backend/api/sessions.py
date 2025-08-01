"""Session management API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session as DBSession
from sqlalchemy import and_
from typing import List
from datetime import datetime, timedelta
from user_agents import parse

from models.database import get_db, User
from models.session import Session
from middleware.auth_middleware import get_current_user
from pydantic import BaseModel

router = APIRouter(prefix="/api/sessions", tags=["sessions"])


class SessionInfo(BaseModel):
    """Session information model."""
    id: int
    session_id: str
    device_type: str
    browser: str
    os: str
    ip_address: str
    created_at: datetime
    last_accessed: datetime
    expires_at: datetime
    is_remember_me: bool
    is_current: bool


class SessionListResponse(BaseModel):
    """Response model for session list."""
    sessions: List[SessionInfo]
    total: int


def parse_user_agent(user_agent_string: str):
    """Parse user agent string to extract device info."""
    ua = parse(user_agent_string)
    
    # Determine device type
    if ua.is_mobile:
        device_type = "mobile"
    elif ua.is_tablet:
        device_type = "tablet"
    else:
        device_type = "desktop"
    
    # Get browser and OS
    browser = ua.browser.family if ua.browser.family else "Unknown"
    os = ua.os.family if ua.os.family else "Unknown"
    
    return {
        "device_type": device_type,
        "browser": browser,
        "os": os
    }


@router.get("/", response_model=SessionListResponse)
async def get_user_sessions(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db)
):
    """Get all active sessions for the current user."""
    
    # Get current session ID from request
    current_session_id = getattr(request.state, "session_id", None)
    
    # Query active sessions
    sessions = db.query(Session).filter(
        and_(
            Session.user_id == current_user.id,
            Session.is_active == True,
            Session.expires_at > datetime.utcnow()
        )
    ).order_by(Session.last_accessed.desc()).all()
    
    # Format session data
    session_list = []
    for session in sessions:
        session_info = SessionInfo(
            id=session.id,
            session_id=session.session_id,
            device_type=session.device_type or "Unknown",
            browser=session.browser or "Unknown",
            os=session.os or "Unknown",
            ip_address=session.ip_address or "Unknown",
            created_at=session.created_at,
            last_accessed=session.last_accessed,
            expires_at=session.expires_at,
            is_remember_me=session.is_remember_me,
            is_current=(session.session_id == current_session_id)
        )
        session_list.append(session_info)
    
    return SessionListResponse(
        sessions=session_list,
        total=len(session_list)
    )


@router.delete("/{session_id}")
async def revoke_session(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db)
):
    """Revoke a specific session."""
    
    # Find the session
    session = db.query(Session).filter(
        and_(
            Session.id == session_id,
            Session.user_id == current_user.id
        )
    ).first()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    # Revoke the session
    session.revoke()
    db.commit()
    
    return {"message": "Session revoked successfully"}


@router.delete("/")
async def revoke_all_sessions(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db)
):
    """Revoke all sessions except the current one."""
    
    # Get current session ID
    current_session_id = getattr(request.state, "session_id", None)
    
    # Revoke all other sessions
    sessions = db.query(Session).filter(
        and_(
            Session.user_id == current_user.id,
            Session.session_id != current_session_id,
            Session.is_active == True
        )
    ).all()
    
    for session in sessions:
        session.revoke()
    
    db.commit()
    
    return {
        "message": f"Revoked {len(sessions)} session(s)",
        "revoked_count": len(sessions)
    }


def create_session(
    user_id: int,
    session_id: str,
    user_agent: str,
    ip_address: str,
    is_remember_me: bool,
    db: DBSession
) -> Session:
    """Create a new session for a user."""
    
    # Parse user agent
    device_info = parse_user_agent(user_agent)
    
    # Calculate expiry
    if is_remember_me:
        expires_at = datetime.utcnow() + timedelta(days=90)
    else:
        expires_at = datetime.utcnow() + timedelta(hours=24)
    
    # Create session
    session = Session(
        user_id=user_id,
        session_id=session_id,
        device_info=user_agent,
        device_type=device_info["device_type"],
        browser=device_info["browser"],
        os=device_info["os"],
        ip_address=ip_address,
        expires_at=expires_at,
        is_remember_me=is_remember_me
    )
    
    db.add(session)
    db.commit()
    
    return session