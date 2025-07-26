#!/usr/bin/env python3
"""Test the screenshot PDF"""

import sys
sys.path.append('.')

from backend.universal_parser import parse_universal_pdf
import logging

# Enable logging to see what's happening
logging.basicConfig(level=logging.INFO)

pdf_path = "/Users/MAC/Downloads/Shot-2024-09-14-at-19.24.43@2x.jpg.pdf"

print(f"Testing: {pdf_path}")
print("=" * 70)

try:
    transactions = parse_universal_pdf(pdf_path)
    
    print(f"\nTotal transactions found: {len(transactions)}")
    
    if transactions:
        for i, trans in enumerate(transactions[:10]):
            date_str = trans.get('date_string', trans.get('date', 'No date'))
            if hasattr(date_str, 'strftime'):
                date_str = date_str.strftime('%Y-%m-%d')
            desc = trans.get('description', 'No description')[:50]
            amount = trans.get('amount', 0.0)
            print(f"{i+1}. {str(date_str)[:10]:10} | {desc:50} | ${amount:>10.2f}")
    else:
        print("\nNo transactions found!")
        
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()