# SQLite configuration for cheap hosting
# Replace database.py connection string with:

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Use SQLite for cheap/free hosting
DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "app.db")
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

# SQLite connection (no server needed!)
SQLALCHEMY_DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args={"check_same_thread": False}  # Needed for SQLite
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)