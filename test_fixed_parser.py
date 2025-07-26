#!/usr/bin/env python3
"""Test the fixed column parser on Bank Statement Example Final.pdf"""

from backend.fixed_column_parser import parse_fixed_column_layout
from backend.improved_fixed_parser import parse_bank_statement_with_columns
from backend.universal_parser import parse_universal_pdf

pdf_path = '/Users/MAC/Desktop/pdfs/Bank Statement Example Final.pdf'

print("=== TESTING FIXED COLUMN PARSER ===")
print("=" * 60)

# Test with fixed column parser directly
print("\n1. Testing with Fixed Column Parser:")
print("-" * 40)
transactions = parse_fixed_column_layout(pdf_path)

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

# Compare with expected totals from the statement
print("\n" + "=" * 40)
print("Expected from statement header:")
print("  Total money in: £5,474.00")
print("  Total money out: £1,395.17")

# Test with improved parser
print("\n\n2. Testing with Improved Fixed Parser:")
print("-" * 40)
transactions2 = parse_bank_statement_with_columns(pdf_path)

print(f"Total transactions: {len(transactions2)}")

# Group by type
deposits2 = [t for t in transactions2 if t.get('amount', 0) > 0]
withdrawals2 = [t for t in transactions2 if t.get('amount', 0) < 0]

print(f"\nDeposits: {len(deposits2)} transactions, Total: ${sum(t['amount'] for t in deposits2):,.2f}")
for i, trans in enumerate(deposits2):
    print(f"  {i+1}. {trans.get('date_string', 'N/A')} - {trans.get('description', 'N/A')}: ${trans.get('amount', 0):.2f}")

print(f"\nWithdrawals: {len(withdrawals2)} transactions, Total: ${sum(t['amount'] for t in withdrawals2):,.2f}")
for i, trans in enumerate(withdrawals2):
    print(f"  {i+1}. {trans.get('date_string', 'N/A')} - {trans.get('description', 'N/A')}: ${trans.get('amount', 0):.2f}")