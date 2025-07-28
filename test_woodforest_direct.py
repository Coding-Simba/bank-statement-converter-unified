#\!/usr/bin/env python3
"""Test Woodforest parser directly"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from woodforest_parser_enhanced import parse_woodforest
from woodforest_parser import parse_woodforest as parse_woodforest_old

pdf_path = "/Users/MAC/Desktop/pdfs/1/USA Woodforest.pdf"

print("Testing Woodforest parsers...")

# Test old parser
print("\n=== Old Woodforest Parser ===")
trans_old = parse_woodforest_old(pdf_path)
print(f"Transactions found: {len(trans_old)}")

# Test enhanced parser
print("\n=== Enhanced Woodforest Parser ===")
trans_new = parse_woodforest(pdf_path)
print(f"Transactions found: {len(trans_new)}")

if trans_new:
    print(f"\nFirst 5 transactions:")
    for i, trans in enumerate(trans_new[:5]):
        print(f"{i+1}. {trans['date_string']} | {trans['description'][:50]}... | ${trans['amount']:.2f}")

# Let's check the PDF content
import pdfplumber
print("\n=== PDF Content Check ===")
with pdfplumber.open(pdf_path) as pdf:
    print(f"Total pages: {len(pdf.pages)}")
    # Check first page
    text = pdf.pages[0].extract_text()
    if text:
        lines = text.split('\n')
        print("\nLooking for transaction patterns:")
        import re
        for line in lines[:50]:
            if re.search(r'\d{2}-\d{2}', line):
                print(f"  {line[:100]}")
