"""Add Stripe fields to database."""

from sqlalchemy import create_engine, text
from pathlib import Path

# Database configuration
BASE_DIR = Path(__file__).resolve().parent.parent
DATABASE_PATH = BASE_DIR / 'data' / 'bank_converter.db'
DATABASE_URL = f"sqlite:///{DATABASE_PATH}"

def migrate():
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as conn:
        # Check if column already exists
        result = conn.execute(text("PRAGMA table_info(users)"))
        columns = [row[1] for row in result]
        
        if 'stripe_customer_id' not in columns:
            print("Adding stripe_customer_id column...")
            conn.execute(text("ALTER TABLE users ADD COLUMN stripe_customer_id VARCHAR(255)"))
            conn.commit()
            print("✓ stripe_customer_id column added")
        else:
            print("✓ stripe_customer_id column already exists")
            
    print("Migration complete!")

if __name__ == "__main__":
    migrate()