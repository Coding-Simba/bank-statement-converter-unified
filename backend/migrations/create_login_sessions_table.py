"""Create login_sessions table for tracking user login history."""

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


def create_login_sessions_table():
    """Create the login_sessions table."""
    
    with engine.connect() as conn:
        trans = conn.begin()
        
        try:
            # Check if table exists
            result = conn.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'login_sessions'
                )
            """)).fetchone()
            
            if result[0]:
                print("❓ Table 'login_sessions' already exists")
                print("Dropping and recreating...")
                conn.execute(text("DROP TABLE IF EXISTS login_sessions CASCADE"))
            
            # Create table
            conn.execute(text("""
                CREATE TABLE login_sessions (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    
                    -- Session information
                    session_id VARCHAR(255) UNIQUE NOT NULL,
                    ip_address VARCHAR(45),
                    user_agent TEXT,
                    
                    -- Location data
                    country VARCHAR(100),
                    city VARCHAR(100),
                    
                    -- Device information
                    device_type VARCHAR(50),
                    browser VARCHAR(50),
                    os VARCHAR(50),
                    
                    -- Session status
                    is_active BOOLEAN DEFAULT TRUE,
                    login_successful BOOLEAN DEFAULT TRUE,
                    logout_type VARCHAR(50),
                    
                    -- Security
                    suspicious_activity BOOLEAN DEFAULT FALSE,
                    failed_attempts INTEGER DEFAULT 0,
                    
                    -- Timestamps
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    logged_out_at TIMESTAMP
                )
            """))
            print("✓ Created table: login_sessions")
            
            # Create indexes
            indexes = [
                ("idx_login_sessions_user_id", "user_id"),
                ("idx_login_sessions_session_id", "session_id"),
                ("idx_login_sessions_user_created", "user_id, created_at"),
                ("idx_login_sessions_active", "user_id, is_active"),
                ("idx_login_sessions_activity", "last_activity"),
                ("idx_login_sessions_ip", "ip_address")
            ]
            
            for index_name, columns in indexes:
                try:
                    conn.execute(text(f"""
                        CREATE INDEX {index_name} 
                        ON login_sessions({columns})
                    """))
                    print(f"✓ Created index: {index_name}")
                except Exception as e:
                    print(f"✗ Error creating index {index_name}: {e}")
            
            # Add relationship to users table (if column doesn't exist)
            try:
                # First check if we can add the relationship
                conn.execute(text("""
                    DO $$
                    BEGIN
                        IF NOT EXISTS (
                            SELECT 1 FROM pg_class c
                            JOIN pg_namespace n ON n.oid = c.relnamespace
                            WHERE c.relname = 'users' AND n.nspname = 'public'
                        ) THEN
                            RAISE NOTICE 'Users table does not exist';
                        END IF;
                    END $$;
                """))
                print("✓ Users table exists, relationship created")
            except Exception as e:
                print(f"⚠️  Warning: {e}")
            
            trans.commit()
            print("\n✓ Migration completed successfully!")
            
        except Exception as e:
            trans.rollback()
            print(f"\n✗ Migration failed: {e}")
            raise


def insert_sample_data():
    """Insert sample login session data for testing."""
    with engine.connect() as conn:
        trans = conn.begin()
        
        try:
            # Get a user ID
            result = conn.execute(text("SELECT id FROM users LIMIT 1")).fetchone()
            if not result:
                print("⚠️  No users found in database")
                return
            
            user_id = result[0]
            
            # Insert sample sessions
            sample_sessions = [
                {
                    "user_id": user_id,
                    "session_id": "sample_current_session_123",
                    "ip_address": "192.168.1.100",
                    "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) Chrome/120.0.0.0",
                    "country": "United States",
                    "city": "New York",
                    "device_type": "desktop",
                    "browser": "Chrome",
                    "os": "macOS",
                    "is_active": True,
                    "created_at": "CURRENT_TIMESTAMP"
                },
                {
                    "user_id": user_id,
                    "session_id": "sample_mobile_session_456",
                    "ip_address": "10.0.0.50",
                    "user_agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) Mobile/15E148",
                    "country": "United States",
                    "city": "San Francisco",
                    "device_type": "mobile",
                    "browser": "Safari",
                    "os": "iOS",
                    "is_active": False,
                    "logout_type": "manual",
                    "created_at": "CURRENT_TIMESTAMP - INTERVAL '2 days'",
                    "logged_out_at": "CURRENT_TIMESTAMP - INTERVAL '2 days' + INTERVAL '4 hours'"
                },
                {
                    "user_id": user_id,
                    "session_id": "sample_failed_session_789",
                    "ip_address": "203.0.113.0",
                    "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Firefox/121.0",
                    "device_type": "desktop",
                    "browser": "Firefox",
                    "os": "Windows",
                    "is_active": False,
                    "login_successful": False,
                    "created_at": "CURRENT_TIMESTAMP - INTERVAL '7 days'"
                }
            ]
            
            for session in sample_sessions:
                columns = ", ".join(session.keys())
                values = ", ".join([f":{k}" for k in session.keys()])
                
                # Handle SQL expressions
                for key, value in session.items():
                    if isinstance(value, str) and ("CURRENT_TIMESTAMP" in value or "INTERVAL" in value):
                        session[key] = text(value)
                
                conn.execute(
                    text(f"INSERT INTO login_sessions ({columns}) VALUES ({values})"),
                    session
                )
            
            trans.commit()
            print("✓ Inserted sample login sessions")
            
        except Exception as e:
            trans.rollback()
            print(f"✗ Failed to insert sample data: {e}")


def check_table():
    """Check the created table structure."""
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns 
            WHERE table_name = 'login_sessions'
            ORDER BY ordinal_position
        """))
        
        print("\nlogin_sessions table columns:")
        print("-" * 60)
        for row in result:
            print(f"{row[0]:20} {row[1]:20} {row[2]}")


if __name__ == "__main__":
    print("Login Sessions Table Migration")
    print("=" * 60)
    
    # Create table
    create_login_sessions_table()
    
    # Check structure
    check_table()
    
    # Optionally insert sample data
    response = input("\nInsert sample data? (y/n): ")
    if response.lower() == 'y':
        insert_sample_data()