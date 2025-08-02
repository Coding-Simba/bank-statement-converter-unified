"""Statement management API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status, Request, UploadFile, File
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import os
import uuid
from pathlib import Path

from models.database import get_db, User, Statement, GenerationTracking, Subscription, UsageLog
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
    monthly_limit: Optional[int] = None
    monthly_used: Optional[int] = None


@router.get("/check-limit", response_model=GenerationLimitResponse)
async def check_generation_limit(
    request: Request,
    db: Session = Depends(get_db)
):
    """Check if user can generate based on their limit."""
    user, session_id = get_user_or_session(request)
    
    if user:
        # Authenticated user - check subscription-based limits
        from datetime import datetime
        
        # Get active subscription
        subscription = db.query(Subscription).filter(
            Subscription.user_id == user.id,
            Subscription.status == "active"
        ).first()
        
        # Determine plan
        plan_id = subscription.plan_id if subscription else "free"
        
        # Get plan limits
        plan_limits = {
            "free": {"monthly": 150, "daily": 5},
            "starter": {"monthly": 400, "daily": 999},
            "professional": {"monthly": 1000, "daily": 999},
            "business": {"monthly": 4000, "daily": 999}
        }
        
        limits = plan_limits.get(plan_id, plan_limits["free"])
        
        # Get current month usage
        start_of_month = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        monthly_usage = db.query(UsageLog).filter(
            UsageLog.user_id == user.id,
            UsageLog.created_at >= start_of_month
        ).count()
        
        # For free users, also check daily limit
        if plan_id == "free":
            user.reset_daily_limit_if_needed()
            db.commit()
            can_generate = user.daily_generations < limits["daily"] and monthly_usage < limits["monthly"]
            message = None
            if user.daily_generations >= limits["daily"]:
                message = f"Daily limit of {limits['daily']} conversions reached"
            elif monthly_usage >= limits["monthly"]:
                message = f"Monthly limit of {limits['monthly']} conversions reached"
        else:
            can_generate = monthly_usage < limits["monthly"]
            message = f"Monthly limit of {limits['monthly']} conversions reached" if not can_generate else None
        
        return GenerationLimitResponse(
            can_generate=can_generate,
            daily_limit=limits["daily"],
            daily_used=user.daily_generations if plan_id == "free" else 0,
            account_type=plan_id,
            message=message,
            monthly_limit=limits["monthly"],
            monthly_used=monthly_usage
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


@router.post("/convert")
async def convert_statement(
    request: Request,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Convert a bank statement PDF to CSV."""
    user, session_id = get_user_or_session(request)
    
    # Check generation limit
    if user:
        # Check subscription-based limits
        from datetime import datetime
        
        # Get active subscription
        subscription = db.query(Subscription).filter(
            Subscription.user_id == user.id,
            Subscription.status == "active"
        ).first()
        
        # Determine plan
        plan_id = subscription.plan_id if subscription else "free"
        
        # Get plan limits
        plan_limits = {
            "free": {"monthly": 150, "daily": 5},
            "starter": {"monthly": 400, "daily": 999},
            "professional": {"monthly": 1000, "daily": 999},
            "business": {"monthly": 4000, "daily": 999}
        }
        
        limits = plan_limits.get(plan_id, plan_limits["free"])
        
        # Get current month usage
        start_of_month = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        monthly_usage = db.query(UsageLog).filter(
            UsageLog.user_id == user.id,
            UsageLog.created_at >= start_of_month
        ).count()
        
        # For free users, also check daily limit
        if plan_id == "free":
            user.reset_daily_limit_if_needed()
            if user.daily_generations >= limits["daily"]:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"Daily limit of {limits['daily']} conversions reached"
                )
        
        if monthly_usage >= limits["monthly"]:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Monthly limit of {limits['monthly']} conversions reached. Please upgrade your plan."
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
    
    # Update generation count and log usage
    if user:
        # Log usage for subscription tracking
        usage_log = UsageLog(
            user_id=user.id,
            pages=1,
            statement_id=statement.id
        )
        db.add(usage_log)
        
        # Also update daily count for free users
        subscription = db.query(Subscription).filter(
            Subscription.user_id == user.id,
            Subscription.status == "active"
        ).first()
        
        if not subscription or subscription.plan_id == "free":
            user.daily_generations += 1
    else:
        tracking.increment_count()
    
    db.commit()
    db.refresh(statement)
    
    response = StatementResponse(
        id=statement.id,
        filename=statement.filename,
        original_filename=statement.original_filename,
        created_at=statement.created_at,
        expires_at=statement.expires_at,
        file_size=statement.file_size
    )
    
    # Add results_url to response
    response_dict = response.dict()
    response_dict["results_url"] = f"/results/{statement.id}"
    
    return response_dict


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


