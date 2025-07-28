# Bank Statement Converter - Deployment Guide

## Summary of Changes Made

### Enhanced PDF Parser Implementation
1. **Primary Parser**: pdfplumber integration
   - Modern PDF parsing with better table detection
   - Layout preservation for complex statements
   - Word-level extraction with bounding boxes

2. **Smart Parser Selection**
   - Analyzes PDF structure to choose best method
   - Detects scanned PDFs for OCR processing
   - Handles complex layouts with appropriate parsers

3. **PyMuPDF OCR Integration**
   - Column detection algorithm
   - Better text positioning
   - Handles scanned PDFs accurately

4. **Manual Validation Interface**
   - JSON templates for manual review
   - Confidence scoring system
   - Audit trail for corrections

5. **Validation Improvements**
   - Filters phone numbers (1-80, 82-50 patterns)
   - Validates amounts (<$1M threshold)
   - Preserves raw data as fallback

## Files Changed

### New Files
- `backend/universal_parser_enhanced.py` - Main enhanced parser
- `backend/pdfplumber_parser.py` - pdfplumber implementation
- `backend/smart_pdf_analyzer.py` - PDF analysis for parser selection
- `backend/pymupdf_column_parser.py` - PyMuPDF with column detection
- `backend/pymupdf_ocr_parser.py` - PyMuPDF with OCR support
- `backend/manual_validation_interface.py` - Manual review system

### Modified Files
- Updated imports and parser calls throughout the codebase

## Deployment Steps

### Method 1: Direct SSH (When Available)
```bash
# Connect to server
ssh -i /Users/MAC/Downloads/bank-statement-converter.pem ubuntu@bankcsvconverter.com

# Navigate to project
cd /home/ubuntu/bank-statement-converter

# Pull latest changes
git pull origin main

# Install new dependencies
pip3 install pdfplumber pymupdf

# Restart service
sudo systemctl restart bank-converter

# Check status
sudo systemctl status bank-converter
```

### Method 2: AWS Lightsail Console
1. Log into AWS Lightsail console
2. Find your instance (bank-statement-converter)
3. Use the browser-based SSH terminal
4. Run the deployment commands above

### Method 3: GitHub Actions (If Set Up)
1. Push changes trigger automatic deployment
2. Check Actions tab in GitHub for status

### Method 4: Manual Update via FTP/SFTP
1. Use FileZilla or similar with these credentials:
   - Host: bankcsvconverter.com
   - User: ubuntu
   - Auth: SSH key (bank-statement-converter.pem)
   - Port: 22 (SFTP)

2. Upload changed files to:
   - `/home/ubuntu/bank-statement-converter/backend/`

3. SSH in to restart service

## Testing After Deployment

### 1. Basic Functionality Test
```bash
# On the server
cd /home/ubuntu/bank-statement-converter
python3 -c "from backend.universal_parser_enhanced import parse_universal_pdf_enhanced; print('Import successful')"
```

### 2. Web Interface Test
1. Visit https://bankcsvconverter.com
2. Upload test PDFs:
   - example_bank_statement.pdf
   - dummy_statement.pdf
3. Verify extraction accuracy

### 3. API Test
```bash
curl -X POST https://bankcsvconverter.com/api/parse \
  -F "file=@test.pdf" \
  -H "Accept: application/json"
```

## Rollback Plan

If issues occur after deployment:

```bash
# On the server
cd /home/ubuntu/bank-statement-converter

# Revert to previous commit
git log --oneline -5  # Find the previous working commit
git reset --hard <commit-hash>

# Restart service
sudo systemctl restart bank-converter
```

## Monitoring

### Check Logs
```bash
# Application logs
sudo journalctl -u bank-converter -f

# Nginx logs (if applicable)
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

### Check Service Status
```bash
sudo systemctl status bank-converter
ps aux | grep python
```

## Troubleshooting

### SSH Connection Issues
1. Check AWS Lightsail firewall rules (port 22)
2. Verify SSH key permissions: `chmod 400 bank-statement-converter.pem`
3. Try IP address if domain fails: `3.235.19.83`
4. Use AWS Lightsail browser terminal as backup

### Service Won't Start
1. Check Python dependencies: `pip3 list | grep -E "pdfplumber|pymupdf"`
2. Check for syntax errors: `python3 -m py_compile backend/*.py`
3. Review service logs: `sudo journalctl -u bank-converter -n 50`

### Parser Errors
1. Test parser locally first
2. Check file permissions on server
3. Verify all dependencies installed
4. Review validation reports for specific PDFs

## Contact for Issues
- Check GitHub repository for updates
- Review commit history for recent changes
- Test with known working PDFs first