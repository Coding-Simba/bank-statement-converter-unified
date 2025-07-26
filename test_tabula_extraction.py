#!/usr/bin/env python3
"""Test tabula extraction on the PDF"""

import tabula
import pandas as pd

pdf_path = "/Users/MAC/Downloads/merged_statements_2025-07-26.pdf"

print("Testing tabula extraction...")
print("-" * 60)

try:
    # Try different extraction methods
    methods = [
        {'lattice': True, 'pages': 'all'},
        {'stream': True, 'pages': 'all'}, 
        {'guess': True, 'pages': 'all'}
    ]
    
    for i, method in enumerate(methods):
        print(f"\nMethod {i+1}: {method}")
        print("-" * 40)
        
        try:
            tables = tabula.read_pdf(pdf_path, **method)
            print(f"Found {len(tables)} tables")
            
            for j, table in enumerate(tables[:2]):  # Show first 2 tables
                if isinstance(table, pd.DataFrame) and not table.empty:
                    print(f"\nTable {j+1} shape: {table.shape}")
                    print("Columns:", list(table.columns))
                    print("\nFirst 10 rows:")
                    print(table.head(10))
                    
                    # Check if any column might contain dates
                    for col in table.columns:
                        sample = table[col].astype(str).str.strip()
                        # Look for date patterns
                        date_matches = sample.str.match(r'^\d{1,2}[/-]\d{1,2}[/-]\d{2,4}$').sum()
                        if date_matches > 0:
                            print(f"\nColumn '{col}' might contain dates ({date_matches} found)")
                            
        except Exception as e:
            print(f"Error with method: {e}")
            
except Exception as e:
    print(f"General error: {e}")
    
# Also try with PDFPlumber
print("\n\nTrying PDFPlumber...")
print("-" * 60)

try:
    import pdfplumber
    
    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages[:2]):
            print(f"\nPage {i+1}:")
            
            # Extract tables
            tables = page.extract_tables()
            if tables:
                print(f"Found {len(tables)} tables")
                for j, table in enumerate(tables[:2]):
                    print(f"\nTable {j+1}:")
                    for row in table[:5]:  # First 5 rows
                        print(row)
            else:
                print("No tables found")
                
            # Try extracting text
            text = page.extract_text()
            if text:
                lines = text.split('\n')
                print(f"\nText preview (first 20 lines):")
                for line in lines[:20]:
                    if line.strip():
                        print(f"  {line}")
                        
except Exception as e:
    print(f"PDFPlumber error: {e}")