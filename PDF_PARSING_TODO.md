# PDF Bank Statement Parsing TODO List

## Overview
Test and fix parsing for 17 different bank statement PDFs from various countries and banks. Each PDF must be thoroughly tested to ensure ALL transactions from ALL pages are correctly extracted to CSV format.

## Progress Tracking
- [x] Total PDFs to test: 17
- [x] PDFs completed: 17
- [x] PDFs with issues fixed: 17

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
- [x] **USA Bank of America.pdf**
  - Path: `/Users/MAC/Desktop/pdfs/1/USA Bank of America.pdf`
  - Status: ✅ Fixed and tested
  - Issues found: Multi-section format with separate "Deposits and other credits" and "Withdrawals and other debits" sections
  - Fix applied: Created boa_parser.py that handles separate sections. Successfully extracts 69 transactions (28 deposits, 41 withdrawals) 

- [x] **USA BECU statement 4 pages.pdf**
  - Path: `/Users/MAC/Desktop/pdfs/1/USA BECU statement 4 pages.pdf`
  - Status: ✅ Fixed and tested
  - Issues found: Multi-page format with Deposits/Withdrawals sections that don't continue across all pages. Different spacing patterns on different pages.
  - Fix applied: Created becu_parser.py that handles section headers and also parses transactions without section headers. Successfully extracts 71 transactions (9 deposits, 62 withdrawals) 

- [x] **USA Citizens Bank.pdf**
  - Path: `/Users/MAC/Desktop/pdfs/1/USA Citizens Bank.pdf`
  - Status: ✅ Fixed and tested
  - Issues found: M/D date format without year, multi-line transaction descriptions that continue across lines
  - Fix applied: Created citizens_parser.py that handles multi-line descriptions and M/D dates. Successfully extracts 68 transactions (9 deposits, 59 withdrawals) 

- [x] **USA Discover Bank.pdf**
  - Path: `/Users/MAC/Desktop/pdfs/1/USA Discover Bank.pdf`
  - Status: ✅ Fixed and tested
  - Issues found: Credit card statement format with categories (Payments, Merchandise, Restaurants, etc.) and Mon D date format
  - Fix applied: Created discover_parser.py that handles category headers and transaction/post dates. Successfully extracts 32 transactions (1 payment credit, 31 purchase debits) 

- [x] **USA Green Dot Bank Statement 3 page.pdf**
  - Path: `/Users/MAC/Desktop/pdfs/1/USA Green Dot Bank Statement 3 page.pdf`
  - Status: ✅ Fixed and tested
  - Issues found: Simple statement format with only 2 transactions. Uses MM/DD date format and +/- amount indicators
  - Fix applied: Created greendot_parser.py for simple transaction format. Successfully extracts 2 transactions (1 deposit, 1 fee) 

- [x] **USA Netspend Bank Statement.pdf**
  - Path: `/Users/MAC/Desktop/pdfs/1/USA Netspend Bank Statement.pdf`
  - Status: ✅ Fixed and tested
  - Issues found: Table format with columns for Date, Details, Withdrawals, Deposits, and Balance. Uses Mon D date format.
  - Fix applied: Created netspend_parser.py using column position parsing. Successfully extracts 24 transactions (9 deposits, 15 withdrawals) 

- [x] **USA PayPal Account Statement.pdf**
  - Path: `/Users/MAC/Desktop/pdfs/1/USA PayPal Account Statement.pdf`
  - Status: ✅ Fixed and tested
  - Issues found: PayPal format with columns for Date, Description, Currency, Amount, Fees, and Total. Some totals wrap to next line.
  - Fix applied: Created paypal_parser.py that handles wrapped transactions and extracts fees/totals. Successfully extracts all 10 transactions (5 deposits, 5 transfers) 

- [x] **USA Suntrust.pdf**
  - Path: `/Users/MAC/Desktop/pdfs/1/USA Suntrust.pdf`
  - Status: ✅ Fixed and tested
  - Issues found: Credit card statement format with simple transaction layout (date, description, amount)
  - Fix applied: Created suntrust_parser.py that handles MM/DD/YYYY date format. Successfully extracts all 9 transactions (all charges) 

- [x] **USA Woodforest.pdf**
  - Path: `/Users/MAC/Desktop/pdfs/1/USA Woodforest.pdf`
  - Status: ✅ Fixed and tested
  - Issues found: Business checking format with columns for Date, Credits, Debits, Balance, and Description. Uses MM-DD date format.
  - Fix applied: Created woodforest_parser.py using column position parsing. Successfully extracts all 51 transactions (10 deposits, 41 withdrawals) 

- [x] **Walmart Money Card Bank Statement 3 page.pdf**
  - Path: `/Users/MAC/Desktop/pdfs/1/Walmart Money Card Bank Statement 3 page.pdf`
  - Status: ✅ Fixed and tested
  - Issues found: Complex multi-line format where descriptions appear above dates. Uses MM/DD date format with amount patterns varying.
  - Fix applied: Created walmart_parser.py that looks for amount lines and searches backward for dates and descriptions. Successfully extracts 16 transactions (3 deposits, 13 withdrawals) 

## Code Changes Log
Document each parser update here with timestamp and what was changed:

1. **2025-01-27**: Initial TODO list created
2. **2025-01-27 01:33**: Created summary_statement_parser.py for ANZ home loan statement (summary-only format)
3. **2025-01-27 02:45**: Created commonwealth_simple_parser.py for Commonwealth Bank multi-line format with proper debit/credit detection
4. **2025-01-27 03:00**: Created westpac_parser.py for Westpac In/Out column format with negative values
5. **2025-01-27 03:15**: Created rbc_parser_v2.py for RBC multi-line format where date appears once for multiple transactions
6. **2025-01-27 03:30**: Created monzo_parser.py for Monzo simple table format
7. **2025-01-27 03:45**: Created monese_simple_parser.py for Monese multi-line format with transaction reconstruction
8. **2025-01-27 04:00**: Created santander_parser.py for Santander multi-line format with spacing detection
9. **2025-01-27 04:15**: Created boa_parser.py for Bank of America multi-section format
10. **2025-01-27 04:30**: Created becu_parser.py for BECU multi-page format with varying section headers
11. **2025-01-27 04:45**: Created citizens_parser.py for Citizens Bank M/D date format with multi-line descriptions
12. **2025-01-27 05:00**: Created discover_parser.py for Discover credit card format with transaction categories
13. **2025-01-27 05:15**: Created greendot_parser.py for Green Dot simple statement format
14. **2025-01-27 05:30**: Created netspend_parser.py for Netspend table format with column positions
15. **2025-01-27 05:45**: Created paypal_parser.py for PayPal account statements with fees and wrapped totals
16. **2025-01-27 06:00**: Created suntrust_parser.py for SunTrust credit card statements
17. **2025-01-27 06:15**: Created woodforest_parser.py for Woodforest National Bank business checking
18. **2025-01-27 06:30**: Created walmart_parser.py for Walmart Money Card statements with multi-line format 

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