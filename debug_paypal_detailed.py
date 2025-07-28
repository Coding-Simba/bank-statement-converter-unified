#!/usr/bin/env python3
"""Debug PayPal parser with detailed analysis"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

import pdfplumber
from parsers.paypal_parser import PaypalParser

pdf_path = "/Users/MAC/Desktop/pdfs/1/USA PayPal Account Statement.pdf"

print("=== PayPal PDF Detailed Analysis ===")

# Extract all text to understand format
with pdfplumber.open(pdf_path) as pdf:
    for page_num, page in enumerate(pdf.pages):
        print(f"\n=== Page {page_num + 1} ===")
        
        # Extract tables
        tables = page.extract_tables()
        if tables:
            print(f"Found {len(tables)} table(s)")
            for i, table in enumerate(tables):
                print(f"\nTable {i+1} ({len(table)} rows):")
                for j, row in enumerate(table[:10]):  # First 10 rows
                    print(f"Row {j}: {row}")
        
        # Extract raw text
        text = page.extract_text()
        lines = text.split('\n')
        
        print("\nText lines with transaction patterns:")
        for i, line in enumerate(lines):
            line = line.strip()
            # Look for lines that start with dates
            if line and (line[:2].isdigit() or line[:3] in ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']):
                print(f"Line {i}: {line}")

# Test the parser
print("\n=== Testing PayPal Parser ===")
parser = PaypalParser()
transactions = parser.parse(pdf_path)

print(f"\nTotal transactions: {len(transactions)}")
if transactions:
    print("\nFirst 5 transactions:")
    for i, trans in enumerate(transactions[:5]):
        print(f"{i+1}. {trans}")
else:
    # Try to extract transactions manually
    print("\nNo transactions found. Trying manual extraction...")
    
    # Test table parsing
    year = parser.detect_year_from_pdf(pdf_path)
    print(f"Detected year: {year}")
    
    tables = parser.extract_table_data(pdf_path)
    print(f"\nExtracted {len(tables)} table rows")
    
    if tables:
        print("\nFirst 10 table rows:")
        for i, row in enumerate(tables[:10]):
            print(f"{i}: {row}")