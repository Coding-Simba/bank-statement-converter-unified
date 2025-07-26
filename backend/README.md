# Bank Statement Split by Date Backend

This backend service provides functionality to split PDF bank statements based on transaction dates and export filtered transactions as CSV files.

## Features

- **PDF Parsing**: Extracts transactions from PDF bank statements using multiple methods (tabula-py and PyPDF2)
- **Date Range Filtering**: Filter transactions by custom date ranges or preset periods
- **Multiple Date Formats**: Supports various date formats commonly used in bank statements
- **CSV Export**: Exports filtered transactions in a clean CSV format
- **Preset Date Ranges**: Quick selection for common periods (last month, quarter, year, etc.)

## Setup

1. **Install Python dependencies**:
```bash
pip install -r requirements.txt
```

2. **Install Java** (required for tabula-py):
- tabula-py requires Java 8+ to be installed
- Download from: https://www.java.com/download/

3. **Run the Flask server**:
```bash
python split-by-date.py
```

The server will start on `http://localhost:5000`

## API Endpoints

### POST `/api/split-statement`

Splits a PDF bank statement by date range and returns a CSV file.

**Request:**
- Method: `POST`
- Content-Type: `multipart/form-data`
- Parameters:
  - `file`: PDF file (required)
  - `preset`: Date range preset (optional) - Options: `last_month`, `last_quarter`, `last_3_months`, `last_6_months`, `year_to_date`, `last_year`
  - `start_date`: Custom start date in YYYY-MM-DD format (required if preset not provided)
  - `end_date`: Custom end date in YYYY-MM-DD format (required if preset not provided)

**Response:**
- Success: CSV file download with filtered transactions
- Error: JSON with error message

### POST `/api/test-extraction`

Test endpoint to check PDF extraction without filtering.

**Request:**
- Method: `POST`
- Content-Type: `multipart/form-data`
- Parameters:
  - `file`: PDF file (required)

**Response:**
- JSON with extraction results including total transactions and date range

## Transaction Extraction

The backend uses multiple methods to extract transactions:

1. **Tabula-py**: Attempts to extract data from tables in the PDF
2. **PyPDF2**: Falls back to text extraction with regex patterns

Supported transaction patterns:
- `MM/DD/YYYY Description Amount`
- `DD-MMM-YYYY Description Amount`
- Various date formats with reference numbers

## Date Formats Supported

- MM/DD/YYYY
- MM-DD-YYYY
- YYYY-MM-DD
- DD/MM/YYYY
- DD-MM-YYYY
- MMM DD, YYYY
- MMMM DD, YYYY
- MM/DD/YY
- DD-MMM-YYYY

## Error Handling

The API returns appropriate error messages for:
- Invalid file types
- Missing required parameters
- Invalid date formats
- No transactions found
- PDF parsing errors

## Security Considerations

- File size limit: 50MB
- Only PDF files are accepted
- Uploaded files are temporarily stored and deleted after processing
- CORS is enabled for local development

## Troubleshooting

1. **"No transactions found"**: 
   - Ensure the PDF contains transaction data
   - Check if the PDF is text-based (not scanned image)
   - Try the test extraction endpoint to debug

2. **Java not found error**:
   - Install Java 8 or higher
   - Ensure Java is in your system PATH

3. **Date parsing errors**:
   - Check if transaction dates match supported formats
   - Ensure date range is valid (start date before end date)