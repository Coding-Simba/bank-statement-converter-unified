"""Add user preferences columns to users table for SQLite."""

import sqlite3
import json
import os
import sys

# Get the database path
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "..", "data", "bank_converter.db")

def add_columns():
    """Add preference columns to users table if they don't exist."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Get existing columns
    cursor.execute("PRAGMA table_info(users)")
    existing_columns = [col[1] for col in cursor.fetchall()]
    
    # Define columns to add
    columns_to_add = [
        ("timezone", "VARCHAR DEFAULT 'UTC'"),
        ("notification_preferences", "TEXT DEFAULT '{}'"),
        ("conversion_preferences", "TEXT DEFAULT '{}'"),
        ("two_factor_enabled", "BOOLEAN DEFAULT 0"),
        ("two_factor_secret", "VARCHAR"),
        ("two_factor_backup_codes", "TEXT"),
        ("email_verified", "BOOLEAN DEFAULT 0"),
        ("api_key", "VARCHAR"),
        ("api_key_created_at", "TIMESTAMP"),
        ("api_key_last_used", "TIMESTAMP")
    ]
    
    # Add missing columns
    for column_name, column_def in columns_to_add:
        if column_name not in existing_columns:
            try:
                cursor.execute(f"ALTER TABLE users ADD COLUMN {column_name} {column_def}")
                print(f"✅ Added column: {column_name}")
            except sqlite3.OperationalError as e:
                if "duplicate column name" in str(e):
                    print(f"⚠️  Column already exists: {column_name}")
                else:
                    print(f"❌ Error adding column {column_name}: {e}")
    
    conn.commit()
    conn.close()
    print("\n✅ User preferences migration complete!")

if __name__ == "__main__":
    print("SQLite User Preferences Migration")
    print("=" * 80)
    print(f"Database: {DB_PATH}")
    
    if not os.path.exists(DB_PATH):
        print(f"❌ Database not found at {DB_PATH}")
        sys.exit(1)
    
    add_columns()