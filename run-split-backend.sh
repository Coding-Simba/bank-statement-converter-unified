#!/bin/bash

echo "Starting Split-by-Date Backend Server..."
echo "======================================="

# Navigate to backend directory
cd backend

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install requirements
echo "Installing requirements..."
pip install -r requirements.txt

# Run the split-by-date server
echo "Starting server on http://localhost:5000"
echo "The split-by-date tool will be available at http://localhost:8080/split-by-date.html"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

python split-by-date.py