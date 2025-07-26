#!/usr/bin/env python3
"""Final test of PDF parsing functionality"""

import sys
sys.path.append('.')

from backend.universal_parser import parse_universal_pdf
import json

pdf_path = "/Users/MAC/Downloads/merged_statements_2025-07-26.pdf"

print(f"Testing PDF parsing on: {pdf_path}")
print("-" * 60)

transactions = parse_universal_pdf(pdf_path)

print(f"\nSuccessfully extracted {len(transactions)} transactions!")

if transactions:
    print("\nSample transactions:")
    print("-" * 60)
    
    # Show first 5 and last 5
    for i, trans in enumerate(transactions[:5]):
        print(f"\n{i+1}. {trans.get('description', 'No description')}")
        print(f"   Amount: ${trans.get('amount', 0):.2f}")
        if trans.get('date'):
            print(f"   Date: {trans['date'].strftime('%Y-%m-%d')}")
    
    if len(transactions) > 10:
        print("\n...")
        for i, trans in enumerate(transactions[-5:], len(transactions)-4):
            print(f"\n{i}. {trans.get('description', 'No description')}")
            print(f"   Amount: ${trans.get('amount', 0):.2f}")
            if trans.get('date'):
                print(f"   Date: {trans['date'].strftime('%Y-%m-%d')}")
    
    # Summary
    total_amount = sum(t.get('amount', 0) for t in transactions)
    print(f"\n\nSummary:")
    print(f"Total transactions: {len(transactions)}")
    print(f"Total amount: ${abs(total_amount):,.2f}")
    print(f"Transactions with dates: {sum(1 for t in transactions if t.get('date'))}")
    print(f"Transactions without dates: {sum(1 for t in transactions if not t.get('date'))}")
else:
    print("\nNo transactions found!")