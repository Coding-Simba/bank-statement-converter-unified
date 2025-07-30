#!/usr/bin/env python3
"""Fix database schema on production server"""

import sys
import os
sys.path.insert(0, '/home/ubuntu/bank-statement-converter/backend')

from models.database import Base, engine, init_db

# Drop all tables and recreate with correct schema
print("Recreating database with correct schema...")
Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)

# Initialize with default data
init_db()

print("Database recreated successfully!")

# Create a test user
from models.database import get_db, User
from utils.auth import hash_password

db = next(get_db())
test_user = User(
    email="test@example.com",
    password_hash=hash_password("test123"),
    full_name="Test User",
    account_type="free",
    is_active=True,
    email_verified=True
)
db.add(test_user)
db.commit()
print("Test user created: test@example.com / test123")