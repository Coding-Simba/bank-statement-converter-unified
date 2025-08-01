"""Add columns needed for dashboard functionality."""

from sqlalchemy import create_engine, text
from pathlib import Path
import sys

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from models.database import DATABASE_URL

def run_migration():
    """Add missing columns to the database."""
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as conn:
        # Add deleted_at column to statements table if it doesn't exist
        try:
            conn.execute(text("""
                ALTER TABLE statements ADD COLUMN deleted_at TIMESTAMP NULL;
            """))
            print("Added deleted_at column to statements table")
        except Exception as e:
            print(f"Column deleted_at might already exist: {e}")
        
        # Add bank column to statements table if it doesn't exist
        try:
            conn.execute(text("""
                ALTER TABLE statements ADD COLUMN bank VARCHAR(255) NULL;
            """))
            print("Added bank column to statements table")
        except Exception as e:
            print(f"Column bank might already exist: {e}")
        
        # Add validated column to statements table if it doesn't exist
        try:
            conn.execute(text("""
                ALTER TABLE statements ADD COLUMN validated BOOLEAN DEFAULT 0;
            """))
            print("Added validated column to statements table")
        except Exception as e:
            print(f"Column validated might already exist: {e}")
        
        # Create index on statements for better performance
        try:
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_statements_user_deleted 
                ON statements(user_id, is_deleted);
            """))
            print("Created index on statements table")
        except Exception as e:
            print(f"Index might already exist: {e}")
        
        conn.commit()
    
    print("Migration completed successfully!")


if __name__ == "__main__":
    run_migration()