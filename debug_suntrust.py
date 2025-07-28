#!/usr/bin/env python3
"""Debug SunTrust parser"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

import pdfplumber
from parsers.suntrust_parser import SuntrustParser

pdf_path = "/Users/MAC/Desktop/pdfs/1/USA Suntrust.pdf"

print("=== SunTrust PDF Debug ===")

# Check PDF content
with pdfplumber.open(pdf_path) as pdf:
    text = pdf.pages[0].extract_text()
    lines = text.split('\n')[:30]
    
    print("First 30 lines:")
    for i, line in enumerate(lines):
        print(f"{i+1}: {line}")

# Test the parser
print("\n=== Testing SunTrust Parser ===")
parser = SuntrustParser()

# Check supported date formats
print(f"\nSupported date formats: {parser.supported_date_formats}")

# Test extraction
transactions = parser.parse(pdf_path)
print(f"\nTotal transactions: {len(transactions)}")

if transactions:
    print("\nFirst 5 transactions:")
    for i, trans in enumerate(transactions[:5]):
        print(f"{i+1}. {trans}")
else:
    print("\nNo transactions found by custom parser")
    
    # Try manual extraction
    year = parser.detect_year_from_pdf(pdf_path)
    print(f"\nDetected year: {year}")
    
    # Test table extraction
    tables = parser.extract_table_data(pdf_path)
    print(f"\nExtracted {len(tables)} table rows")
    if tables:
        print("\nFirst 10 table rows:")
        for i, row in enumerate(tables[:10]):
            print(f"{i}: {row}")