"""Cleanup utilities for expired statements."""

import os
from datetime import datetime
from pathlib import Path
from sqlalchemy.orm import Session

from models.database import SessionLocal, Statement


def cleanup_expired_statements():
    """Clean up expired statement files and database records."""
    db = SessionLocal()
    
    try:
        # Find expired statements
        expired_statements = db.query(Statement).filter(
            Statement.expires_at < datetime.utcnow(),
            Statement.is_deleted == False
        ).all()
        
        cleanup_count = 0
        
        for statement in expired_statements:
            try:
                # Delete file if it exists
                if os.path.exists(statement.file_path):
                    os.remove(statement.file_path)
                    print(f"Deleted file: {statement.file_path}")
                
                # Also delete the original PDF if it exists
                pdf_path = statement.file_path.replace('.csv', '.pdf')
                if os.path.exists(pdf_path):
                    os.remove(pdf_path)
                
                # Mark as deleted in database
                statement.mark_deleted()
                cleanup_count += 1
                
            except Exception as e:
                print(f"Error cleaning up statement {statement.id}: {e}")
        
        db.commit()
        
        if cleanup_count > 0:
            print(f"Cleaned up {cleanup_count} expired statements")
            
    except Exception as e:
        print(f"Error in cleanup task: {e}")
        db.rollback()
    finally:
        db.close()


def get_storage_stats():
    """Get storage statistics for uploaded files."""
    upload_dir = Path(__file__).parent.parent.parent / "uploads"
    
    if not upload_dir.exists():
        return {
            "total_files": 0,
            "total_size_mb": 0,
            "pdf_count": 0,
            "csv_count": 0
        }
    
    total_size = 0
    pdf_count = 0
    csv_count = 0
    
    for file in upload_dir.iterdir():
        if file.is_file():
            total_size += file.stat().st_size
            if file.suffix == '.pdf':
                pdf_count += 1
            elif file.suffix == '.csv':
                csv_count += 1
    
    return {
        "total_files": pdf_count + csv_count,
        "total_size_mb": round(total_size / (1024 * 1024), 2),
        "pdf_count": pdf_count,
        "csv_count": csv_count
    }