"""Add missing columns to users table."""

from sqlalchemy import create_engine, text
from pathlib import Path
import sys

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from models.database import DATABASE_URL

def run_migration():
    """Add missing columns to the users table."""
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as conn:
        # Add missing columns one by one
        columns_to_add = [
            ("refresh_token_family", "VARCHAR(255) NULL"),
            ("refresh_token_version", "INTEGER DEFAULT 1"),
            ("timezone", "VARCHAR(50) DEFAULT 'UTC'"),
            ("two_factor_secret", "VARCHAR(255) NULL"),
            ("two_factor_enabled", "BOOLEAN DEFAULT 0"),
            ("two_factor_backup_codes", "TEXT NULL"),
            ("api_key", "VARCHAR(255) NULL"),
            ("api_key_created_at", "TIMESTAMP NULL"),
            ("notification_preferences", "TEXT NULL"),
            ("pending_email", "VARCHAR(255) NULL"),
            ("pending_email_token", "VARCHAR(255) NULL"),
            ("pending_email_expires", "TIMESTAMP NULL"),
            ("company", "VARCHAR(255) NULL"),  # Add missing company field
            ("plan", "VARCHAR(50) NULL"),  # Add missing plan field
            ("is_verified", "BOOLEAN DEFAULT 0")  # Add missing is_verified field
        ]
        
        for column_name, column_def in columns_to_add:
            try:
                conn.execute(text(f"ALTER TABLE users ADD COLUMN {column_name} {column_def};"))
                print(f"Added column: {column_name}")
            except Exception as e:
                if "duplicate column name" in str(e).lower() or "already exists" in str(e).lower():
                    print(f"Column {column_name} already exists")
                else:
                    print(f"Error adding {column_name}: {e}")
        
        conn.commit()
    
    print("Migration completed!")


if __name__ == "__main__":
    run_migration()