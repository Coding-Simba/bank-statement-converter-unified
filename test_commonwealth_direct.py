#!/usr/bin/env python3
"""Test Commonwealth parser directly"""

from backend.commonwealth_final_parser import parse_commonwealth_final as parse_commonwealth_bank

pdf_path = '/Users/MAC/Desktop/pdfs/1/Australia Commonwealth J C.pdf'

print("Testing Commonwealth Bank parser directly...")
print("=" * 60)

transactions = parse_commonwealth_bank(pdf_path)

print(f"\nTotal transactions: {len(transactions)}")

# Group by type  
deposits = [t for t in transactions if t.get('amount', 0) > 0]
withdrawals = [t for t in transactions if t.get('amount', 0) < 0]

print(f"Deposits: {len(deposits)}")
print(f"Withdrawals: {len(withdrawals)}")

# Show first few
if transactions:
    print("\nFirst 5 transactions:")
    for i, trans in enumerate(transactions[:5]):
        print(f"{i+1}. {trans['date_string']} - {trans['description'][:50]}... ${trans['amount']:.2f}")