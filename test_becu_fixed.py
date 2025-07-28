#!/usr/bin/env python3
"""Test fixed BECU parser"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from parsers.becu_parser import BECUParser

pdf_path = "/Users/MAC/Desktop/pdfs/1/USA BECU statement 4 pages.pdf"

print("Testing fixed BECU parser...")
parser = BECUParser()
transactions = parser.parse(pdf_path)

print(f"\nTransactions found: {len(transactions)}")
print(f"First 10 transactions:")
for i, trans in enumerate(transactions[:10]):
    print(f"{i+1}. {trans['date_string']} | {trans['description'][:50]}... | ${trans['amount']:.2f}")