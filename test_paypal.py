#!/usr/bin/env python3
"""Test PayPal statement parser"""

from backend.paypal_parser import parse_paypal

pdf_path = '/Users/MAC/Desktop/pdfs/1/USA PayPal Account Statement.pdf'

print("Testing PayPal statement...")
print("=" * 60)

transactions = parse_paypal(pdf_path)

print(f"\nTotal transactions: {len(transactions)}")

# Group by type  
deposits = [t for t in transactions if t.get('amount', 0) > 0]
transfers_out = [t for t in transactions if t.get('amount', 0) < 0]

print(f"Deposits: {len(deposits)}")
print(f"Transfers out: {len(transfers_out)}")

# Show all transactions
if transactions:
    print("\nAll transactions:")
    for trans in transactions:
        fees = trans.get('fees', 0)
        gross = trans.get('gross_amount', 0)
        print(f"{trans.get('date_string', 'N/A')} - {trans.get('description', 'N/A')[:40]}... | Gross: ${gross:.2f} | Fees: ${fees:.2f} | Total: ${trans['amount']:.2f}")