#!/usr/bin/env python3
"""Test Woodforest parser directly"""

from backend.woodforest_parser import parse_woodforest

pdf_path = '/Users/MAC/Desktop/pdfs/1/USA Woodforest.pdf'

print("Testing Woodforest statement with dedicated parser...")
print("=" * 60)

transactions = parse_woodforest(pdf_path)

print(f"\nTotal transactions: {len(transactions)}")

# Group by type  
credits = [t for t in transactions if t.get('amount', 0) > 0]
debits = [t for t in transactions if t.get('amount', 0) < 0]

print(f"Credits/Deposits: {len(credits)}")
print(f"Debits/Withdrawals: {len(debits)}")

# Show all transactions
if transactions:
    print("\nAll transactions:")
    for trans in transactions:
        print(f"{trans.get('date_string', 'N/A')} - {trans.get('description', 'N/A')[:50]}... ${trans['amount']:.2f}")