"""Add sessions table for tracking active user sessions."""

from sqlalchemy import create_engine, text
from pathlib import Path

# Database configuration
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATABASE_PATH = BASE_DIR / 'data' / 'bank_converter.db'
DATABASE_URL = f"sqlite:///{DATABASE_PATH}"

def upgrade():
    """Create sessions table."""
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as conn:
        # Create sessions table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                session_id VARCHAR(255) UNIQUE NOT NULL,
                device_info TEXT,
                device_type VARCHAR(50),
                browser VARCHAR(50),
                os VARCHAR(50),
                ip_address VARCHAR(50),
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_accessed DATETIME DEFAULT CURRENT_TIMESTAMP,
                expires_at DATETIME NOT NULL,
                is_remember_me BOOLEAN DEFAULT 0,
                is_active BOOLEAN DEFAULT 1,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """))
        
        # Create indexes
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions(user_id)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_sessions_session_id ON sessions(session_id)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_sessions_active ON sessions(is_active)"))
        
        conn.commit()
        print("Sessions table created successfully")

def downgrade():
    """Drop sessions table."""
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as conn:
        conn.execute(text("DROP TABLE IF EXISTS sessions"))
        conn.commit()
        print("Sessions table dropped")

if __name__ == "__main__":
    upgrade()