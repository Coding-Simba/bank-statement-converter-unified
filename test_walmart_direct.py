#!/usr/bin/env python3
"""Test Walmart Money Card parser directly"""

from backend.walmart_parser import parse_walmart

pdf_path = '/Users/MAC/Desktop/pdfs/1/Walmart Money Card Bank Statement 3 page.pdf'

print("Testing Walmart Money Card statement with dedicated parser...")
print("=" * 60)

transactions = parse_walmart(pdf_path)

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