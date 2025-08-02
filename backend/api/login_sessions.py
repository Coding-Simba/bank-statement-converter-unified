"""Login session tracking API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_
from typing import List, Optional
from datetime import datetime, timedelta
import secrets
import json

from models.database import get_db, User
from models.login_session import LoginSession
from middleware.auth_middleware import get_current_user
from dependencies import get_current_active_user


router = APIRouter(prefix="/api/user", tags=["sessions"])


def get_client_info(request: Request):
    """Extract client information from request."""
    # Get IP address
    ip_address = request.client.host
    if request.headers.get("X-Forwarded-For"):
        ip_address = request.headers.get("X-Forwarded-For").split(",")[0].strip()
    elif request.headers.get("X-Real-IP"):
        ip_address = request.headers.get("X-Real-IP")
    
    # Get user agent
    user_agent = request.headers.get("User-Agent", "Unknown")
    
    return {
        "ip_address": ip_address,
        "user_agent": user_agent
    }


def create_login_session(
    user_id: int,
    request: Request,
    db: Session,
    login_successful: bool = True
) -> LoginSession:
    """Create a new login session record."""
    client_info = get_client_info(request)
    parsed_ua = LoginSession.parse_user_agent(client_info["user_agent"])
    
    session = LoginSession(
        user_id=user_id,
        session_id=secrets.token_urlsafe(32),
        ip_address=client_info["ip_address"],
        user_agent=client_info["user_agent"],
        device_type=parsed_ua["device_type"],
        browser=parsed_ua["browser"],
        os=parsed_ua["os"],
        login_successful=login_successful,
        is_active=login_successful
    )
    
    db.add(session)
    db.commit()
    db.refresh(session)
    
    return session


def update_session_activity(
    user_id: int,
    session_id: Optional[str],
    db: Session
):
    """Update last activity time for active session."""
    if session_id:
        session = db.query(LoginSession).filter(
            and_(
                LoginSession.user_id == user_id,
                LoginSession.session_id == session_id,
                LoginSession.is_active == True
            )
        ).first()
        
        if session:
            session.last_activity = datetime.utcnow()
            db.commit()


def end_login_session(
    user_id: int,
    session_id: Optional[str],
    logout_type: str,
    db: Session
):
    """End a login session."""
    if session_id:
        session = db.query(LoginSession).filter(
            and_(
                LoginSession.user_id == user_id,
                LoginSession.session_id == session_id,
                LoginSession.is_active == True
            )
        ).first()
        
        if session:
            session.is_active = False
            session.logged_out_at = datetime.utcnow()
            session.logout_type = logout_type
            db.commit()


@router.get("/sessions")
async def get_login_sessions(
    limit: int = 10,
    include_failed: bool = False,
    current_user: User = Depends(get_current_user),
    request: Request = None,
    db: Session = Depends(get_db)
):
    """Get recent login sessions for the current user."""
    # Build query
    query = db.query(LoginSession).filter(
        LoginSession.user_id == current_user.id
    )
    
    # Filter failed attempts if not requested
    if not include_failed:
        query = query.filter(LoginSession.login_successful == True)
    
    # Get recent sessions
    sessions = query.order_by(desc(LoginSession.created_at)).limit(limit).all()
    
    # Get current session info to mark it
    current_ip = get_client_info(request)["ip_address"] if request else None
    
    # Convert to dict and mark current session
    sessions_data = []
    for session in sessions:
        session_dict = session.to_dict()
        
        # Mark current session
        if session.is_active and session.ip_address == current_ip:
            session_dict["is_current"] = True
        
        # Format location
        if session.city and session.country:
            session_dict["location"] = f"{session.city}, {session.country}"
        elif session.country:
            session_dict["location"] = session.country
        else:
            session_dict["location"] = "Unknown location"
        
        sessions_data.append(session_dict)
    
    return {
        "sessions": sessions_data,
        "total_sessions": len(sessions_data),
        "active_sessions": sum(1 for s in sessions_data if s["is_active"])
    }


@router.get("/sessions/active")
async def get_active_sessions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all active sessions for the current user."""
    sessions = db.query(LoginSession).filter(
        and_(
            LoginSession.user_id == current_user.id,
            LoginSession.is_active == True
        )
    ).order_by(desc(LoginSession.last_activity)).all()
    
    return {
        "active_sessions": [session.to_dict() for session in sessions],
        "count": len(sessions)
    }


