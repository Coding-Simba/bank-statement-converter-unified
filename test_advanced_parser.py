#!/usr/bin/env python3
"""Test the advanced OCR parser integration with dummy PDF"""

import sys
sys.path.append('.')

from backend.universal_parser import parse_universal_pdf
import logging

# Enable logging to see what parsers are being used
logging.basicConfig(level=logging.INFO)

pdf_path = "/Users/MAC/Downloads/dummy_statement.pdf"

print(f"Testing advanced parser integration on: {pdf_path}")
print("=" * 70)

try:
    # Parse the PDF using the universal parser
    transactions = parse_universal_pdf(pdf_path)
    
    print(f"\nTotal transactions found: {len(transactions)}")
    
    if transactions:
        # Group by whether they have dates
        with_dates = [t for t in transactions if t.get('date')]
        without_dates = [t for t in transactions if not t.get('date')]
        
        print(f"Transactions with dates: {len(with_dates)}")
        print(f"Transactions without dates: {len(without_dates)}")
        
        # Show first 10 transactions with dates
        if with_dates:
            print(f"\n--- Transactions with dates (first 10) ---")
            for i, trans in enumerate(with_dates[:10]):
                date_str = trans.get('date_string', 'No date string')
                desc = trans.get('description', 'No description')[:50]
                amount = trans.get('amount', 0.0)
                print(f"{i+1:2d}. {date_str:8} | {desc:50} | ${amount:>10.2f}")
        
        # Show first 5 transactions without dates
        if without_dates:
            print(f"\n--- Transactions without dates (first 5) ---")
            for i, trans in enumerate(without_dates[:5]):
                desc = trans.get('description', 'No description')[:50]
                amount = trans.get('amount', 0.0)
                print(f"{i+1:2d}. {'No date':8} | {desc:50} | ${amount:>10.2f}")
        
        # Summary
        total_credits = sum(t['amount'] for t in transactions if t['amount'] > 0)
        total_debits = sum(t['amount'] for t in transactions if t['amount'] < 0)
        
        print(f"\n--- Summary ---")
        print(f"Total credits: ${total_credits:,.2f}")
        print(f"Total debits: ${total_debits:,.2f}")
        print(f"Net: ${total_credits + total_debits:,.2f}")
        
    else:
        print("\nNo transactions found!")
        
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()