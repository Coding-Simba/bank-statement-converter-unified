"""Statement deletion API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Dict, Any

from models.database import get_db, User, Statement
from dependencies import get_current_user

router = APIRouter()

@router.delete("/statement/{statement_id}")
async def delete_statement(
    statement_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, str]:
    """Soft delete a statement."""
    
    # Get the statement
    statement = db.query(Statement).filter(
        Statement.id == statement_id,
        Statement.user_id == current_user.id
    ).first()
    
    if not statement:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Statement not found or you don't have permission to delete it"
        )
    
    # Check if already deleted
    if statement.is_deleted:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Statement is already deleted"
        )
    
    # Soft delete the statement
    statement.is_deleted = True
    statement.deleted_at = datetime.utcnow()
    
    try:
        db.commit()
        return {"message": "Statement deleted successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete statement"
        )

@router.post("/statement/{statement_id}/restore")
async def restore_statement(
    statement_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, str]:
    """Restore a soft-deleted statement."""
    
    # Get the statement
    statement = db.query(Statement).filter(
        Statement.id == statement_id,
        Statement.user_id == current_user.id
    ).first()
    
    if not statement:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Statement not found or you don't have permission to restore it"
        )
    
    # Check if not deleted
    if not statement.is_deleted:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Statement is not deleted"
        )
    
    # Restore the statement
    statement.is_deleted = False
    statement.deleted_at = None
    
    try:
        db.commit()
        return {"message": "Statement restored successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to restore statement"
        )

@router.delete("/statements/bulk")
async def bulk_delete_statements(
    statement_ids: list[int],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Bulk soft delete multiple statements."""
    
    # Get all statements that belong to the user
    statements = db.query(Statement).filter(
        Statement.id.in_(statement_ids),
        Statement.user_id == current_user.id,
        Statement.is_deleted == False
    ).all()
    
    if not statements:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No statements found or you don't have permission to delete them"
        )
    
    # Soft delete all statements
    deleted_count = 0
    for statement in statements:
        statement.is_deleted = True
        statement.deleted_at = datetime.utcnow()
        deleted_count += 1
    
    try:
        db.commit()
        return {
            "message": f"Successfully deleted {deleted_count} statements",
            "deleted_count": deleted_count
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete statements"
        )