#!/usr/bin/env python3
"""Test PDF parsing to debug transaction count issue"""

import sys
from universal_parser import parse_universal_pdf

if len(sys.argv) < 2:
    print("Usage: python test_pdf_parsing.py <pdf_file>")
    sys.exit(1)

pdf_path = sys.argv[1]
print(f"\n=== Testing PDF: {pdf_path} ===\n")

try:
    transactions = parse_universal_pdf(pdf_path)
    print(f"\n=== FINAL RESULT ===")
    print(f"Total transactions: {len(transactions)}")
    
    if transactions:
        print("\nFirst 5 transactions:")
        for i, trans in enumerate(transactions[:5]):
            print(f"{i+1}. Date: {trans.get('date')}, Amount: {trans.get('amount')}, Desc: {trans.get('description', 'N/A')[:50]}")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()