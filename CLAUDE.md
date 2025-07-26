# Bank Statement Converter - CLAUDE.md

## Project Overview
Bank statement PDF to CSV converter with web interface. Deployed on AWS Lightsail with Cloudflare.

## Important Guidelines
- **COMMIT AFTER EVERY CODE CHANGE** - No matter how small
- Always test PDF parsing locally before deploying
- Keep track of all changes to prevent regression

## Current Issues (2025-01-26)
1. ~~PDF parser extracting headers as transactions~~ - FIXED with Camelot filtering
2. ~~Camelot was removed but needs to be re-implemented~~ - DONE with debug logging
3. ~~Lost working functionality~~ - RESTORED and improved

## Recent Fixes
- Re-implemented Camelot parser with header filtering
- Added is_valid_transaction() to filter out non-transaction content
- Successfully deployed to production server
- All PDFs now parsing correctly without header issues
- Fixed multi-page PDF parsing with advanced OCR (2025-07-26)
  - Added advanced_ocr_parser.py for image-based pages
  - Universal parser now automatically tries OCR for better extraction
  - Successfully extracts all transactions from multi-line formats

## Testing
- Test PDF: `/Users/MAC/Downloads/example_bank_statement.pdf`
- Always verify parsing works locally before pushing to server

## Deployment Info
- Server: 3.235.19.83 (AWS Lightsail)
- Domain: bankcsvconverter.com (via Cloudflare)
- SSH Key: `/Users/MAC/Downloads/bank-statement-converter.pem`
- User: ubuntu

## Git Workflow
```bash
# After EVERY change:
git add -A
git commit -m "Description of change"
git push origin main
```

## Debug Approach
1. Re-implement Camelot with debugging
2. Add validation to filter headers
3. Test each parser method individually
4. Commit after each successful fix