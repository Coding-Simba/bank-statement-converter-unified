#!/usr/bin/env python3
"""Debug Discover parser"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

import pdfplumber
from parsers.discover_parser import DiscoverParser

pdf_path = "/Users/MAC/Desktop/pdfs/1/USA Discover Bank.pdf"

print("=== Discover PDF Debug ===")

# Check PDF content
with pdfplumber.open(pdf_path) as pdf:
    print(f"Total pages: {len(pdf.pages)}")
    
    for page_num in range(min(2, len(pdf.pages))):
        print(f"\n=== Page {page_num + 1} ===")
        text = pdf.pages[page_num].extract_text()
        lines = text.split('\n')[:30]
        
        print(f"First 30 lines:")
        for i, line in enumerate(lines):
            print(f"{i+1}: {line}")

# Test the parser
print("\n=== Testing Discover Parser ===")
parser = DiscoverParser()

# Check supported date formats
print(f"\nSupported date formats: {parser.supported_date_formats}")

# Test extraction
transactions = parser.parse(pdf_path)
print(f"\nTotal transactions: {len(transactions)}")

if transactions:
    print("\nAll transactions:")
    for i, trans in enumerate(transactions):
        print(f"{i+1}. {trans['date_string']} | {trans['description'][:50]} | ${trans['amount']:.2f}")
else:
    print("\nNo transactions found")