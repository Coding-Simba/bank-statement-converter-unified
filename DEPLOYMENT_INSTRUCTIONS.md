# Deployment Instructions for Bank Statement Parser Update

## Overview
The bank-specific PDF parsers have been successfully created and pushed to GitHub. Follow these steps to deploy the updates to your AWS Lightsail server.

## Prerequisites
- SSH access to your AWS Lightsail server
- Server IP address or domain: bankcsvconverter.com
- SSH key file (usually a .pem file)

## Deployment Steps

### 1. Connect to Your Server
```bash
ssh -i /path/to/your-key.pem ubuntu@your-server-ip
```

### 2. Navigate to Project Directory
```bash
cd ~/bank-statement-converter-unified
```

### 3. Pull Latest Changes
```bash
git pull origin main
```

### 4. Install/Update Dependencies
```bash
cd backend
source venv/bin/activate  # Activate virtual environment
pip install -r requirements.txt
```

### 5. Restart the Backend Service
```bash
# If using systemd
sudo systemctl restart bankconverter-backend

# OR if using PM2
pm2 restart bankconverter-backend

# OR if running manually
# Kill the existing process
ps aux | grep "python.*main.py" | grep -v grep | awk '{print $2}' | xargs kill -9
# Start the backend
nohup python main.py > backend.log 2>&1 &
```

### 6. Verify Deployment
```bash
# Check if backend is running
curl http://localhost:8000/health

# Check logs
tail -f backend.log
```

## What's New in This Update

### New Bank Parsers Added:
1. **Bank of America** (`bank_of_america_parser.py`)
   - Handles MM/DD/YY date format
   - Processes Zelle transfers, ATM transactions, direct deposits
   - Successfully extracts 48 transactions from test PDFs

2. **Wells Fargo** (`wells_fargo_parser.py`)
   - Handles M/D/YYYY date format
   - Processes ATM deposits/withdrawals, Square transactions
   - Successfully extracts 93 transactions from test PDFs

3. **RBC (Royal Bank of Canada)** (`rbc_parser.py`)
   - Handles D Mon date format (e.g., "3 Apr")
   - Processes e-Transfers, Interac purchases
   - Successfully extracts 16 transactions from test PDFs

4. **Commonwealth Bank of Australia** (`commonwealth_parser.py`)
   - Handles DD Mon date format with AUD currency
   - Processes international transactions, card payments
   - Successfully extracts 77 transactions from test PDFs

### Updated Files:
- `backend/universal_parser.py` - Updated to route to new bank-specific parsers
- `backend/api/statements.py` - Updated to use the enhanced parser system

## Testing the New Parsers

Once deployed, test with sample PDFs from each supported bank:

```bash
# Test via API
curl -X POST http://localhost:8000/api/convert \
  -F "file=@/path/to/bank-statement.pdf" \
  -H "Accept: application/json"
```

## Troubleshooting

### If parsers aren't working:
1. Check backend logs: `tail -f backend.log`
2. Verify Python dependencies: `pip list | grep -E "tabula|pdfplumber|pandas"`
3. Ensure PDF files are being uploaded correctly
4. Check file permissions on the uploads directory

### Common Issues:
- **Import errors**: Run `pip install -r requirements.txt` again
- **Parser not detected**: Check the bank detection logic in `universal_parser.py`
- **No transactions extracted**: Verify the PDF format matches expected patterns

## Rollback Instructions

If needed, you can rollback to the previous version:

```bash
git log --oneline -5  # Find the previous commit hash
git checkout <previous-commit-hash>
sudo systemctl restart bankconverter-backend
```

## Support

The parsers have been tested locally and are working correctly. If you encounter any issues during deployment, check:
1. Server logs
2. Python version compatibility (tested with Python 3.12)
3. PDF file permissions
4. Memory usage during PDF processing