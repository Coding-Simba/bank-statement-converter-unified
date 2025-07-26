"""Feedback API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

from ..models.database import get_db, User, Statement, Feedback
from ..middleware.auth_middleware import get_user_or_session

router = APIRouter(prefix="/api", tags=["feedback"])


class FeedbackCreate(BaseModel):
    statement_id: Optional[int]
    rating: int  # 1-5
    comment: Optional[str]


class FeedbackResponse(BaseModel):
    id: int
    rating: int
    comment: Optional[str]
    created_at: datetime
    
    class Config:
        orm_mode = True


@router.post("/feedback", response_model=FeedbackResponse)
async def create_feedback(
    feedback_data: FeedbackCreate,
    request: Request,
    db: Session = Depends(get_db)
):
    """Submit feedback for a conversion."""
    user, session_id = get_user_or_session(request)
    
    # Validate rating
    if feedback_data.rating < 1 or feedback_data.rating > 5:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Rating must be between 1 and 5"
        )
    
    # If statement_id is provided, verify access
    if feedback_data.statement_id:
        statement = db.query(Statement).filter(
            Statement.id == feedback_data.statement_id
        ).first()
        
        if not statement:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Statement not found"
            )
        
        # Check access permissions
        if user and statement.user_id != user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        elif not user and statement.session_id != session_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
    
    # Create feedback
    feedback = Feedback(
        user_id=user.id if user else None,
        statement_id=feedback_data.statement_id,
        session_id=session_id if not user else None,
        rating=feedback_data.rating,
        comment=feedback_data.comment
    )
    
    db.add(feedback)
    db.commit()
    db.refresh(feedback)
    
    return FeedbackResponse(
        id=feedback.id,
        rating=feedback.rating,
        comment=feedback.comment,
        created_at=feedback.created_at
    )


@router.get("/feedback/stats")
async def get_feedback_stats(db: Session = Depends(get_db)):
    """Get feedback statistics (admin endpoint)."""
    # TODO: Add admin authentication
    
    total_feedback = db.query(Feedback).count()
    avg_rating = db.query(func.avg(Feedback.rating)).scalar() or 0
    
    rating_distribution = db.query(
        Feedback.rating,
        func.count(Feedback.rating)
    ).group_by(Feedback.rating).all()
    
    return {
        "total_feedback": total_feedback,
        "average_rating": round(avg_rating, 2),
        "rating_distribution": {
            str(rating): count 
            for rating, count in rating_distribution
        }
    }