#!/usr/bin/env python3
"""Analyze Commonwealth format"""

import pdfplumber
import re

pdf_path = "/Users/MAC/Desktop/pdfs/1/Australia Commonwealth J C.pdf"

print("=== Analyzing Commonwealth Format ===")

with pdfplumber.open(pdf_path) as pdf:
    # Check page 2 which has transactions
    page = pdf.pages[1]  # Page 2 (0-indexed)
    
    # Extract tables
    tables = page.extract_tables()
    print(f"\nFound {len(tables)} table(s) on page 2")
    
    if tables:
        table = tables[0]
        print(f"\nTable has {len(table)} rows")
        print("\nFirst 10 rows:")
        for i, row in enumerate(table[:10]):
            print(f"Row {i}: {row}")
    
    # Extract text
    text = page.extract_text()
    lines = text.split('\n')
    
    print("\n\nLines with date patterns:")
    for line in lines:
        # Look for DD MMM pattern
        if re.search(r'\d{1,2}\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)', line):
            print(f"  {line[:100]}")