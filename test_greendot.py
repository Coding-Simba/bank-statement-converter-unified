#!/usr/bin/env python3
"""Test Green Dot statement parser"""

from backend.greendot_parser import parse_greendot

pdf_path = '/Users/MAC/Desktop/pdfs/1/USA Green Dot Bank Statement 3 page.pdf'

print("Testing Green Dot statement...")
print("=" * 60)

transactions = parse_greendot(pdf_path)

print(f"\nTotal transactions: {len(transactions)}")

# Group by type  
deposits = [t for t in transactions if t.get('amount', 0) > 0]
withdrawals = [t for t in transactions if t.get('amount', 0) < 0]

print(f"Deposits: {len(deposits)}")
print(f"Withdrawals/Fees: {len(withdrawals)}")

# Show all transactions
if transactions:
    print("\nAll transactions:")
    for trans in transactions:
        print(f"{trans.get('date_string', 'N/A')} - {trans.get('description', 'N/A')} ({trans.get('type', 'N/A')}) ${trans['amount']:.2f}")