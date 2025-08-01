#!/usr/bin/env python3
"""Add fields for user settings functionality."""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from models.database import DATABASE_URL
import json

def upgrade():
    """Add new fields for settings functionality."""
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as conn:
        # Add timezone field
        try:
            conn.execute(text("ALTER TABLE users ADD COLUMN timezone VARCHAR(50) DEFAULT 'UTC'"))
            print("✓ Added timezone column")
        except Exception as e:
            print(f"  Column timezone might already exist: {e}")
        
        # Add 2FA fields
        try:
            conn.execute(text("ALTER TABLE users ADD COLUMN two_factor_secret VARCHAR(255)"))
            print("✓ Added two_factor_secret column")
        except Exception as e:
            print(f"  Column two_factor_secret might already exist: {e}")
            
        try:
            conn.execute(text("ALTER TABLE users ADD COLUMN two_factor_enabled BOOLEAN DEFAULT 0"))
            print("✓ Added two_factor_enabled column")
        except Exception as e:
            print(f"  Column two_factor_enabled might already exist: {e}")
        
        # Add API key fields
        try:
            conn.execute(text("ALTER TABLE users ADD COLUMN api_key VARCHAR(255) UNIQUE"))
            print("✓ Added api_key column")
        except Exception as e:
            print(f"  Column api_key might already exist: {e}")
            
        try:
            conn.execute(text("ALTER TABLE users ADD COLUMN api_key_created_at TIMESTAMP"))
            print("✓ Added api_key_created_at column")
        except Exception as e:
            print(f"  Column api_key_created_at might already exist: {e}")
        
        # Add notification preferences (SQLite doesn't have native JSON, use TEXT)
        try:
            default_prefs = json.dumps({
                "security_alerts": True,
                "product_updates": True,
                "usage_reports": False,
                "marketing_emails": False
            })
            conn.execute(text(f"ALTER TABLE users ADD COLUMN notification_preferences TEXT DEFAULT '{default_prefs}'"))
            print("✓ Added notification_preferences column")
        except Exception as e:
            print(f"  Column notification_preferences might already exist: {e}")
        
        # Add pending email fields for email change verification
        try:
            conn.execute(text("ALTER TABLE users ADD COLUMN pending_email VARCHAR(255)"))
            print("✓ Added pending_email column")
        except Exception as e:
            print(f"  Column pending_email might already exist: {e}")
            
        try:
            conn.execute(text("ALTER TABLE users ADD COLUMN pending_email_token VARCHAR(255)"))
            print("✓ Added pending_email_token column")
        except Exception as e:
            print(f"  Column pending_email_token might already exist: {e}")
            
        try:
            conn.execute(text("ALTER TABLE users ADD COLUMN pending_email_expires TIMESTAMP"))
            print("✓ Added pending_email_expires column")
        except Exception as e:
            print(f"  Column pending_email_expires might already exist: {e}")
        
        # Add 2FA backup codes field
        try:
            conn.execute(text("ALTER TABLE users ADD COLUMN two_factor_backup_codes TEXT"))
            print("✓ Added two_factor_backup_codes column")
        except Exception as e:
            print(f"  Column two_factor_backup_codes might already exist: {e}")
        
        conn.commit()
        print("\n✅ Migration completed successfully!")

def downgrade():
    """Remove settings fields."""
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as conn:
        columns_to_drop = [
            'timezone', 'two_factor_secret', 'two_factor_enabled',
            'api_key', 'api_key_created_at', 'notification_preferences',
            'pending_email', 'pending_email_token', 'pending_email_expires',
            'two_factor_backup_codes'
        ]
        
        for column in columns_to_drop:
            try:
                # SQLite doesn't support DROP COLUMN directly
                print(f"Note: SQLite doesn't support dropping columns. Column {column} will remain but be unused.")
            except Exception as e:
                print(f"Error with column {column}: {e}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Run settings fields migration')
    parser.add_argument('--downgrade', action='store_true', help='Run downgrade instead of upgrade')
    args = parser.parse_args()
    
    if args.downgrade:
        print("Running downgrade...")
        downgrade()
    else:
        print("Running upgrade...")
        upgrade()