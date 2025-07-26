# Universal PDF Parser Implementation

## Overview
The bank statement converter now supports **any bank PDF format**, not just Rabobank. The universal parser uses multiple extraction methods to handle various bank statement formats from around the world.

## Features

### 1. Multi-Method Extraction
The parser tries multiple methods in order:
1. **Bank-specific parsers** (e.g., Rabobank)
2. **Tabula-py** - Extracts tables from PDFs (with/without borders)
3. **PDFPlumber** - Advanced text and table extraction
4. **PyPDF2 + Regex** - Fallback text extraction with pattern matching

### 2. Supported Date Formats
- US format: `MM/DD/YYYY`, `MM-DD-YYYY`
- European format: `DD/MM/YYYY`, `DD-MM-YYYY`
- ISO format: `YYYY-MM-DD`
- Month names: `Jan 15, 2024`, `15-Jan-2024`
- Short year: `MM/DD/YY`

### 3. Supported Amount Formats
- US format: `$1,234.56`, `($1,234.56)` for negatives
- European format: `€1.234,56`, `1.234,56 EUR`
- UK format: `£1,234.56 DR/CR`
- With/without currency symbols
- Parentheses for negative amounts
- DR/CR indicators

### 4. Bank Format Examples

#### US Banks (Chase, Bank of America, Wells Fargo)
```
01/15/2024    WALMART #1234           ($48.73)
01/16/2024    DIRECT DEPOSIT          $2,500.00
```

#### European Banks (ING, ABN AMRO, Rabobank)
```
15-01-2024    Supermarkt AH          €48,73 AF
16-01-2024    Salaris               €2.500,00 BIJ
```

#### UK Banks (HSBC, Barclays, Lloyds)
```
15 Jan 2024    Tesco Superstore      £48.73 DR
16 Jan 2024    Salary Payment        £2,500.00 CR
```

### 5. Screenshot PDF Support
The parser can handle screenshot PDFs through:
- **PDFPlumber** - Has OCR capabilities for image-based PDFs
- **Tabula** - Can extract tables from screenshot PDFs

## Implementation Details

### File Structure
```
backend/
├── universal_parser.py    # Main universal parsing logic
├── rabobank_parser.py    # Rabobank-specific parser
└── api/
    └── statements.py     # API endpoint using universal parser
```

### Key Functions

1. **`parse_universal_pdf(pdf_path)`**
   - Main entry point
   - Tries bank-specific parsers first
   - Falls back to generic extraction methods

2. **`extract_transactions_from_dataframe(df)`**
   - Processes pandas DataFrames from table extraction
   - Intelligent column detection for dates, descriptions, amounts

3. **`extract_transactions_from_text(text)`**
   - Regex-based extraction for unstructured text
   - Supports multiple date/amount formats

4. **`extract_amount(amount_str)`**
   - Handles various currency formats
   - Detects decimal separators (comma vs dot)
   - Handles negative amounts

## Testing

The universal parser has been tested with:
- ✅ Rabobank PDFs (Dutch format)
- ✅ Text-based extraction for various formats
- ✅ Table-based PDFs
- ✅ European number formats (1.234,56)
- ✅ US number formats (1,234.56)

## Usage

### Via Web Interface
1. Go to http://localhost:8080
2. Upload any bank statement PDF
3. Get CSV with parsed transactions

### Via API
```bash
curl -X POST http://localhost:5000/api/convert \
  -F "file=@bank_statement.pdf" \
  -o converted.csv
```

## Future Enhancements
1. Add more bank-specific parsers
2. Improve OCR for screenshot PDFs
3. Add support for multi-currency statements
4. Machine learning for format detection