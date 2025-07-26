#!/usr/bin/env python3
"""Test the updated universal parser with pdftotext support"""

import sys
sys.path.append('.')

from backend.universal_parser import parse_universal_pdf

pdf_path = "/Users/MAC/Downloads/merged_statements_2025-07-26.pdf"

print(f"Testing updated parser on: {pdf_path}")
print("-" * 60)

# Add debug to see raw transactions before deduplication
import json

transactions = parse_universal_pdf(pdf_path)

print(f"\nFound {len(transactions)} transactions after deduplication")

if transactions:
    print("\nFirst 10 transactions:")
    for i, trans in enumerate(transactions[:10]):
        print(f"\n{i+1}. Date: {trans.get('date')}")
        print(f"   Date string: {trans.get('date_string')}")
        print(f"   Description: {trans.get('description')}")
        print(f"   Amount: {trans.get('amount')}")
        print(f"   Amount string: {trans.get('amount_string')}")
else:
    print("\nNo transactions found!")