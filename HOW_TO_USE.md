# How to Use the Bank Statement Converter

## Current Status
✅ Backend server is running on port 5000  
✅ Frontend server is running on port 8080  
✅ Universal PDF parser is implemented and working  
✅ Frontend is now connected to the backend API

## To Use the System:

### 1. Access the Website
Go to: http://localhost:8080

### 2. Upload a Bank Statement
- Click "CHOOSE FILES" or drag and drop a PDF
- Supports ANY bank format (not just Rabobank)
- Supports screenshot PDFs

### 3. Download the Converted File
- Click "Download CSV" to get the converted file
- The file will contain real parsed data from your PDF

## Testing the Connection
Open: http://localhost:8080/test-backend-connection.html

This will show you:
- Backend health status
- Upload functionality test
- API connection status

## What Was Fixed:

1. **Frontend Connection**: Updated `modern-homepage-fixed.js` to connect to the backend API instead of using hardcoded sample data

2. **Universal Parser**: Implemented a universal PDF parser that supports:
   - US bank formats (Chase, Bank of America, etc.)
   - European bank formats (Rabobank, ING, etc.)
   - UK bank formats (HSBC, Barclays, etc.)
   - Screenshot PDFs
   - Various date and number formats

3. **API Integration**: The frontend now:
   - Uploads files to `http://localhost:5000/api/convert`
   - Stores the statement ID
   - Downloads from `http://localhost:5000/api/statement/{id}/download`

## Important Notes:

- Clear your browser cache or do a hard refresh (Ctrl+Shift+R or Cmd+Shift+R) to ensure you get the updated JavaScript
- The backend must be running for conversions to work
- If the backend is not available, it will fall back to demo data

## Troubleshooting:

If you still get sample data:
1. Make sure both servers are running
2. Clear browser cache (hard refresh)
3. Check browser console for errors
4. Try the test page at `/test-backend-connection.html`

The system should now work with ANY bank PDF, not just Rabobank!