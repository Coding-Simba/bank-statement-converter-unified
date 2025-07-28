#!/bin/bash
cd /Users/MAC/chrome/bank-statement-converter-unified
source backend/venv/bin/activate
cd backend
python -m uvicorn main:app --reload --port 5000 --log-level info &
echo "Backend server started on port 5000"
echo "Process ID: $!"