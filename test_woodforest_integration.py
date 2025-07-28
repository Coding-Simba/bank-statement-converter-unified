#!/usr/bin/env python3
"""Test Woodforest integration with universal parser"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from universal_parser_enhanced import parse_universal_pdf_enhanced, detect_bank

pdf_path = "/Users/MAC/Desktop/pdfs/1/USA Woodforest.pdf"

print("Testing Woodforest integration...")

# Test bank detection
detected = detect_bank(pdf_path)
print(f"\nDetected bank: {detected}")

# Test universal parser
print("\n=== Universal Parser Enhanced ===")
transactions = parse_universal_pdf_enhanced(pdf_path)
print(f"Transactions found: {len(transactions)}")

if transactions:
    print(f"\nFirst 5 transactions:")
    for i, trans in enumerate(transactions[:5]):
        print(f"{i+1}. {trans['date_string']} | {trans['description'][:50]}... | ${trans['amount']:.2f}")