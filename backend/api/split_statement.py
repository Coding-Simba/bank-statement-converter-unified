"""Split statement by date range API endpoint."""

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, status
from fastapi.responses import StreamingResponse
from typing import Optional
from datetime import datetime, timedelta
import io
import pandas as pd
from pathlib import Path
import os
import uuid

# Import the universal parser
from universal_parser import parse_universal_pdf

router = APIRouter(prefix="/api", tags=["split-statement"])


def get_date_range_from_preset(preset: str):
    """Get date range based on preset selection"""
    today = datetime.now()
    
    if preset == 'last_month':
        # First day of last month
        if today.month == 1:
            start_date = datetime(today.year - 1, 12, 1)
        else:
            start_date = datetime(today.year, today.month - 1, 1)
        
        # Last day of last month
        if today.month == 1:
            end_date = datetime(today.year, 1, 1) - timedelta(days=1)
        else:
            end_date = datetime(today.year, today.month, 1) - timedelta(days=1)
    
    elif preset == 'last_quarter':
        current_quarter = (today.month - 1) // 3
        if current_quarter == 0:
            start_date = datetime(today.year - 1, 10, 1)
            end_date = datetime(today.year - 1, 12, 31)
        else:
            start_date = datetime(today.year, (current_quarter - 1) * 3 + 1, 1)
            if current_quarter == 1:
                end_date = datetime(today.year, 3, 31)
            elif current_quarter == 2:
                end_date = datetime(today.year, 6, 30)
            else:
                end_date = datetime(today.year, 9, 30)
    
    elif preset == 'last_3_months':
        end_date = today
        start_date = today - timedelta(days=90)
    
    elif preset == 'last_6_months':
        end_date = today
        start_date = today - timedelta(days=180)
    
    elif preset == 'year_to_date':
        start_date = datetime(today.year, 1, 1)
        end_date = today
    
    elif preset == 'last_year':
        start_date = datetime(today.year - 1, 1, 1)
        end_date = datetime(today.year - 1, 12, 31)
    
    else:
        # Default to last month
        return get_date_range_from_preset('last_month')
    
    return start_date, end_date


def filter_transactions_by_date(transactions, start_date, end_date):
    """Filter transactions within date range"""
    filtered = []
    
    for trans in transactions:
        if 'date' in trans and trans['date']:
            if start_date <= trans['date'] <= end_date:
                filtered.append(trans)
    
    return filtered


def create_csv_from_transactions(transactions):
    """Create CSV content from transactions"""
    if not transactions:
        return "Date,Description,Amount,Balance\n"
    
    # Convert to DataFrame
    df = pd.DataFrame(transactions)
    
    # Prepare output columns
    output_data = []
    balance = 0.0
    
    for _, trans in df.iterrows():
        # Format date
        date_str = trans['date'].strftime('%Y-%m-%d') if 'date' in trans and trans['date'] else "Unknown"
        
        # Get description
        description = str(trans.get('description', 'Transaction')).replace('"', '""')  # Escape quotes
        
        # Get amount
        amount = trans.get('amount', 0.0)
        balance += amount
        
        output_data.append({
            'Date': date_str,
            'Description': description,
            'Amount': f"{amount:.2f}",
            'Balance': f"{balance:.2f}"
        })
    
    # Create DataFrame and convert to CSV
    output_df = pd.DataFrame(output_data)
    return output_df.to_csv(index=False)


@router.post("/split-statement")
async def split_statement(
    file: UploadFile = File(...),
    preset: Optional[str] = Form(None),
    start_date: Optional[str] = Form(None),
    end_date: Optional[str] = Form(None)
):
    """Split PDF statement by date range and return filtered CSV"""
    
    # Validate file
    if not file.filename.endswith('.pdf'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are supported"
        )
    
    # Save uploaded file temporarily
    upload_dir = Path(__file__).parent.parent.parent / "uploads"
    upload_dir.mkdir(exist_ok=True)
    
    file_id = str(uuid.uuid4())
    file_path = upload_dir / f"{file_id}.pdf"
    
    try:
        # Save file
        contents = await file.read()
        with open(file_path, 'wb') as f:
            f.write(contents)
        
        # Extract transactions using universal parser
        all_transactions = parse_universal_pdf(str(file_path))
        
        if not all_transactions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No transactions found in the PDF"
            )
        
        # Determine date range
        if preset:
            filter_start, filter_end = get_date_range_from_preset(preset)
        else:
            # Parse custom date range
            try:
                filter_start = datetime.strptime(start_date, '%Y-%m-%d') if start_date else None
                filter_end = datetime.strptime(end_date, '%Y-%m-%d') if end_date else None
                
                if not filter_start or not filter_end:
                    raise ValueError("Both start and end dates are required")
                    
            except ValueError as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid date format. Use YYYY-MM-DD. Error: {str(e)}"
                )
        
        # Filter transactions by date range
        filtered_transactions = filter_transactions_by_date(all_transactions, filter_start, filter_end)
        
        if not filtered_transactions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No transactions found in the specified date range"
            )
        
        # Create CSV
        csv_content = create_csv_from_transactions(filtered_transactions)
        
        # Return CSV as streaming response
        csv_bytes = csv_content.encode('utf-8')
        csv_io = io.BytesIO(csv_bytes)
        
        filename = f"transactions_{filter_start.strftime('%Y%m%d')}_{filter_end.strftime('%Y%m%d')}.csv"
        
        return StreamingResponse(
            csv_io,
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "Content-Length": str(len(csv_bytes))
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing PDF: {str(e)}"
        )
    finally:
        # Clean up temporary file
        if file_path.exists():
            os.remove(file_path)


@router.post("/test-extraction")
async def test_extraction(file: UploadFile = File(...)):
    """Test endpoint to check PDF extraction without filtering"""
    
    if not file.filename.endswith('.pdf'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are supported"
        )
    
    # Save uploaded file temporarily
    upload_dir = Path(__file__).parent.parent.parent / "uploads"
    upload_dir.mkdir(exist_ok=True)
    
    file_id = str(uuid.uuid4())
    file_path = upload_dir / f"{file_id}.pdf"
    
    try:
        # Save file
        contents = await file.read()
        with open(file_path, 'wb') as f:
            f.write(contents)
        
        # Extract all transactions
        transactions = parse_universal_pdf(str(file_path))
        
        # Prepare response
        if transactions:
            dates = [t['date'] for t in transactions if 'date' in t and t['date']]
            
            response = {
                'total_transactions': len(transactions),
                'sample': transactions[:5],
                'date_range': {
                    'earliest': min(dates).strftime('%Y-%m-%d') if dates else None,
                    'latest': max(dates).strftime('%Y-%m-%d') if dates else None
                }
            }
        else:
            response = {
                'total_transactions': 0,
                'sample': [],
                'date_range': None
            }
        
        return response
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing PDF: {str(e)}"
        )
    finally:
        # Clean up temporary file
        if file_path.exists():
            os.remove(file_path)