@router.get("/statement/{statement_id}/transactions")
async def get_statement_transactions(
    statement_id: int,
    request: Request,
    page: int = 1,
    per_page: int = 50,
    db: Session = Depends(get_db)
):
    """Get paginated transactions for a statement with metadata."""
    user, session_id = get_user_or_session(request)
    
    # Get statement
    statement = db.query(Statement).filter(Statement.id == statement_id).first()
    
    if not statement:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Statement not found"
        )
    
    # Check access permissions (same logic as download)
    if user and statement.user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    elif not user:
        from datetime import datetime, timedelta
        if statement.created_at < datetime.utcnow() - timedelta(minutes=5):
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
    
    # Get original PDF path
    pdf_path = statement.file_path.replace('.csv', '.pdf')
    if not os.path.exists(pdf_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Original PDF not found"
        )
    
    # Re-parse PDF to get transactions
    from universal_parser import parse_universal_pdf
    try:
        all_transactions = parse_universal_pdf(pdf_path)
        
        # Sort by date
        all_transactions = sorted(all_transactions, key=lambda x: x.get('date') or datetime.min)
        
        # Calculate statistics
        if all_transactions:
            dates = [t['date'] for t in all_transactions if t.get('date')]
            date_range = {
                "start": min(dates).strftime('%Y-%m-%d') if dates else None,
                "end": max(dates).strftime('%Y-%m-%d') if dates else None
            }
            
            # Try to detect bank from PDF text
            import PyPDF2
            bank_name = "Unknown Bank"
            try:
                with open(pdf_path, 'rb') as file:
                    reader = PyPDF2.PdfReader(file)
                    if reader.pages:
                        first_page_text = reader.pages[0].extract_text().lower()
                        # Simple bank detection
                        banks = {
                            'chase': 'Chase Bank',
                            'bank of america': 'Bank of America',
                            'wells fargo': 'Wells Fargo',
                            'citibank': 'Citibank',
                            'pnc': 'PNC Bank',
                            'huntington': 'Huntington Bank',
                            'fifth third': 'Fifth Third Bank',
                            'commonwealth': 'Commonwealth Bank',
                            'bendigo': 'Bendigo Bank',
                            'rabobank': 'Rabobank'
                        }
                        for key, value in banks.items():
                            if key in first_page_text:
                                bank_name = value
                                break
            except:
                pass
        else:
            date_range = {"start": None, "end": None}
            bank_name = "Unknown Bank"
        
        # Pagination
        total_count = len(all_transactions)
        total_pages = (total_count + per_page - 1) // per_page
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        
        # Get page of transactions
        page_transactions = all_transactions[start_idx:end_idx]
        
        # Format transactions for JSON response
        formatted_transactions = []
        for trans in page_transactions:
            formatted_transactions.append({
                "date": trans['date'].strftime('%Y-%m-%d') if trans.get('date') else "N/A",
                "description": trans.get('description', 'Unknown'),
                "amount": float(trans.get('amount', 0)),
                "balance": float(trans.get('balance', 0))
            })
        
        return {
            "transactions": formatted_transactions,
            "total_count": total_count,
            "statistics": {
                "bank_name": bank_name,
                "date_range": date_range,
                "total_transactions": total_count,
                "original_filename": statement.original_filename
            },
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total_pages": total_pages
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to parse transactions: {str(e)}"
        )


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