@router.post("/sessions/{session_id}/terminate")
async def terminate_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Terminate a specific session."""
    session = db.query(LoginSession).filter(
        and_(
            LoginSession.user_id == current_user.id,
            LoginSession.session_id == session_id,
            LoginSession.is_active == True
        )
    ).first()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found or already terminated"
        )
    
    # End the session
    session.is_active = False
    session.logged_out_at = datetime.utcnow()
    session.logout_type = "forced"
    db.commit()
    
    return {"message": "Session terminated successfully"}


@router.post("/sessions/terminate-all")
async def terminate_all_sessions(
    except_current: bool = True,
    current_user: User = Depends(get_current_user),
    request: Request = None,
    db: Session = Depends(get_db)
):
    """Terminate all sessions for the current user."""
    query = db.query(LoginSession).filter(
        and_(
            LoginSession.user_id == current_user.id,
            LoginSession.is_active == True
        )
    )
    
    # Optionally exclude current session
    if except_current and request:
        current_ip = get_client_info(request)["ip_address"]
        # Find most recent session from current IP
        current_session = db.query(LoginSession).filter(
            and_(
                LoginSession.user_id == current_user.id,
                LoginSession.ip_address == current_ip,
                LoginSession.is_active == True
            )
        ).order_by(desc(LoginSession.created_at)).first()
        
        if current_session:
            query = query.filter(LoginSession.id != current_session.id)
    
    # Terminate all matching sessions
    sessions = query.all()
    terminated_count = 0
    
    for session in sessions:
        session.is_active = False
        session.logged_out_at = datetime.utcnow()
        session.logout_type = "forced_all"
        terminated_count += 1
    
    db.commit()
    
    return {
        "message": f"Terminated {terminated_count} session(s)",
        "terminated_count": terminated_count
    }


@router.get("/sessions/stats")
async def get_session_stats(
    days: int = 30,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get session statistics for the user."""
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    
    # Get all sessions in timeframe
    sessions = db.query(LoginSession).filter(
        and_(
            LoginSession.user_id == current_user.id,
            LoginSession.created_at >= cutoff_date
        )
    ).all()
    
    # Calculate statistics
    stats = {
        "total_logins": len([s for s in sessions if s.login_successful]),
        "failed_attempts": len([s for s in sessions if not s.login_successful]),
        "unique_ips": len(set(s.ip_address for s in sessions)),
        "unique_devices": len(set(f"{s.device_type}-{s.browser}-{s.os}" for s in sessions)),
        "device_breakdown": {},
        "browser_breakdown": {},
        "location_breakdown": {},
        "hourly_pattern": [0] * 24
    }
    
    # Device breakdown
    for session in sessions:
        if session.login_successful:
            stats["device_breakdown"][session.device_type] = \
                stats["device_breakdown"].get(session.device_type, 0) + 1
            stats["browser_breakdown"][session.browser] = \
                stats["browser_breakdown"].get(session.browser, 0) + 1
            
            # Location
            location = session.country or "Unknown"
            stats["location_breakdown"][location] = \
                stats["location_breakdown"].get(location, 0) + 1
            
            # Hourly pattern
            hour = session.created_at.hour
            stats["hourly_pattern"][hour] += 1
    
    return stats


# Hook these functions into auth endpoints
def track_login(user_id: int, request: Request, db: Session, success: bool = True):
    """Track a login attempt."""
    return create_login_session(user_id, request, db, success)


def track_logout(user_id: int, session_id: str, db: Session):
    """Track a logout."""
    end_login_session(user_id, session_id, "manual", db)