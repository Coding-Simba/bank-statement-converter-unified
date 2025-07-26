# Backend Setup for Split-by-Date Feature

## Quick Start

1. **Run the backend server:**
   ```bash
   ./run-split-backend.sh
   ```

   Or manually:
   ```bash
   cd backend
   python3 split-by-date.py
   ```

2. **The server will start on http://localhost:5000**

3. **Access the split-by-date tool at http://localhost:8080/split-by-date.html**

## Requirements

The backend requires Python 3 and will automatically install:
- Flask (web framework)
- PyPDF2 (PDF processing)
- pandas (data manipulation)
- tabula-py (table extraction from PDFs)

## How it Works

1. Upload a PDF bank statement
2. Select a date range (or use quick presets)
3. Click "Split & Download"
4. The backend will:
   - Extract transactions from the PDF
   - Filter by your selected date range
   - Return a CSV file with only those transactions

## Troubleshooting

### "Backend server is not running" error
- Make sure you've started the backend with `./run-split-backend.sh`
- Check that port 5000 is not being used by another application
- Try running `python3 backend/split-by-date.py` directly to see any error messages

### Java not found error (for tabula-py)
- tabula-py requires Java to be installed
- On Mac: `brew install openjdk`
- On Ubuntu: `sudo apt-get install default-jre`

### Port 5000 already in use
- Kill the process using port 5000: `lsof -ti:5000 | xargs kill -9`
- Or change the port in `backend/split-by-date.py` (last line)