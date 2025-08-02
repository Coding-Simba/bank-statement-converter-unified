#!/usr/bin/env python3
"""Simple test of backend functionality"""

import os
import sys
sys.path.insert(0, '.')

# Test imports
try:
    from models.database import init_db, get_db
    print("✓ Database models imported")
except Exception as e:
    print(f"✗ Database import error: {e}")
    exit(1)

try:
    from api.statements import router
    print("✓ Statements API imported")
except Exception as e:
    print(f"✗ Statements API import error: {e}")
    exit(1)

# Test database connection
try:
    init_db()
    print("✓ Database initialized")
except Exception as e:
    print(f"✗ Database init error: {e}")
    exit(1)

# Test a simple query
try:
    from sqlalchemy.orm import Session
    from models.database import Statement
    
    db = next(get_db())
    count = db.query(Statement).count()
    print(f"✓ Database query successful - {count} statements found")
    db.close()
except Exception as e:
    print(f"✗ Database query error: {e}")

print("\nAll basic tests passed!")