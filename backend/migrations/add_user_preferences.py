"""Add user preferences columns to the users table."""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database connection
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost/bankcsv")
engine = create_engine(DATABASE_URL)


def add_columns():
    """Add user preference columns to the users table."""
    
    columns_to_add = [
        ("timezone", "VARCHAR(50)", "'UTC'"),
        ("notification_preferences", "TEXT", "NULL"),
        ("conversion_preferences", "TEXT", "NULL"),
        ("two_factor_enabled", "BOOLEAN", "FALSE"),
        ("two_factor_secret", "VARCHAR(255)", "NULL"),
        ("two_factor_backup_codes", "TEXT", "NULL"),
        ("api_key", "VARCHAR(255)", "NULL"),
        ("api_key_created_at", "TIMESTAMP", "NULL"),
        ("email_verified", "BOOLEAN", "TRUE"),
        ("pending_email", "VARCHAR(255)", "NULL"),
        ("pending_email_token", "VARCHAR(255)", "NULL"),
        ("pending_email_expires", "TIMESTAMP", "NULL"),
    ]
    
    with engine.connect() as conn:
        # Start transaction
        trans = conn.begin()
        
        try:
            # Check existing columns
            existing_columns = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'users'
            """)).fetchall()
            
            existing_column_names = [col[0] for col in existing_columns]
            
            # Add missing columns
            for column_name, column_type, default_value in columns_to_add:
                if column_name not in existing_column_names:
                    try:
                        alter_sql = f"""
                            ALTER TABLE users 
                            ADD COLUMN {column_name} {column_type} DEFAULT {default_value}
                        """
                        conn.execute(text(alter_sql))
                        print(f"✓ Added column: {column_name}")
                    except OperationalError as e:
                        if "already exists" not in str(e):
                            print(f"✗ Error adding column {column_name}: {e}")
                else:
                    print(f"- Column {column_name} already exists")
            
            # Create index for API key lookups
            try:
                conn.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_users_api_key 
                    ON users(api_key) 
                    WHERE api_key IS NOT NULL
                """))
                print("✓ Created index on api_key")
            except Exception as e:
                print(f"✗ Error creating api_key index: {e}")
            
            # Create index for email verification
            try:
                conn.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_users_pending_email_token 
                    ON users(pending_email_token) 
                    WHERE pending_email_token IS NOT NULL
                """))
                print("✓ Created index on pending_email_token")
            except Exception as e:
                print(f"✗ Error creating pending_email_token index: {e}")
            
            trans.commit()
            print("\n✓ Migration completed successfully!")
            
        except Exception as e:
            trans.rollback()
            print(f"\n✗ Migration failed: {e}")
            raise


def check_columns():
    """Check which columns exist in the users table."""
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_name = 'users'
            ORDER BY ordinal_position
        """))
        
        print("\nCurrent users table columns:")
        print("-" * 80)
        for row in result:
            print(f"{row[0]:30} {row[1]:20} {row[2]:10} {row[3] or 'NULL'}")


if __name__ == "__main__":
    print("User Preferences Migration")
    print("=" * 80)
    
    # Show current state
    check_columns()
    
    # Run migration
    print("\nRunning migration...")
    add_columns()
    
    # Show final state
    print("\nFinal table structure:")
    check_columns()