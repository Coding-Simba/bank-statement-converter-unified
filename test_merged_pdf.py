#!/usr/bin/env python3
"""Test merged statements PDF with accurate parser"""

from backend.accurate_column_parser import parse_accurate_columns

pdf_path = '/Users/MAC/Desktop/pdfs/merged_statements_2025-07-26.pdf'

print("=== TESTING MERGED STATEMENTS PDF ===")
print("=" * 60)

transactions = parse_accurate_columns(pdf_path)

print(f"\nTotal transactions: {len(transactions)}")

# Group by type
deposits = [t for t in transactions if t.get('amount', 0) > 0]
withdrawals = [t for t in transactions if t.get('amount', 0) < 0]

print(f"\nDeposits: {len(deposits)} transactions")
if deposits:
    print(f"Total deposits: ${sum(t['amount'] for t in deposits):,.2f}")
    for i, trans in enumerate(deposits[:5]):
        print(f"  {i+1}. {trans.get('date_string', 'N/A')} - {trans.get('description', 'N/A')}: ${trans.get('amount', 0):.2f}")
    if len(deposits) > 5:
        print(f"  ... and {len(deposits) - 5} more")

print(f"\nWithdrawals: {len(withdrawals)} transactions")
if withdrawals:
    print(f"Total withdrawals: ${sum(t['amount'] for t in withdrawals):,.2f}")
    for i, trans in enumerate(withdrawals[:5]):
        print(f"  {i+1}. {trans.get('date_string', 'N/A')} - {trans.get('description', 'N/A')}: ${trans.get('amount', 0):.2f}")
    if len(withdrawals) > 5:
        print(f"  ... and {len(withdrawals) - 5} more")