"""Transaction validation API endpoints"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Optional
from datetime import datetime
import json
import os
import pandas as pd
from pydantic import BaseModel

from ..database import get_db
from ..models import Statement, User
from ..auth import get_current_user_optional
from ..auth import get_user_or_session

router = APIRouter()

class TransactionUpdate(BaseModel):
    date: str
    description: str
    amount: float
    balance: float

class ValidationUpdate(BaseModel):
    transactions: List[TransactionUpdate]

class ValidationResponse(BaseModel):
    id: int
    filename: str
    bank: Optional[str]
    transactions: List[Dict]
    created_at: datetime
    validated: bool
    validation_date: Optional[datetime]

@router.get("/statement/{statement_id}/validation", response_model=ValidationResponse)
async def get_validation_data(
    statement_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    """Get statement data for validation"""
    user, session_id = get_user_or_session(request)
    
    # Get statement
    statement = db.query(Statement).filter(Statement.id == statement_id).first()
    
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
        # Allow recent anonymous statements
        from datetime import datetime, timedelta
        if statement.created_at < datetime.utcnow() - timedelta(hours=1):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
    
    # Load transactions from CSV or stored data
    transactions = []
    
    # First check if we have validated transactions stored
    if statement.validated_data:
        transactions = json.loads(statement.validated_data)
    else:
        # Load from CSV file
        csv_path = statement.file_path
        if os.path.exists(csv_path):
            try:
                df = pd.read_csv(csv_path)
                # Convert to list of dicts
                for _, row in df.iterrows():
                    trans = {
                        'date': row.get('Date', ''),
                        'description': row.get('Description', ''),
                        'amount': float(row.get('Amount', 0)),
                        'balance': float(row.get('Balance', 0))
                    }
                    transactions.append(trans)
            except Exception as e:
                logger.error(f"Error reading CSV: {e}")
    
    # Detect bank from filename or content
    bank = None
    if statement.original_filename:
        filename_lower = statement.original_filename.lower()
        if 'westpac' in filename_lower:
            bank = 'Westpac'
        elif 'woodforest' in filename_lower:
            bank = 'Woodforest'
        elif 'citizens' in filename_lower:
            bank = 'Citizens Bank'
        elif 'suntrust' in filename_lower:
            bank = 'SunTrust'
        elif 'wells' in filename_lower and 'fargo' in filename_lower:
            bank = 'Wells Fargo'
        elif 'chase' in filename_lower:
            bank = 'Chase'
        elif 'bofa' in filename_lower or 'bank of america' in filename_lower:
            bank = 'Bank of America'
    
    return ValidationResponse(
        id=statement.id,
        filename=statement.original_filename,
        bank=bank,
        transactions=transactions,
        created_at=statement.created_at,
        validated=statement.validated,
        validation_date=statement.validation_date
    )

@router.put("/statement/{statement_id}/validation")
async def update_validation_data(
    statement_id: int,
    validation_data: ValidationUpdate,
    request: Request,
    db: Session = Depends(get_db)
):
    """Update validated transaction data"""
    user, session_id = get_user_or_session(request)
    
    # Get statement
    statement = db.query(Statement).filter(Statement.id == statement_id).first()
    
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
        if statement.created_at < datetime.utcnow() - timedelta(hours=1):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
    
    # Convert transactions to dict format
    transactions = []
    for trans in validation_data.transactions:
        transactions.append({
            'date': trans.date,
            'description': trans.description,
            'amount': trans.amount,
            'balance': trans.balance
        })
    
    # Store validated data
    statement.validated_data = json.dumps(transactions)
    statement.validated = True
    statement.validation_date = datetime.utcnow()
    
    # Update CSV file with validated data
    try:
        df = pd.DataFrame(transactions)
        df.columns = ['Date', 'Description', 'Amount', 'Balance']
        
        # Save to CSV
        df.to_csv(statement.file_path, index=False)
        
        db.commit()
        
        return {"message": "Validation data saved successfully"}
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error saving validation data: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save validation data"
        )

@router.get("/statement/{statement_id}/download")
async def download_validated_csv(
    statement_id: int,
    validated: bool = True,
    request: Request,
    db: Session = Depends(get_db)
):
    """Download the validated CSV file"""
    user, session_id = get_user_or_session(request)
    
    # Get statement
    statement = db.query(Statement).filter(Statement.id == statement_id).first()
    
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
        if statement.created_at < datetime.utcnow() - timedelta(hours=1):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
    
    # Check if file exists
    if not os.path.exists(statement.file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )
    
    # If requesting validated data and it exists, use it
    if validated and statement.validated_data:
        # Create CSV from validated data
        transactions = json.loads(statement.validated_data)
        df = pd.DataFrame(transactions)
        df.columns = ['Date', 'Description', 'Amount', 'Balance']
        
        # Generate filename
        original_name = os.path.splitext(statement.original_filename)[0]
        filename = f"{original_name}_validated.csv"
        
        # Return CSV content
        from fastapi.responses import Response
        csv_content = df.to_csv(index=False)
        
        return Response(
            content=csv_content,
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
    else:
        # Return original CSV
        from fastapi.responses import FileResponse
        return FileResponse(
            path=statement.file_path,
            media_type="text/csv",
            filename=statement.filename
        )

# Add validation status to statement list
@router.get("/statements/validation-status")
async def get_validation_status(
    request: Request,
    db: Session = Depends(get_db)
):
    """Get validation status for user's statements"""
    user, session_id = get_user_or_session(request)
    
    # Query statements
    query = db.query(Statement)
    
    if user:
        query = query.filter(Statement.user_id == user.id)
    else:
        query = query.filter(Statement.session_id == session_id)
    
    statements = query.order_by(Statement.created_at.desc()).limit(50).all()
    
    # Return validation status
    results = []
    for statement in statements:
        results.append({
            'id': statement.id,
            'filename': statement.original_filename,
            'created_at': statement.created_at,
            'validated': statement.validated,
            'validation_date': statement.validation_date,
            'expires_at': statement.expires_at
        })
    
    return results