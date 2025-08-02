#!/usr/bin/env python3
"""Quick test for Huntington bank PDF"""

import sys
sys.path.append('backend')

# Try to import just what we need
try:
    import pdfplumber
    print("✓ pdfplumber imported successfully")
except ImportError as e:
    print(f"✗ pdfplumber import failed: {e}")

try:
    from universal_parser import parse_universal_pdf
    print("✓ universal_parser imported successfully")
    
    # Now test the actual parsing
    pdf_path = '/Users/MAC/Desktop/pdfs/1/USA Ohio Huntington bank statement 7  page.pdf'
    print(f"\nTesting: {pdf_path}")
    
    transactions = parse_universal_pdf(pdf_path)
    print(f"\n✓ Parsing completed - Found {len(transactions)} transactions")
    
    if transactions:
        print("\nFirst 5 transactions:")
        for i, trans in enumerate(transactions[:5]):
            date_str = trans.get('date', 'No date')
            if hasattr(date_str, 'strftime'):
                date_str = date_str.strftime('%Y-%m-%d')
            desc = trans.get('description', 'No description')[:50]
            amount = trans.get('amount', 'No amount')
            print(f"  {i+1}. {date_str} | {desc:<50} | {amount}")
    else:
        print("\n⚠️  No transactions found - checking PDF directly with pdfplumber...")
        
        with pdfplumber.open(pdf_path) as pdf:
            print(f"\nPDF has {len(pdf.pages)} pages")
            
            # Extract text from first page
            first_page = pdf.pages[0]
            text = first_page.extract_text()
            if text:
                print("\nFirst 500 chars of page 1:")
                print(text[:500])
                
                # Try to extract tables
                tables = first_page.extract_tables()
                if tables:
                    print(f"\nFound {len(tables)} tables on page 1")
                    print("First table preview:")
                    for row in tables[0][:5]:
                        print("  ", row)
                else:
                    print("\nNo tables found on page 1")
            else:
                print("\nNo text extracted from page 1")
                
except Exception as e:
    print(f"\n✗ Error: {e}")
    import traceback
    traceback.print_exc()