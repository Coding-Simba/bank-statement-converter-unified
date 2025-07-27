#!/usr/bin/env python3
"""Test dummy PDF directly"""

from backend.universal_parser import parse_universal_pdf

pdf_path = '/Users/MAC/Desktop/pdfs/dummy_statement.pdf'

print("Testing dummy statement...")
print("=" * 60)

transactions = parse_universal_pdf(pdf_path)

print(f"\nTotal transactions: {len(transactions)}")

if transactions:
    for trans in transactions:
        print(f"{trans.get('date_string', 'N/A')} - {trans.get('description', 'N/A')[:40]}... ${trans['amount']:.2f}")
else:
    print("No transactions found")