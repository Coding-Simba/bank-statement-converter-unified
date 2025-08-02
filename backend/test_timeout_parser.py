#!/usr/bin/env python3
"""Test the timeout parser"""

import sys
import time
from universal_parser_timeout import parse_universal_pdf

if len(sys.argv) < 2:
    print("Usage: python test_timeout_parser.py <pdf_file>")
    sys.exit(1)

pdf_path = sys.argv[1]
print(f"Testing timeout parser with: {pdf_path}")

start_time = time.time()
try:
    transactions = parse_universal_pdf(pdf_path)
    elapsed = time.time() - start_time
    
    print(f"\nCompleted in {elapsed:.2f} seconds")
    print(f"Found {len(transactions)} transactions")
    
    if transactions:
        print("\nFirst 5 transactions:")
        for i, trans in enumerate(transactions[:5]):
            print(f"{i+1}. Date: {trans.get('date')}, "
                  f"Amount: {trans.get('amount')}, "
                  f"Description: {trans.get('description', 'N/A')[:50]}")
except Exception as e:
    elapsed = time.time() - start_time
    print(f"\nFailed after {elapsed:.2f} seconds")
    print(f"Error: {e}")