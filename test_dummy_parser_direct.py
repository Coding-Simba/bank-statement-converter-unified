#!/usr/bin/env python3
"""Test dummy PDF parser directly"""

import sys
sys.path.append('.')

from backend.dummy_pdf_parser import parse_dummy_pdf

pdf_path = "/Users/MAC/Downloads/dummy_statement.pdf"

print(f"Testing dummy PDF parser on: {pdf_path}")
print("=" * 70)

try:
    transactions = parse_dummy_pdf(pdf_path)
    
    print(f"\nTotal transactions found: {len(transactions)}")
    
    if transactions:
        # Show all transactions
        for i, trans in enumerate(transactions):
            date_str = trans.get('date_string', 'No date')
            desc = trans.get('description', 'No description')[:50]
            amount = trans.get('amount', 0.0)
            print(f"{i+1:2d}. {date_str:8} | {desc:50} | ${amount:>10.2f}")
        
        # Summary
        total_credits = sum(t['amount'] for t in transactions if t['amount'] > 0)
        total_debits = sum(t['amount'] for t in transactions if t['amount'] < 0)
        
        print(f"\n--- Summary ---")
        print(f"Total credits: ${total_credits:,.2f}")
        print(f"Total debits: ${total_debits:,.2f}")
        print(f"Net: ${total_credits + total_debits:,.2f}")
        
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()