#!/usr/bin/env python3
"""Analyze PDF structure to understand transaction format"""

import PyPDF2
import pdfplumber

pdf_path = '/Users/MAC/Desktop/pdfs/Bank Statement Example Final.pdf'

print("=== ANALYZING PDF STRUCTURE ===")
print("=" * 60)

# First, get basic info
try:
    with open(pdf_path, 'rb') as file:
        pdf_reader = PyPDF2.PdfReader(file)
        print(f"Number of pages: {len(pdf_reader.pages)}")
        
        # Extract first page text
        first_page_text = pdf_reader.pages[0].extract_text()
        print("\nFirst 500 characters of page 1:")
        print("-" * 40)
        print(first_page_text[:500])
except Exception as e:
    print(f"PyPDF2 error: {e}")

# Now use pdfplumber for better table detection
print("\n\nUSING PDFPLUMBER FOR TABLES:")
print("=" * 60)

try:
    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages[:2]):  # First 2 pages
            print(f"\nPage {page_num + 1}:")
            
            # Extract tables
            tables = page.extract_tables()
            print(f"Found {len(tables)} tables")
            
            for i, table in enumerate(tables):
                if table and len(table) > 0:
                    print(f"\nTable {i+1} (first 5 rows):")
                    for row_num, row in enumerate(table[:5]):
                        print(f"  Row {row_num}: {row}")
                    
                    if len(table) > 5:
                        print(f"  ... and {len(table) - 5} more rows")
            
            # Also get raw text
            text = page.extract_text()
            if text:
                lines = text.split('\n')
                print(f"\nSample text lines from page {page_num + 1}:")
                # Find lines that might be transactions
                for line in lines[:30]:  # First 30 lines
                    if any(char.isdigit() for char in line) and len(line) > 20:
                        print(f"  > {line}")
                        
except Exception as e:
    print(f"pdfplumber error: {e}")
    import traceback
    traceback.print_exc()