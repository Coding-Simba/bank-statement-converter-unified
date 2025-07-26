"""Initialize the database with tables."""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from backend.models.database import init_db, DATABASE_PATH

if __name__ == "__main__":
    print("Initializing database...")
    init_db()
    print(f"Database initialized successfully at: {DATABASE_PATH}")
    print("\nTables created:")
    print("- users")
    print("- statements") 
    print("- feedback")
    print("- generation_tracking")