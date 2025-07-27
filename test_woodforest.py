#!/usr/bin/env python3
"""Test USA Woodforest statement"""

from backend.universal_parser import parse_universal_pdf

pdf_path = '/Users/MAC/Desktop/pdfs/1/USA Woodforest.pdf'

print("Testing USA Woodforest statement...")
print("=" * 60)

transactions = parse_universal_pdf(pdf_path)

print(f"\nTotal transactions: {len(transactions)}")

# Group by type  
deposits = [t for t in transactions if t.get('amount', 0) > 0]
withdrawals = [t for t in transactions if t.get('amount', 0) < 0]

print(f"Deposits: {len(deposits)}")
print(f"Withdrawals: {len(withdrawals)}")

# Show sample transactions
if transactions:
    print("\nFirst 5 transactions:")
    for trans in transactions[:5]:
        print(f"{trans.get('date_string', 'N/A')} - {trans.get('description', 'N/A')[:40]}... ${trans['amount']:.2f}")
        
    print("\nLast 5 transactions:")
    for trans in transactions[-5:]:
        print(f"{trans.get('date_string', 'N/A')} - {trans.get('description', 'N/A')[:40]}... ${trans['amount']:.2f}")