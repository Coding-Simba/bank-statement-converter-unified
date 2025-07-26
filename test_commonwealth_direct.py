#!/usr/bin/env python3
"""Test Commonwealth parser directly"""

from backend.commonwealth_simple_parser import parse_commonwealth_simple as parse_commonwealth_bank

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

# Show first few of each type
if transactions:
    print("\nFirst 5 withdrawals:")
    withdrawals_shown = 0
    for trans in transactions:
        if trans.get('amount', 0) < 0 and withdrawals_shown < 5:
            print(f"{trans['date_string']} - {trans['description'][:50]}... ${trans['amount']:.2f}")
            withdrawals_shown += 1
    
    print("\nFirst 5 deposits:")
    deposits_shown = 0
    for trans in transactions:
        if trans.get('amount', 0) > 0 and deposits_shown < 5:
            print(f"{trans['date_string']} - {trans['description'][:50]}... ${trans['amount']:.2f}")
            deposits_shown += 1
    
    # Show all cash deposits
    print("\nAll CASH DEPOSIT transactions:")
    for trans in transactions:
        if 'CASH DEPOSIT' in trans['description']:
            print(f"{trans['date_string']} - {trans['description'][:50]}... ${trans['amount']:.2f} (amount_string: {trans.get('amount_string', 'N/A')})")