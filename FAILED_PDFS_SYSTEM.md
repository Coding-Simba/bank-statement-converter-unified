# Failed PDFs Management System

## Overview
The bank statement converter has a built-in system to automatically save PDFs that fail to parse correctly. This helps identify problematic PDFs for improving the parsers.

## How It Works

### 1. Automatic Detection
When `universal_parser.py` processes a PDF, it uses `FailedPDFManager` to check if parsing was successful based on these criteria:
- No transactions found
- Less than 50% of transactions are valid (have description/amount)
- Less than 30% of transactions have dates
- Transactions with unrealistic amounts (0 or > $1 million)

### 2. Storage Location
Failed PDFs are saved to: `/home/ubuntu/bank-statement-converter-unified/backend/failed_pdfs/`

### 3. File Naming
Failed PDFs are saved with timestamp and hash:
- Format: `YYYYMMDD_HHMMSS_[hash8]_originalname.pdf`
- Example: `20250128_143022_a1b2c3d4_bank_statement.pdf`

### 4. Metadata Tracking
A `failed_pdfs_metadata.json` file tracks:
- Original filename
- Save timestamp
- Number of transactions found/valid
- Error information
- Sample transactions
- Status (pending_review, reviewed, fixed)

## Fetching Failed PDFs

### Option 1: Using the Provided Script
```bash
# Make script executable
chmod +x fetch_failed_pdfs.sh

# Run the script
./fetch_failed_pdfs.sh
```

### Option 2: Manual Commands
```bash
# Create local directory
mkdir -p retrieved_failed_pdfs

# Fetch metadata file
scp -i /Users/MAC/Downloads/bank-statement-converter.pem \
    ubuntu@3.235.19.83:/home/ubuntu/bank-statement-converter-unified/backend/failed_pdfs/failed_pdfs_metadata.json \
    retrieved_failed_pdfs/

# List PDFs from last 24 hours
ssh -i /Users/MAC/Downloads/bank-statement-converter.pem \
    ubuntu@3.235.19.83 \
    "find /home/ubuntu/bank-statement-converter-unified/backend/failed_pdfs -name '*.pdf' -mtime -1 -ls"

# Download all PDFs from last 24 hours
ssh -i /Users/MAC/Downloads/bank-statement-converter.pem \
    ubuntu@3.235.19.83 \
    "cd /home/ubuntu/bank-statement-converter-unified/backend/failed_pdfs && tar -czf - *.pdf" | tar -xzf - -C retrieved_failed_pdfs/
```

### Option 3: Python Script
```bash
# Install required libraries
pip install paramiko scp

# Run the Python script
python fetch_failed_pdfs.py
```

## Analyzing Failed PDFs

Once you have the failed PDFs locally:

1. **Check metadata**: Review `failed_pdfs_metadata.json` to understand failure patterns
2. **Test locally**: Run the PDFs through local parsers to debug
3. **Common issues**:
   - Scanned PDFs needing OCR
   - New bank formats not recognized
   - Complex table layouts
   - Missing date formats
   - Non-standard transaction patterns

## Improving Parsers

Based on failed PDFs:
1. Identify the bank/format
2. Create or update the appropriate parser
3. Test with the failed PDF
4. Mark as "fixed" in metadata
5. Deploy updated parser

## Server Connection Issues

If you can't connect to the server:
1. Check server status in AWS console
2. Verify SSH key permissions: `chmod 400 /Users/MAC/Downloads/bank-statement-converter.pem`
3. Check security group allows SSH (port 22)
4. Try alternative connection methods or wait for server availability