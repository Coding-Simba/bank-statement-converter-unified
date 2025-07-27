# PDF Bank Statement Parsing TODO List

## Overview
Test and fix parsing for 17 different bank statement PDFs from various countries and banks. Each PDF must be thoroughly tested to ensure ALL transactions from ALL pages are correctly extracted to CSV format.

## Progress Tracking
- [ ] Total PDFs to test: 17
- [ ] PDFs completed: 7
- [ ] PDFs with issues fixed: 7

## Testing Methodology for Each PDF
1. Run parser on the PDF
2. Check total transaction count
3. Verify deposits vs withdrawals classification
4. Use AI to analyze if all transactions were captured
5. Check multi-page extraction
6. Update parser code if needed
7. Commit changes after each fix
8. Document the fix in this file

## PDF Test Status

### Australia (3 PDFs)
- [x] **Australia ANZ.pdf**
  - Path: `/Users/MAC/Desktop/pdfs/1/Australia ANZ.pdf`
  - Status: ✅ Fixed and tested
  - Issues found: Home loan statement with only summary totals, no individual transactions
  - Fix applied: Created summary_statement_parser.py to extract summary lines as transactions 

- [x] **Australia Commonwealth J C.pdf**
  - Path: `/Users/MAC/Desktop/pdfs/1/Australia Commonwealth J C.pdf`
  - Status: ✅ Fixed and tested
  - Issues found: Complex multi-line format with debit/credit columns. Initial parsers were extracting balance amounts instead of transaction amounts.
  - Fix applied: Created commonwealth_simple_parser.py that correctly identifies 461 transactions (90 deposits, 371 withdrawals) by parsing the specific column layout

- [x] **Australia Westpac bank statement.pdf**
  - Path: `/Users/MAC/Desktop/pdfs/1/Australia Westpac bank statement.pdf`
  - Status: ✅ Fixed and tested
  - Issues found: In/Out column format with negative values in Out column. Parser was treating all transactions as deposits.
  - Fix applied: Created westpac_parser.py that correctly handles negative Out values. Successfully extracts 15 transactions (7 deposits, 8 withdrawals)

### Canada (1 PDF)
- [x] **Canada RBC.pdf**
  - Path: `/Users/MAC/Desktop/pdfs/1/Canada RBC.pdf`
  - Status: ✅ Fixed and tested
  - Issues found: Multi-line transactions where date appears once for multiple transactions. Initial parser only found 6 transactions.
  - Fix applied: Created rbc_parser_v2.py that handles multi-line format. Successfully extracts 50 transactions (8 deposits, 42 withdrawals)

### UK (3 PDFs)
- [x] **Monzo Bank st. word.pdf**
  - Path: `/Users/MAC/Desktop/pdfs/1/Monzo Bank st. word.pdf`
  - Status: ✅ Fixed and tested
  - Issues found: Default parser was only extracting dates as descriptions
  - Fix applied: Created monzo_parser.py for simple table format. Successfully extracts 28 transactions (13 deposits, 15 withdrawals) with proper descriptions

- [x] **UK Monese Bank Statement.pdf**
  - Path: `/Users/MAC/Desktop/pdfs/1/UK Monese Bank Statement.pdf`
  - Status: ✅ Fixed and tested
  - Issues found: Multi-line format where some transactions split across lines. Initial parser missed the £200 transaction.
  - Fix applied: Created monese_simple_parser.py that finds all amounts and reconstructs transactions. Successfully extracts all 29 transactions (6 deposits, 23 withdrawals)

- [x] **UK Santander.pdf**
  - Path: `/Users/MAC/Desktop/pdfs/1/UK Santander.pdf`
  - Status: ✅ Fixed and tested
  - Issues found: Multi-line format with reference numbers on separate lines. Initial parser was confusing balance with transaction amount.
  - Fix applied: Created santander_parser.py with proper spacing detection. Successfully extracts 27 transactions (4 deposits, 23 withdrawals)

### USA (10 PDFs)
- [ ] **USA Bank of America.zip**
  - Path: `/Users/MAC/Desktop/pdfs/1/USA Bank of America.zip`
  - Status: Not tested (needs unzipping first)
  - Issues found: 
  - Fix applied: 

- [ ] **USA BECU statement 4 pages.pdf**
  - Path: `/Users/MAC/Desktop/pdfs/1/USA BECU statement 4 pages.pdf`
  - Status: Not tested
  - Issues found: 
  - Fix applied: 

- [ ] **USA Citizens Bank.pdf**
  - Path: `/Users/MAC/Desktop/pdfs/1/USA Citizens Bank.pdf`
  - Status: Not tested
  - Issues found: 
  - Fix applied: 

- [ ] **USA Discover Bank.pdf**
  - Path: `/Users/MAC/Desktop/pdfs/1/USA Discover Bank.pdf`
  - Status: Not tested
  - Issues found: 
  - Fix applied: 

- [ ] **USA Green Dot Bank Statement 3 page.pdf**
  - Path: `/Users/MAC/Desktop/pdfs/1/USA Green Dot Bank Statement 3 page.pdf`
  - Status: Not tested
  - Issues found: 
  - Fix applied: 

- [ ] **USA Netspend Bank Statement.pdf**
  - Path: `/Users/MAC/Desktop/pdfs/1/USA Netspend Bank Statement.pdf`
  - Status: Not tested
  - Issues found: 
  - Fix applied: 

- [ ] **USA PayPal Account Statement.pdf**
  - Path: `/Users/MAC/Desktop/pdfs/1/USA PayPal Account Statement.pdf`
  - Status: Not tested
  - Issues found: 
  - Fix applied: 

- [ ] **USA Suntrust.pdf**
  - Path: `/Users/MAC/Desktop/pdfs/1/USA Suntrust.pdf`
  - Status: Not tested
  - Issues found: 
  - Fix applied: 

- [ ] **USA Woodforest.pdf**
  - Path: `/Users/MAC/Desktop/pdfs/1/USA Woodforest.pdf`
  - Status: Not tested
  - Issues found: 
  - Fix applied: 

- [ ] **Walmart Money Card Bank Statement 3 page.pdf**
  - Path: `/Users/MAC/Desktop/pdfs/1/Walmart Money Card Bank Statement 3 page.pdf`
  - Status: Not tested
  - Issues found: 
  - Fix applied: 

## Code Changes Log
Document each parser update here with timestamp and what was changed:

1. **2025-01-27**: Initial TODO list created
2. **2025-01-27 01:33**: Created summary_statement_parser.py for ANZ home loan statement (summary-only format)
3. **2025-01-27 02:45**: Created commonwealth_simple_parser.py for Commonwealth Bank multi-line format with proper debit/credit detection
4. **2025-01-27 03:00**: Created westpac_parser.py for Westpac In/Out column format with negative values 

## Common Issues Found
List recurring issues across multiple PDFs:
- 
- 

## Test Script Location
- Main test script: `test_all_bank_pdfs.py`
- Individual test results: `test_results/` directory

## Next Steps When Resuming
1. Check this file for last completed PDF
2. Run test script on next PDF in list
3. Analyze results and fix any issues
4. Update this TODO list
5. Commit changes
6. Continue with next PDF