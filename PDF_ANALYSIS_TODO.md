# PDF Analysis TODO List

## Overview
Analyze bank statement PDFs to identify parsing issues and missing data (transactions, descriptions, tables).

## PDFs to Analyze

### Canadian Banks
- [ ] **Canada RBC.pdf** - Royal Bank of Canada
  - [ ] Check transaction extraction
  - [ ] Verify date formats
  - [ ] Check description parsing
  - [ ] Verify balance calculations
  - [ ] Note any special table formats

- [ ] **Canada RBC (1).pdf** - Royal Bank of Canada (duplicate?)
  - [ ] Compare with first RBC file
  - [ ] Check for format differences

### Australian Banks
- [ ] **Australia Westpac bank statement.pdf**
  - [ ] Check transaction table structure
  - [ ] Verify currency handling (AUD)
  - [ ] Check date format (DD/MM/YYYY)
  - [ ] Verify description extraction

- [ ] **Australia Bendigo Bank Statement.pdf**
  - [ ] Analyze table layout
  - [ ] Check for multiple account sections
  - [ ] Verify transaction categorization

- [ ] **Australia Commonwealth J C.pdf**
  - [ ] Check transaction format
  - [ ] Verify running balance extraction
  - [ ] Check for special characters in descriptions

### UK Banks
- [ ] **United Kingdom Metro Bank.pdf**
  - [ ] Check UK date format handling
  - [ ] Verify GBP currency extraction
  - [ ] Check transaction reference numbers

- [ ] **UK Nationwide word pdf.pdf**
  - [ ] Check if Word-to-PDF conversion affects parsing
  - [ ] Verify table structure integrity
  - [ ] Check for formatting issues

### USA Banks - Major Banks
- [ ] **USA Bank of America.pdf**
  - [ ] Analyze multi-column layout
  - [ ] Check pending vs posted transactions
  - [ ] Verify check number extraction
  - [ ] Test description parsing

- [ ] **USA Wells Fargo 7 pages.pdf**
  - [ ] Test multi-page handling
  - [ ] Check page break transaction continuity
  - [ ] Verify running balance across pages
  - [ ] Check for summary sections

- [ ] **USA PNC 2.pdf**
  - [ ] Analyze PNC format
  - [ ] Check transaction type indicators
  - [ ] Verify fee extraction

- [ ] **USA Citizens Bank.pdf**
  - [ ] Check transaction table format
  - [ ] Verify date parsing
  - [ ] Check for additional tables (fees, interest)

### USA Banks - Credit Unions & Others
- [ ] **USA Navy Federal 5 pages.pdf**
  - [ ] Test 5-page document handling
  - [ ] Check for member-specific formatting
  - [ ] Verify transaction codes

- [ ] **USA DCU Bank Statement 5 page.pdf**
  - [ ] Digital Federal Credit Union format
  - [ ] Check for unique table structures
  - [ ] Verify all 5 pages parse correctly

- [ ] **USAA Bank Statement 5 page.pdf**
  - [ ] Check military bank specific format
  - [ ] Verify transaction details extraction
  - [ ] Test insurance/investment sections

- [ ] **USA BECU statement 4 pages.pdf**
  - [ ] Boeing Employees Credit Union
  - [ ] Check for member rewards data
  - [ ] Verify 4-page continuity

- [ ] **USA Woodforest.pdf**
  - [ ] Check regional bank format
  - [ ] Verify fee structure parsing
  - [ ] Check transaction codes

### Special Cases
- [ ] **USA PayPal Account Statement.pdf**
  - [ ] Check non-traditional bank format
  - [ ] Verify transaction ID extraction
  - [ ] Check currency conversion handling
  - [ ] Test email/username parsing

- [ ] **USA Bank of America.zip**
  - [ ] Extract and analyze contents
  - [ ] Check if multiple statements
  - [ ] Test batch processing

### Template/Test Files
- [ ] **merged_statements_2025-07-26.pdf**
  - [ ] Check how merged PDFs are handled
  - [ ] Verify statement separation
  - [ ] Test date continuity

