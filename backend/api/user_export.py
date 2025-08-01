"""User data export API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from datetime import datetime
import csv
import json
import io
from typing import Optional

from models.database import get_db, User, Statement, GenerationTracking, Payment
from dependencies import get_current_user

router = APIRouter()

@router.post("/user/export-data")
async def export_user_data(
    format: str = "json",  # json or csv
    include_statements: bool = True,
    include_usage: bool = True,
    include_payments: bool = True,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Export user data in JSON or CSV format."""
    
    if format not in ["json", "csv"]:
        raise HTTPException(status_code=400, detail="Format must be 'json' or 'csv'")
    
    # Prepare data to export
    export_data = {
        "user_info": {
            "email": current_user.email,
            "full_name": current_user.full_name,
            "company_name": current_user.company_name,
            "account_type": current_user.account_type,
            "subscription_plan": current_user.subscription_plan,
            "created_at": current_user.created_at.isoformat() if current_user.created_at else None,
        }
    }
    
    # Get statements if requested
    if include_statements:
        statements = db.query(Statement).filter(
            Statement.user_id == current_user.id,
            or_(Statement.is_deleted == False, Statement.is_deleted == None)
        ).order_by(Statement.created_at.desc()).all()
        
        export_data["statements"] = [
            {
                "id": stmt.id,
                "original_filename": stmt.original_filename,
                "bank": stmt.bank,
                "file_size": stmt.file_size,
                "created_at": stmt.created_at.isoformat() if stmt.created_at else None,
                "validated": stmt.validated
            }
            for stmt in statements
        ]
    
    # Get usage history if requested
    if include_usage:
        usage_history = db.query(GenerationTracking).filter(
            GenerationTracking.user_id == current_user.id
        ).order_by(GenerationTracking.date.desc()).all()
        
        export_data["usage_history"] = [
            {
                "date": usage.date.isoformat() if usage.date else None,
                "count": usage.count
            }
            for usage in usage_history
        ]
    
    # Get payment history if requested
    if include_payments:
        payments = db.query(Payment).filter(
            Payment.user_id == current_user.id
        ).order_by(Payment.created_at.desc()).all()
        
        export_data["payments"] = [
            {
                "amount": payment.amount,
                "currency": payment.currency,
                "status": payment.status,
                "created_at": payment.created_at.isoformat() if payment.created_at else None,
                "description": payment.description
            }
            for payment in payments
        ]
    
    # Format response based on requested format
    if format == "json":
        content = json.dumps(export_data, indent=2)
        media_type = "application/json"
        filename = f"bankcsv_export_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
    else:  # csv
        # For CSV, we'll create separate sections
        output = io.StringIO()
        writer = csv.writer(output)
        
        # User info section
        writer.writerow(["USER INFORMATION"])
        writer.writerow(["Field", "Value"])
        for key, value in export_data["user_info"].items():
            writer.writerow([key, value])
        writer.writerow([])
        
        # Statements section
        if include_statements and "statements" in export_data:
            writer.writerow(["CONVERSION HISTORY"])
            if export_data["statements"]:
                writer.writerow(["ID", "Filename", "Bank", "Size", "Created At", "Validated"])
                for stmt in export_data["statements"]:
                    writer.writerow([
                        stmt["id"],
                        stmt["original_filename"],
                        stmt["bank"] or "",
                        stmt["file_size"] or "",
                        stmt["created_at"],
                        "Yes" if stmt["validated"] else "No"
                    ])
            else:
                writer.writerow(["No conversions found"])
            writer.writerow([])
        
        # Usage history section
        if include_usage and "usage_history" in export_data:
            writer.writerow(["USAGE HISTORY"])
            if export_data["usage_history"]:
                writer.writerow(["Date", "Conversions"])
                for usage in export_data["usage_history"]:
                    writer.writerow([usage["date"], usage["count"]])
            else:
                writer.writerow(["No usage history found"])
            writer.writerow([])
        
        # Payment history section
        if include_payments and "payments" in export_data:
            writer.writerow(["PAYMENT HISTORY"])
            if export_data["payments"]:
                writer.writerow(["Amount", "Currency", "Status", "Date", "Description"])
                for payment in export_data["payments"]:
                    writer.writerow([
                        payment["amount"],
                        payment["currency"],
                        payment["status"],
                        payment["created_at"],
                        payment["description"] or ""
                    ])
            else:
                writer.writerow(["No payment history found"])
        
        content = output.getvalue()
        media_type = "text/csv"
        filename = f"bankcsv_export_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"
    
    return Response(
        content=content,
        media_type=media_type,
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"'
        }
    )

@router.get("/user/export-summary")
async def get_export_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a summary of what data is available for export."""
    
    # Count statements
    statement_count = db.query(Statement).filter(
        Statement.user_id == current_user.id,
        or_(Statement.is_deleted == False, Statement.is_deleted == None)
    ).count()
    
    # Count usage days
    usage_days = db.query(GenerationTracking).filter(
        GenerationTracking.user_id == current_user.id
    ).count()
    
    # Count payments
    payment_count = db.query(Payment).filter(
        Payment.user_id == current_user.id
    ).count()
    
    return {
        "available_data": {
            "statements": statement_count,
            "usage_days": usage_days,
            "payments": payment_count
        },
        "export_formats": ["json", "csv"],
        "last_activity": current_user.updated_at.isoformat() if current_user.updated_at else None
    }