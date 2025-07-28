#!/usr/bin/env python3
"""Test PayPal parser final version"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from parsers.paypal_parser import PaypalParser

pdf_path = "/Users/MAC/Desktop/pdfs/1/USA PayPal Account Statement.pdf"

print("=== Testing PayPal Parser ===")
parser = PaypalParser()
transactions = parser.parse(pdf_path)

print(f"\nTotal transactions: {len(transactions)}")

if transactions:
    print("\nAll transactions:")
    for i, trans in enumerate(transactions):
        print(f"{i+1}. Date: {trans['date_string']}, Amount: ${trans['amount']:.2f}, Desc: {trans['description'][:50]}")