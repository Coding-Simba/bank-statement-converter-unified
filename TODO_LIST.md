# TODO List: Custom Bank Parsers Implementation

Based on the comprehensive analysis of all 21 PDFs, the following banks need custom parsers to properly extract transaction data. The main issue for most is missing dates, but some have additional extraction problems.

## High Priority - Banks with Critical Issues

### 1. ANZ Bank (Australia ANZ.pdf)
- **Issue**: Missing dates (1/1 transactions)
- **Sample**: `1/15 | /15 ETHEL ST | $1.00`
- **Requirements**: 
  - Implement date extraction logic
  - Parse Australian date format
  - Handle partial/corrupted text

### 2. BECU (USA BECU statement 4 pages.pdf)
- **Issue**: Missing dates (72/72 transactions)
- **Sample**: `04/03 | External Deposit THE BOEING COMPA - DIR DEP | $3107.52`
- **Requirements**:
  - Date extraction from MM/DD format
  - Multi-page statement support
  - Handle various transaction types

### 3. Citizens Bank (USA Citizens Bank.pdf)
- **Issue**: Missing dates (85/85 transactions)
- **Sample**: `1/1 | 3299 | $283.98`
- **Requirements**:
  - Complex date parsing
  - Better description extraction
  - Handle check numbers

### 4. Commonwealth Bank (Australia Commonwealth J C.pdf)
- **Issue**: Missing dates (257/257 transactions)
- **Sample**: `27/06/2021 | /06/2021 59.99 $4,935.74 CR | $27.00`
- **Requirements**:
  - Fix date extraction (dates are present but not parsed)
  - Handle Australian DD/MM/YYYY format
  - Parse balance column correctly

### 5. Discover Bank (USA Discover Bank.pdf)
- **Issue**: Missing dates, only 1 transaction extracted from 6 pages
- **Sample**: `23-12-0358 | 12-03587 | $170923.00`
- **Requirements**:
  - Complete table extraction overhaul
  - Proper date format parsing
  - Handle account number patterns

## Medium Priority - Banks with Date Issues

### 6. Green Dot Bank (USA Green Dot Bank Statement 3 page.pdf)
- **Issue**: Missing dates (5/5 transactions), low extraction rate
- **Sample**: `04/15 | IDES PAYMENTS Deposit | $1338.00`
- **Requirements**:
  - MM/DD date format parsing
  - Better transaction detection

### 7. Lloyds Bank (UK Lloyds Bank.pdf)
- **Issue**: Missing dates (2/2 transactions), very low extraction
- **Sample**: `30-13-55 | 13-55 | $30.00`
- **Requirements**:
  - UK date format support
  - Improve table detection

### 8. Metro Bank (United Kingdom Metro Bank.pdf)
- **Issue**: Missing dates (1/1 transaction)
- **Sample**: `21/01/2021 | /01/2021 | $21.00`
- **Requirements**:
  - UK DD/MM/YYYY format
  - Better text extraction

### 9. Nationwide (UK Nationwide word pdf.pdf)
- **Issue**: Missing dates (8/8 transactions), low extraction rate
- **Sample**: `07-04-36 | Aug 2020 Sort Code 07-04-36 | $14.00`
- **Requirements**:
  - Handle Word-converted PDFs
  - Parse UK banking codes
  - Extract dates from various formats

### 10. Netspend (USA Netspend Bank Statement.pdf)
- **Issue**: Missing dates (4/4 transactions)
- **Sample**: `1-80 | 801-930-0991 | $1.00`
- **Requirements**:
  - No tables detected - pure text parsing
  - Phone number vs date differentiation

### 11. PayPal (USA PayPal Account Statement.pdf)
- **Issue**: Missing dates (21/21 transactions)
- **Sample**: `Apr 01, 2022 | - May | $1.00`
- **Requirements**:
  - Parse "MMM DD, YYYY" format
  - Handle PayPal-specific formats

### 12. Scotiabank (Canada Scotiabank.pdf)
- **Issue**: Missing dates (2/2 transactions)
- **Sample**: `1-88 | 888-861-5443 / 416-701-7820 | $1.00`
- **Requirements**:
  - Canadian format support
  - Better transaction detection

### 13. SunTrust (USA Suntrust.pdf)
- **Issue**: Missing dates (21/21 transactions)
- **Sample**: `04/04/2022 | Petron - C5 Station | $223.26`
- **Requirements**:
  - Date format is present but not extracted
  - Fix MM/DD/YYYY parsing

### 14. Walmart MoneyCard (Walmart Money Card Bank Statement 3 page.pdf)
- **Issue**: Missing dates (31/31 transactions)
- **Sample**: `02/01 | Nancyhomes32@Gmail.com | $-20.00`
- **Requirements**:
  - MM/DD format parsing
  - Handle email addresses in descriptions

### 15. Westpac (Australia Westpac bank statement.pdf)
- **Issue**: Missing dates (26/26 transactions)
- **Sample**: `2/11/2022 | Transaction | $1136.00`
- **Requirements**:
  - Australian D/MM/YYYY format
  - Fix date parsing logic

## Low Priority - Template/Unknown Banks

### 16. Bank-Statement-Template-4-TemplateLab.pdf
- **Issue**: No transactions extracted
- **Requirements**:
  - May be a template without real data
  - Verify if contains actual transactions

### 17. merged_statements_2025-07-26.pdf
- **Issue**: Missing dates (17/17 transactions)
- **Sample**: `mm/dd/yyyy | Fast Payment       Amazon | $-132.30`
- **Requirements**:
  - Handle placeholder date formats
  - Parse merged statement structure

## Implementation Strategy

1. **Create base parser class** with common functionality:
   - Date detection and parsing
   - Amount extraction and validation
   - Description cleaning
   - Transaction deduplication

2. **Implement region-specific parsers**:
   - US parser (MM/DD formats)
   - UK parser (DD/MM formats)
   - Australian parser (D/MM/YYYY formats)
   - Canadian parser

3. **Add bank-specific overrides** for:
   - Column detection
   - Table extraction
   - Special format handling

4. **Testing approach**:
   - Unit tests for each parser
   - Integration tests with sample PDFs
   - Validation against expected transaction counts

5. **Priority order**:
   - Start with high-value banks (BECU, Citizens, Commonwealth)
   - Move to common formats (US banks with MM/DD)
   - Handle special cases (PayPal, templates)

## Success Metrics

- All banks should extract at least 90% of transactions
- All valid dates should be parsed correctly
- No phone numbers should be mistaken for dates
- Amounts should be realistic (< $1M for most transactions)
- Descriptions should be meaningful (not just codes)