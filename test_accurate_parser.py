#!/usr/bin/env python3
"""Test the accurate column parser"""

from backend.accurate_column_parser import parse_accurate_columns

pdf_path = '/Users/MAC/Desktop/pdfs/Bank Statement Example Final.pdf'

print("=== TESTING ACCURATE COLUMN PARSER ===")
print("=" * 60)

transactions = parse_accurate_columns(pdf_path)

print(f"Total transactions: {len(transactions)}")

# Group by type
deposits = [t for t in transactions if t.get('amount', 0) > 0]
withdrawals = [t for t in transactions if t.get('amount', 0) < 0]

print(f"\nDeposits: {len(deposits)} transactions, Total: ${sum(t['amount'] for t in deposits):,.2f}")
for i, trans in enumerate(deposits):
    print(f"  {i+1}. {trans.get('date_string', 'N/A')} - {trans.get('description', 'N/A')}: ${trans.get('amount', 0):.2f}")

print(f"\nWithdrawals: {len(withdrawals)} transactions, Total: ${sum(t['amount'] for t in withdrawals):,.2f}")
for i, trans in enumerate(withdrawals):
    print(f"  {i+1}. {trans.get('date_string', 'N/A')} - {trans.get('description', 'N/A')}: ${trans.get('amount', 0):.2f}")

# Calculate totals
total_deposits = sum(t['amount'] for t in deposits)
total_withdrawals = sum(t['amount'] for t in withdrawals)

print("\n" + "=" * 40)
print("Actual totals:")
print(f"  Total deposits: ${total_deposits:,.2f}")
print(f"  Total withdrawals: ${total_withdrawals:,.2f}")
print("\nExpected from statement header:")
print("  Total money in: £5,474.00")
print("  Total money out: £1,395.17")
print("\nDifference:")
print(f"  Deposits: ${total_deposits - 5474:.2f}")
print(f"  Withdrawals: ${total_withdrawals + 1395.17:.2f}")