- [ ] **Bank-Statement-Template-4-TemplateLab.pdf**
  - [ ] Analyze template structure
  - [ ] Use as baseline for comparison

- [ ] **dummy_statement.pdf**
  - [ ] Check test data parsing
  - [ ] Verify all fields extract

- [ ] **Bank Statement Example Final.pdf**
  - [ ] Analyze example format
  - [ ] Check completeness

## Analysis Steps for Each PDF

### 1. Visual Inspection
- [ ] Open PDF manually
- [ ] Note table structure
- [ ] Identify all data sections
- [ ] Check for multiple accounts
- [ ] Note any special formatting

### 2. Run Current Parser
```bash
python test_universal_parser.py "/path/to/pdf"
```
- [ ] Check output CSV
- [ ] Compare with visual data
- [ ] Note missing transactions
- [ ] Note missing fields

### 3. Debug Specific Issues
- [ ] Missing transactions
  - [ ] Check date parsing
  - [ ] Check amount parsing
  - [ ] Check table detection
- [ ] Missing descriptions
  - [ ] Check column detection
  - [ ] Check text extraction
  - [ ] Check encoding issues
- [ ] Missing tables
  - [ ] Check page breaks
  - [ ] Check table headers
  - [ ] Check non-standard layouts

### 4. Document Findings
For each PDF, document:
- [ ] Bank name and format version
- [ ] Number of transactions in PDF
- [ ] Number of transactions extracted
- [ ] Missing data types
- [ ] Specific parsing errors
- [ ] Required parser improvements

## Common Issues to Check

### Date Formats
- [ ] MM/DD/YYYY (USA)
- [ ] DD/MM/YYYY (UK/AU)
- [ ] YYYY-MM-DD
- [ ] MMM DD, YYYY
- [ ] DD-MMM-YYYY

### Amount Formats
- [ ] $1,234.56
- [ ] 1,234.56 USD
- [ ] £1,234.56
- [ ] AUD 1,234.56
- [ ] (1,234.56) for negatives
- [ ] 1.234,56 (European)

### Table Structures
- [ ] Single column amounts
- [ ] Separate debit/credit columns
- [ ] Running balance column
- [ ] Transaction type indicators
- [ ] Reference numbers
- [ ] Check numbers

### Special Sections
- [ ] Pending transactions
- [ ] Interest calculations
- [ ] Fee summaries
- [ ] Account summary
- [ ] Previous balance

## Parser Improvements Needed

### 1. Multi-Format Support
- [ ] Create bank-specific parsers
- [ ] Improve format detection
- [ ] Handle format variations

### 2. Better Table Detection
- [ ] Improve column alignment detection
- [ ] Handle multi-line descriptions
- [ ] Better page break handling

### 3. Enhanced Data Extraction
- [ ] Improve date parsing flexibility
- [ ] Better amount extraction
- [ ] Handle special characters
- [ ] Extract additional fields

### 4. Error Handling
- [ ] Better error messages
- [ ] Partial extraction on errors
- [ ] Format mismatch warnings

## Testing Strategy

1. **Create Test Suite**
   - [ ] One test per bank format
   - [ ] Expected output for each
   - [ ] Automated comparison

2. **Performance Testing**
   - [ ] Time each PDF parsing
   - [ ] Memory usage monitoring
   - [ ] Multi-page efficiency

3. **Accuracy Metrics**
   - [ ] Transaction count accuracy
   - [ ] Amount sum validation
   - [ ] Description completeness
   - [ ] Date range verification

## Priority Order

1. **High Priority** (Major Banks)
   - USA Bank of America
   - USA Wells Fargo
   - Canada RBC
   - Australia Commonwealth

2. **Medium Priority** (Common Formats)
   - USA PNC
   - USA Citizens Bank
   - UK Nationwide
   - Australia Westpac

3. **Low Priority** (Special Cases)
   - PayPal statements
   - Credit union formats
   - Template files

## Next Steps

1. Start with high-priority PDFs
2. Document specific issues for each
3. Create bank-specific parser modules
4. Test improvements locally
5. Deploy once all major formats work

---

**Note**: Do not deploy to server until all major bank formats are parsing correctly with >95% accuracy.