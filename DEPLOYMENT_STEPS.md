# Manual Deployment Steps

The backend has been updated with unified PDF parsing. To deploy to your AWS server:

## 1. SSH into the server
```bash
ssh -i [your-key-file] ubuntu@3.235.19.83
```

## 2. Navigate to the project directory
```bash
cd /home/ubuntu/bank-statement-converter-unified
```

## 3. Pull the latest changes
```bash
git pull origin main
```

## 4. Navigate to backend and activate virtual environment
```bash
cd backend
source venv/bin/activate
```

## 5. Install any new dependencies
```bash
pip install -r requirements.txt
```

## 6. Restart the FastAPI service
```bash
sudo systemctl restart fastapi
```

## 7. Check service status
```bash
sudo systemctl status fastapi
```

## 8. Check logs if needed
```bash
sudo journalctl -u fastapi -f
```

## What's New in This Deployment

1. **New API Endpoints:**
   - `/api/split-statement` - Split PDF statements by date range
   - `/api/analyze-transactions` - Analyze transactions with financial insights

2. **Updated Files:**
   - `backend/main.py` - Includes new routers
   - `backend/api/split_statement.py` - New file
   - `backend/api/analyze_transactions.py` - New file

3. **Frontend Updates:**
   - `split-by-date.html` - Now uses unified backend
   - `analyze-transactions.html` - Now uses unified backend
   - `js/api-config.js` - New file for API configuration
   - `js/analyze-transactions-api.js` - New file for transaction analysis

All PDF parsing now goes through the same universal parser for consistency!