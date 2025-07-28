#!/usr/bin/env python3
"""Debug BECU parser to understand extraction issues"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

import pdfplumber
from parsers.becu_parser import BECUParser

pdf_path = "/Users/MAC/Desktop/pdfs/1/USA BECU statement 4 pages.pdf"

print("=== BECU PDF Debug ===")
print(f"Analyzing: {pdf_path}")

# First, let's see what the PDF contains
with pdfplumber.open(pdf_path) as pdf:
    print(f"\nTotal pages: {len(pdf.pages)}")
    
    # Check first page
    print("\n--- First Page Text (first 1000 chars) ---")
    first_page = pdf.pages[0]
    text = first_page.extract_text()
    if text:
        print(text[:1000])
    
    # Check tables on first page
    print("\n--- Tables on First Page ---")
    tables = first_page.extract_tables()
    print(f"Number of tables: {len(tables)}")
    
    if tables:
        for i, table in enumerate(tables[:2]):  # First 2 tables
            print(f"\nTable {i+1} shape: {len(table)}x{len(table[0]) if table else 0}")
            if table and len(table) > 0:
                # Print first few rows
                for row in table[:5]:
                    print(f"  {row}")

# Now test the parser
print("\n=== Testing BECU Parser ===")
parser = BECUParser()
transactions = parser.extract_transactions(pdf_path)

print(f"\nTransactions found: {len(transactions)}")
if transactions:
    for i, trans in enumerate(transactions[:5]):
        print(f"\nTransaction {i+1}:")
        print(f"  Date: {trans.get('date_string', 'NO DATE')}")
        print(f"  Description: {trans.get('description', 'NO DESC')}")
        print(f"  Amount: ${trans.get('amount', 0):.2f}")

# Let's also check what the year detection finds
year = parser.detect_year_from_pdf(pdf_path)
print(f"\nDetected year: {year}")

# Check if we can find date patterns
print("\n--- Looking for date patterns ---")
with pdfplumber.open(pdf_path) as pdf:
    for page_num, page in enumerate(pdf.pages[:2]):
        text = page.extract_text()
        if text:
            lines = text.split('\n')
            for line in lines[:50]:  # First 50 lines
                # Look for MM/DD patterns
                import re
                if re.search(r'\d{1,2}/\d{1,2}', line):
                    print(f"Page {page_num + 1}: {line[:100]}")