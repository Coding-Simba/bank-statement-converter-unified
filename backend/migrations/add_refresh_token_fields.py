"""Add refresh token rotation fields to User model."""

from sqlalchemy import create_engine, Column, String, Integer
from sqlalchemy.sql import text
from pathlib import Path

# Database configuration
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATABASE_PATH = BASE_DIR / 'data' / 'bank_converter.db'
DATABASE_URL = f"sqlite:///{DATABASE_PATH}"

def upgrade():
    """Add refresh token family fields for token rotation."""
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as conn:
        # Check if columns already exist
        result = conn.execute(text("PRAGMA table_info(users)"))
        columns = [row[1] for row in result]
        
        # Add refresh_token_family if it doesn't exist
        if 'refresh_token_family' not in columns:
            conn.execute(text("""
                ALTER TABLE users 
                ADD COLUMN refresh_token_family VARCHAR(255)
            """))
            print("Added refresh_token_family column")
        
        # Add refresh_token_version if it doesn't exist
        if 'refresh_token_version' not in columns:
            conn.execute(text("""
                ALTER TABLE users 
                ADD COLUMN refresh_token_version INTEGER DEFAULT 1
            """))
            print("Added refresh_token_version column")
        
        conn.commit()
        print("Migration completed successfully")

def downgrade():
    """Remove refresh token family fields."""
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as conn:
        # SQLite doesn't support dropping columns easily
        # Would need to recreate the table without these columns
        print("Downgrade not implemented for SQLite")

if __name__ == "__main__":
    upgrade()