#!/usr/bin/env python3
"""Test SunTrust statement parser"""

from backend.suntrust_parser import parse_suntrust

pdf_path = '/Users/MAC/Desktop/pdfs/1/USA Suntrust.pdf'

print("Testing SunTrust statement...")
print("=" * 60)

transactions = parse_suntrust(pdf_path)

print(f"\nTotal transactions: {len(transactions)}")

# Group by type  
credits = [t for t in transactions if t.get('amount', 0) > 0]
charges = [t for t in transactions if t.get('amount', 0) < 0]

print(f"Credits/Payments: {len(credits)}")
print(f"Charges: {len(charges)}")

# Show all transactions
if transactions:
    print("\nAll transactions:")
    for trans in transactions:
        print(f"{trans.get('date_string', 'N/A')} - {trans.get('description', 'N/A')[:40]}... ${trans['amount']:.2f}")