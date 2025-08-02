"""Create login_sessions table for SQLite."""

import sqlite3
import os
import sys

# Get the database path
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "..", "data", "bank_converter.db")

def create_table():
    """Create login_sessions table."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Create login_sessions table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS login_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            session_id VARCHAR UNIQUE NOT NULL,
            ip_address VARCHAR,
            user_agent TEXT,
            device_type VARCHAR,
            browser VARCHAR,
            os VARCHAR,
            location VARCHAR,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP,
            is_active BOOLEAN DEFAULT 1,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
        )
    """)
    
    # Create indexes
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_login_sessions_user_id ON login_sessions(user_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_login_sessions_session_id ON login_sessions(session_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_login_sessions_is_active ON login_sessions(is_active)")
    
    conn.commit()
    conn.close()
    print("✅ Login sessions table created successfully!")

if __name__ == "__main__":
    print("SQLite Login Sessions Migration")
    print("=" * 80)
    print(f"Database: {DB_PATH}")
    
    if not os.path.exists(DB_PATH):
        print(f"❌ Database not found at {DB_PATH}")
        sys.exit(1)
    
    create_table()