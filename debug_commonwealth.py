#!/usr/bin/env python3
"""Debug Commonwealth parser"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

import pdfplumber
from parsers.commonwealth_parser import CommonwealthParser

pdf_path = "/Users/MAC/Desktop/pdfs/1/Australia Commonwealth J C.pdf"

print("=== Commonwealth PDF Debug ===")

# Check PDF content
with pdfplumber.open(pdf_path) as pdf:
    print(f"Total pages: {len(pdf.pages)}")
    
    # Check first few pages
    for page_num in range(min(3, len(pdf.pages))):
        text = pdf.pages[page_num].extract_text()
        lines = text.split('\n')[:20]
        
        print(f"\n=== Page {page_num + 1} - First 20 lines ===")
        for i, line in enumerate(lines):
            print(f"{i+1}: {line}")

# Test the parser
print("\n=== Testing Commonwealth Parser ===")
parser = CommonwealthParser()

# Check supported date formats
print(f"\nSupported date formats: {parser.supported_date_formats}")

# Test extraction
transactions = parser.parse(pdf_path)
print(f"\nTotal transactions from custom parser: {len(transactions)}")

if transactions:
    print("\nFirst 5 transactions:")
    for i, trans in enumerate(transactions[:5]):
        print(f"{i+1}. {trans['date_string']} | {trans['description'][:50]} | ${trans['amount']:.2f}")
else:
    print("\nNo transactions found by custom parser")