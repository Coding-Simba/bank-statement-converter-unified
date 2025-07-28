#!/usr/bin/env python3
"""Debug Discover parser detailed"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

import pdfplumber

pdf_path = "/Users/MAC/Desktop/pdfs/1/USA Discover Bank.pdf"

print("=== Discover PDF Detailed Analysis ===")

# Check all pages for transaction patterns
with pdfplumber.open(pdf_path) as pdf:
    for page_num, page in enumerate(pdf.pages):
        print(f"\n=== Page {page_num + 1} ===")
        
        # Extract tables
        tables = page.extract_tables()
        if tables:
            print(f"Found {len(tables)} table(s)")
            for i, table in enumerate(tables):
                if i < 2:  # First 2 tables
                    print(f"\nTable {i+1} ({len(table)} rows):")
                    for j, row in enumerate(table[:10]):  # First 10 rows
                        print(f"Row {j}: {row}")
        
        # Look for transaction lines
        text = page.extract_text()
        if text:
            lines = text.split('\n')
            print("\nLines that might be transactions:")
            for line in lines:
                # Look for date patterns at start of line
                import re
                if re.match(r'^\s*(Sep|Oct|Nov|Dec|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug)\s+\d{1,2}', line):
                    print(f"  {line[:100]}")
                elif re.match(r'^\s*\d{1,2}/\d{1,2}', line):
                    print(f"  {line[:100]}")