#!/usr/bin/env python3
"""Debug PDF extraction to understand why only 1 transaction is found"""

from backend.universal_parser import parse_universal_pdf
import PyPDF2
import pdfplumber

pdf_path = './test_example.pdf'

print("=== DEBUGGING PDF EXTRACTION ===")
print(f"PDF: {pdf_path}")
print("=" * 60)

# First, let's see what PyPDF2 extracts
print("\n1. PyPDF2 Text Extraction:")
print("-" * 40)
try:
    with open(pdf_path, 'rb') as file:
        pdf_reader = PyPDF2.PdfReader(file)
        print(f"Number of pages: {len(pdf_reader.pages)}")
        
        for i, page in enumerate(pdf_reader.pages):
            print(f"\n--- Page {i+1} ---")
            text = page.extract_text()
            print(text[:500] + "..." if len(text) > 500 else text)
except Exception as e:
    print(f"PyPDF2 Error: {e}")

# Let's see what pdfplumber extracts
print("\n\n2. PDFPlumber Table Extraction:")
print("-" * 40)
try:
    with pdfplumber.open(pdf_path) as pdf:
        print(f"Number of pages: {len(pdf.pages)}")
        
        for i, page in enumerate(pdf.pages):
            print(f"\n--- Page {i+1} ---")
            tables = page.extract_tables()
            print(f"Number of tables found: {len(tables)}")
            
            for j, table in enumerate(tables):
                print(f"\nTable {j+1}:")
                if table and len(table) > 0:
                    print(f"Rows: {len(table)}, Columns: {len(table[0]) if table[0] else 0}")
                    # Show first 5 rows
                    for row_idx, row in enumerate(table[:5]):
                        print(f"Row {row_idx}: {row}")
except Exception as e:
    print(f"pdfplumber Error: {e}")

# Now run our parser with debug enabled
print("\n\n3. Our Parser Output:")
print("-" * 40)
try:
    import os
    os.environ['CAMELOT_DEBUG'] = '1'  # Enable debug
    transactions = parse_universal_pdf(pdf_path)
    print(f"\nTotal transactions extracted: {len(transactions)}")
    
    for i, trans in enumerate(transactions):
        print(f"\nTransaction {i+1}:")
        print(f"  Date: {trans.get('date_string', 'N/A')}")
        print(f"  Description: {trans.get('description', 'N/A')}")
        print(f"  Amount: ${trans.get('amount', 0):.2f}")
        
except Exception as e:
    print(f"Parser Error: {e}")
    import traceback
    traceback.print_exc()

# Check what tabula extracts
print("\n\n4. Tabula Extraction:")
print("-" * 40)
try:
    import tabula
    tables = tabula.read_pdf(pdf_path, pages='all', multiple_tables=True, silent=False)
    print(f"Number of tables found by tabula: {len(tables)}")
    
    for i, table in enumerate(tables):
        print(f"\nTable {i+1}:")
        print(f"Shape: {table.shape}")
        print("First 5 rows:")
        print(table.head())
        
except Exception as e:
    print(f"Tabula Error: {e}")
    import traceback
    traceback.print_exc()