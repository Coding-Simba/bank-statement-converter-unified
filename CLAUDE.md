# Bank Statement Converter - CLAUDE.md

## Project Overview
Bank statement PDF to CSV converter with web interface. Deployed on AWS Lightsail with Cloudflare.

## Important Guidelines
- **COMMIT AND PUSH AFTER EVERY CODE CHANGE** - No matter how small
- Always test PDF parsing locally before deploying
- Keep track of all changes to prevent regression
- **ALWAYS GIT PUSH** - Push to remote repository after each commit

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
- Fixed authentication persistence issues (2025-07-30)
  - Created auth-fixed.js that doesn't clear tokens on API errors
  - Removed conflicting auth scripts (auth-global.js, auth-persistent.js, auth-universal.js)
  - Users no longer get logged out when navigating between pages

## Testing
- Test PDF: `/Users/MAC/Downloads/example_bank_statement.pdf`
- Always verify parsing works locally before pushing to server

## Deployment Info
- Server: 3.235.19.83 (AWS Lightsail)
- Domain: bankcsvconverter.com (via Cloudflare)
- SSH Key: `/Users/MAC/Downloads/bank-statement-converter.pem`
- User: ubuntu

## Git Workflow & System Health
```bash
# BEFORE making any changes:
./check-backend-health.sh  # ALWAYS verify system is working first!

# After EVERY change:
git add -A
git commit -m "Description of change"
git push origin main  # MANDATORY - Never skip the push!

# After deployment or major changes:
./check-backend-health.sh  # Verify nothing broke
```

**CRITICAL**: Always run `./check-backend-health.sh` before making changes to catch issues early. This prevents the frustrating cycle of fixing one thing and breaking another.

## Common Breaking Points to Watch
1. **Authentication**: Login/logout can break when modifying auth-related files
2. **Stripe Integration**: Payment flow is sensitive to auth changes
3. **Backend Syntax**: Even small syntax errors crash the entire backend
4. **CSS Conflicts**: Global CSS rules can break unrelated pages
5. **Database Models**: Relationship changes can cause 500 errors

## Debug Approach
1. Re-implement Camelot with debugging
2. Add validation to filter headers
3. Test each parser method individually
4. Commit after each successful fix