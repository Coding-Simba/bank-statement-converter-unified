#!/usr/bin/env python3
"""Test Monzo bank statement parser"""

from backend.monzo_parser import parse_monzo

pdf_path = '/Users/MAC/Desktop/pdfs/1/Monzo Bank st. word.pdf'

print("Testing Monzo bank statement...")
print("=" * 60)

transactions = parse_monzo(pdf_path)

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
            print(f"{trans.get('date_string', 'N/A')} - {trans.get('description', 'N/A')[:50]}... ${trans['amount']:.2f}")
            withdrawals_shown += 1
    
    print("\nFirst 5 deposits:")
    deposits_shown = 0
    for trans in transactions:
        if trans.get('amount', 0) > 0 and deposits_shown < 5:
            print(f"{trans.get('date_string', 'N/A')} - {trans.get('description', 'N/A')[:50]}... ${trans['amount']:.2f}")
            deposits_shown += 1