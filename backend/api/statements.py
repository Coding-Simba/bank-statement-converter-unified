"""Statement management API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status, Request, UploadFile, File
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import os
import uuid
from pathlib import Path

from models.database import get_db, User, Statement, GenerationTracking
from middleware.auth_middleware import get_user_or_session, get_current_user
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from utils.auth import generate_session_id

router = APIRouter(prefix="/api", tags=["statements"])

# Configuration
UPLOAD_DIR = Path(__file__).parent.parent.parent / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)


class StatementResponse(BaseModel):
    id: int
    filename: str
    original_filename: str
    created_at: datetime
    expires_at: datetime
    file_size: Optional[int]
    
    class Config:
        from_attributes = True


class GenerationLimitResponse(BaseModel):
    can_generate: bool
    daily_limit: int
    daily_used: int
    account_type: str
    message: Optional[str]


@router.get("/check-limit", response_model=GenerationLimitResponse)
async def check_generation_limit(
    request: Request,
    db: Session = Depends(get_db)
):
    """Check if user can generate based on their limit."""
    user, session_id = get_user_or_session(request)
    
    if user:
        # Authenticated user
        user.reset_daily_limit_if_needed()
        db.commit()
        
        can_generate = user.can_generate()
        daily_limit = user.get_daily_limit()
        
        return GenerationLimitResponse(
            can_generate=can_generate,
            daily_limit=daily_limit if daily_limit != float('inf') else 999,
            daily_used=user.daily_generations,
            account_type=user.account_type,
            message=None if can_generate else f"Daily limit of {daily_limit} conversions reached"
        )
    else:
        # Anonymous user - track by session/IP
        ip_address = request.client.host
        tracking = GenerationTracking.get_or_create(
            db, 
            ip_address=ip_address,
            session_id=session_id
        )
        
        can_generate = tracking.can_generate_anonymous()
        
        return GenerationLimitResponse(
            can_generate=can_generate,
            daily_limit=3,
            daily_used=tracking.generation_count,
            account_type="no_account",
            message=None if can_generate else "Daily limit of 3 conversions reached. Sign up for more!"
        )


@router.post("/convert", response_model=StatementResponse)
async def convert_statement(
    request: Request,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Convert a bank statement PDF to CSV."""
    user, session_id = get_user_or_session(request)
    
    # Check generation limit
    if user:
        user.reset_daily_limit_if_needed()
        if not user.can_generate():
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Daily limit of {user.get_daily_limit()} conversions reached"
            )
    else:
        # Anonymous user
        ip_address = request.client.host
        tracking = GenerationTracking.get_or_create(
            db,
            ip_address=ip_address,
            session_id=session_id
        )
        
        if not tracking.can_generate_anonymous():
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Daily limit of 3 conversions reached. Sign up for more!"
            )
    
    # Validate file
    if not file.filename.endswith('.pdf'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are supported"
        )
    
    # Generate unique filename
    file_id = str(uuid.uuid4())
    safe_filename = f"{file_id}.pdf"
    file_path = UPLOAD_DIR / safe_filename
    
    # Save uploaded file
    try:
        contents = await file.read()
        with open(file_path, 'wb') as f:
            f.write(contents)
        
        file_size = len(contents)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save file: {str(e)}"
        )
    
    # Convert PDF to CSV
    csv_filename = f"{file_id}.csv"
    csv_path = UPLOAD_DIR / csv_filename
    
    # Import the universal parser
    from universal_parser import parse_universal_pdf
    
    try:
        # Parse the PDF using universal parser
        # Note: The universal parser now automatically saves failed PDFs
        # if parsing was incomplete or unsuccessful
        transactions = parse_universal_pdf(str(file_path))
        
        if transactions:
            # Convert to CSV
            with open(csv_path, 'w', encoding='utf-8') as f:
                f.write("Date,Description,Amount,Balance\n")
                
                # Calculate running balance (assuming we start from 0)
                balance = 0.0
                # Sort by date if available, otherwise maintain original order
                sorted_trans = sorted(transactions, key=lambda x: x.get('date') or datetime.min)
                
                for trans in sorted_trans:
                    # Handle missing dates
                    if trans.get('date'):
                        date_str = trans['date'].strftime('%Y-%m-%d')
                    else:
                        date_str = "2024-01-01"  # Default date for transactions without dates
                    
                    description = trans.get('description', 'Unknown').replace('"', '""')  # Escape quotes
                    amount = trans.get('amount', 0.0)
                    balance += amount
                    
                    f.write(f'"{date_str}","{description}",{amount:.2f},{balance:.2f}\n')
        else:
            # If no transactions found, create a sample CSV
            # This PDF has already been saved by the universal parser for improvement
            with open(csv_path, 'w') as f:
                f.write("Date,Description,Amount,Balance\n")
                f.write(f"2024-01-01,No transactions found in PDF: {file.filename},0.00,0.00\n")
                
    except Exception as e:
        # If parsing fails, create error CSV
        with open(csv_path, 'w') as f:
            f.write("Date,Description,Amount,Balance\n")
            f.write(f"2024-01-01,Error parsing PDF: {str(e)},0.00,0.00\n")
    
    # Create statement record
    statement = Statement(
        user_id=user.id if user else None,
        session_id=session_id if not user else None,
        filename=csv_filename,
        file_path=str(csv_path),
        original_filename=file.filename,
        file_size=file_size
    )
    
    db.add(statement)
    
    # Update generation count
    if user:
        user.daily_generations += 1
    else:
        tracking.increment_count()
    
    db.commit()
    db.refresh(statement)
    
    return StatementResponse(
        id=statement.id,
        filename=statement.filename,
        original_filename=statement.original_filename,
        created_at=statement.created_at,
        expires_at=statement.expires_at,
        file_size=statement.file_size
    )


@router.get("/user/statements", response_model=List[StatementResponse])
async def get_user_statements(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all statements for the authenticated user."""
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    statements = db.query(Statement).filter(
        Statement.user_id == current_user.id,
        Statement.is_deleted == False
    ).order_by(Statement.created_at.desc()).all()
    
    return [
        StatementResponse(
            id=stmt.id,
            filename=stmt.filename,
            original_filename=stmt.original_filename,
            created_at=stmt.created_at,
            expires_at=stmt.expires_at,
            file_size=stmt.file_size
        )
        for stmt in statements
    ]


@router.get("/statement/{statement_id}/download")
async def download_statement(
    statement_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    """Download a converted statement."""
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
    # For anonymous users, allow download if statement was created recently (within 5 minutes)
    elif not user:
        from datetime import datetime, timedelta
        if statement.created_at < datetime.utcnow() - timedelta(minutes=5):
            # Only check session for older statements
            if statement.session_id != session_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied"
                )
    
    # Check if expired
    if statement.is_expired():
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="Statement has expired and is no longer available"
        )
    
    # Check if file exists
    if not os.path.exists(statement.file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )
    
    from fastapi.responses import FileResponse
    return FileResponse(
        path=statement.file_path,
        filename=f"converted_{statement.original_filename.replace('.pdf', '.csv')}",
        media_type="text/csv"
    )