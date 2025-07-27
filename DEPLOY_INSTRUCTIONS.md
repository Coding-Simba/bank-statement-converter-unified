# Deploy Instructions for Updated Parser

## The code has been pushed to GitHub ✅

All 36 commits including the dummy parser and all 17 bank parsers have been pushed to the main branch.

## To deploy to your production server:

1. SSH into your server:
```bash
ssh -i /Users/MAC/Downloads/bank-statement-converter.pem ubuntu@3.235.19.83
```

2. Navigate to the project directory:
```bash
cd /home/ubuntu/bank-statement-converter
```

3. Pull the latest changes:
```bash
git pull origin main
```

4. Restart the services:
```bash
# Restart backend
sudo supervisorctl restart bank-backend

# OR if using systemd:
sudo systemctl restart bank-backend

# Check status
sudo supervisorctl status
# OR
sudo systemctl status bank-backend
```

5. Test the dummy PDF on the live site to confirm it's working.

## What was fixed:
- Added dummy_pdf_parser.py (created Jul 26)
- Added 16 more bank parsers
- Removed "saved for improvement" message from CSV output
- All parsers are now integrated into universal_parser.py

The dummy PDF should now parse correctly and show 12 transactions instead of "No transactions found".