@router.get("/statement/{statement_id}/download/markdown")
async def download_statement_markdown(
    statement_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    """Download statement as markdown with statistics header."""
    user, session_id = get_user_or_session(request)
    
    # Get statement
    statement = db.query(Statement).filter(Statement.id == statement_id).first()
    
    if not statement:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Statement not found"
        )
    
    # Check access permissions (same as other endpoints)
    if user and statement.user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    elif not user:
        from datetime import datetime, timedelta
        if statement.created_at < datetime.utcnow() - timedelta(minutes=5):
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
    
    # Get original PDF path
    pdf_path = statement.file_path.replace('.csv', '.pdf')
    if not os.path.exists(pdf_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Original PDF not found"
        )
    
    # Re-parse PDF to get all transactions
    from universal_parser import parse_universal_pdf
    try:
        all_transactions = parse_universal_pdf(pdf_path)
        all_transactions = sorted(all_transactions, key=lambda x: x.get('date') or datetime.min)
        
        # Calculate statistics
        if all_transactions:
            dates = [t['date'] for t in all_transactions if t.get('date')]
            date_range = {
                "start": min(dates).strftime('%Y-%m-%d') if dates else "N/A",
                "end": max(dates).strftime('%Y-%m-%d') if dates else "N/A"
            }
            
            # Detect bank
            import PyPDF2
            bank_name = "Unknown Bank"
            try:
                with open(pdf_path, 'rb') as file:
                    reader = PyPDF2.PdfReader(file)
                    if reader.pages:
                        first_page_text = reader.pages[0].extract_text().lower()
                        banks = {
                            'chase': 'Chase Bank',
                            'bank of america': 'Bank of America',
                            'wells fargo': 'Wells Fargo',
                            'citibank': 'Citibank',
                            'pnc': 'PNC Bank',
                            'huntington': 'Huntington Bank',
                            'fifth third': 'Fifth Third Bank',
                            'commonwealth': 'Commonwealth Bank',
                            'bendigo': 'Bendigo Bank',
                            'rabobank': 'Rabobank'
                        }
                        for key, value in banks.items():
                            if key in first_page_text:
                                bank_name = value
                                break
            except:
                pass
        else:
            date_range = {"start": "N/A", "end": "N/A"}
            bank_name = "Unknown Bank"
        
        # Generate markdown content
        markdown_content = f"""# Bank Statement Export

## Statement Information
- **Bank:** {bank_name}
- **Original File:** {statement.original_filename}
- **Date Range:** {date_range['start']} to {date_range['end']}
- **Total Transactions:** {len(all_transactions)}
- **Exported:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Transactions

| Date | Description | Amount | Balance |
|------|-------------|--------|---------|
"""
        
        # Add transactions
        balance = 0.0
        for trans in all_transactions:
            date_str = trans['date'].strftime('%Y-%m-%d') if trans.get('date') else "N/A"
            desc = trans.get('description', 'Unknown').replace('|', '\\|')  # Escape pipes
            amount = trans.get('amount', 0.0)
            balance += amount
            
            markdown_content += f"| {date_str} | {desc} | ${amount:,.2f} | ${balance:,.2f} |\n"
        
        markdown_content += f"\n---\n*Generated by BankCSV Converter*"
        
        # Save to temporary file
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as tmp_file:
            tmp_file.write(markdown_content)
            tmp_path = tmp_file.name
        
        from fastapi.responses import FileResponse
        return FileResponse(
            path=tmp_path,
            filename=f"{statement.original_filename.replace('.pdf', '')}_bank_statement.md",
            media_type="text/markdown",
            headers={"Content-Disposition": f"attachment; filename={statement.original_filename.replace('.pdf', '')}_bank_statement.md"}
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate markdown: {str(e)}"
        )