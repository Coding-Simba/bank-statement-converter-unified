#!/usr/bin/env python3
"""Run script for the backend server."""

import os
import sys

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

# Run the server
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=5000,
        reload=True
    )