"""Recent statements API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from datetime import datetime, timedelta
from typing import Optional, List
from pydantic import BaseModel

from models.database import get_db, User, Statement
from dependencies import get_current_user_optional, get_current_user

router = APIRouter()

class StatementResponse(BaseModel):
    id: int
    original_filename: str
    bank: Optional[str]
    file_size: Optional[int]
    created_at: datetime
    validated: bool
    expires_at: datetime

    class Config:
        from_attributes = True

@router.get("/statements/recent", response_model=List[StatementResponse])
async def get_recent_statements(
    limit: int = Query(10, ge=1, le=50),
    offset: int = Query(0, ge=0),
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """Get recent statements for the current user or session."""
    
    # Build query based on whether user is authenticated
    if current_user:
        # Authenticated user - get their statements
        query = db.query(Statement).filter(
            Statement.user_id == current_user.id,
            or_(Statement.is_deleted == False, Statement.is_deleted == None)
        )
    else:
        # Anonymous user - use session_id from request
        # For now, return empty list for anonymous users
        # In production, you'd get session_id from cookies/headers
        return []
    
    # Get recent statements
    statements = query.order_by(
        Statement.created_at.desc()
    ).offset(offset).limit(limit).all()
    
    return statements

@router.get("/statements", response_model=List[StatementResponse])
async def get_all_statements(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    bank: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all statements for the current user with optional filters."""
    
    # Base query
    query = db.query(Statement).filter(
        Statement.user_id == current_user.id,
        or_(Statement.is_deleted == False, Statement.is_deleted == None)
    )
    
    # Apply filters
    if start_date:
        query = query.filter(Statement.created_at >= start_date)
    
    if end_date:
        query = query.filter(Statement.created_at <= end_date)
    
    if bank:
        query = query.filter(Statement.bank == bank)
    
    # Get statements
    statements = query.order_by(
        Statement.created_at.desc()
    ).offset(offset).limit(limit).all()
    
    return statements

@router.get("/statements/stats")
async def get_statement_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get statement statistics for the current user."""
    
    # Get unique banks
    banks = db.query(Statement.bank).filter(
        Statement.user_id == current_user.id,
        Statement.bank != None,
        or_(Statement.is_deleted == False, Statement.is_deleted == None)
    ).distinct().all()
    
    # Get statement count by month for the last 12 months
    twelve_months_ago = datetime.utcnow() - timedelta(days=365)
    
    # For SQLite, we need to use different date formatting
    from sqlalchemy import func
    
    monthly_stats = db.query(
        func.strftime("%Y-%m", Statement.created_at).label("month"),
        func.count(Statement.id).label("count")
    ).filter(
        Statement.user_id == current_user.id,
        Statement.created_at >= twelve_months_ago,
        or_(Statement.is_deleted == False, Statement.is_deleted == None)
    ).group_by("month").order_by("month").all()
    
    return {
        "banks": [bank[0] for bank in banks if bank[0]],
        "monthlyStats": [
            {"month": stat[0], "count": stat[1]}
            for stat in monthly_stats
        ],
        "totalStatements": db.query(func.count(Statement.id)).filter(
            Statement.user_id == current_user.id,
            or_(Statement.is_deleted == False, Statement.is_deleted == None)
        ).scalar() or 0
    }