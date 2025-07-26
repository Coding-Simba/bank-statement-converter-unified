#!/usr/bin/env python3
"""Test PDF parser with user's actual file"""

from backend.universal_parser import parse_universal_pdf
import os

# User's PDF path
pdf_path = '/Users/MAC/Desktop/pdfs/example_bank_statement.pdf'

print("=== TESTING USER'S PDF ===")
print(f"PDF: {pdf_path}")
print("=" * 60)

if not os.path.exists(pdf_path):
    print(f"ERROR: PDF file not found at {pdf_path}")
    print("Testing with local copy instead...")
    pdf_path = './test_example.pdf'

try:
    transactions = parse_universal_pdf(pdf_path)
    
    print(f"\nTotal transactions extracted: {len(transactions)}")
    
    # Group by type
    deposits = [t for t in transactions if t.get('amount', 0) > 0]
    withdrawals = [t for t in transactions if t.get('amount', 0) < 0]
    
    print(f"\nDeposits: {len(deposits)} transactions, Total: ${sum(t['amount'] for t in deposits):.2f}")
    for i, trans in enumerate(deposits[:5]):  # Show first 5
        print(f"  {i+1}. {trans.get('date_string', 'N/A')} - {trans.get('description', 'N/A')}: ${trans.get('amount', 0):.2f}")
    if len(deposits) > 5:
        print(f"  ... and {len(deposits) - 5} more")
    
    print(f"\nWithdrawals: {len(withdrawals)} transactions, Total: ${sum(t['amount'] for t in withdrawals):.2f}")
    for i, trans in enumerate(withdrawals[:5]):  # Show first 5
        print(f"  {i+1}. {trans.get('date_string', 'N/A')} - {trans.get('description', 'N/A')}: ${trans.get('amount', 0):.2f}")
    if len(withdrawals) > 5:
        print(f"  ... and {len(withdrawals) - 5} more")
        
    # Show balance
    total_deposits = sum(t['amount'] for t in deposits)
    total_withdrawals = sum(t['amount'] for t in withdrawals)
    net = total_deposits + total_withdrawals
    
    print(f"\n" + "=" * 40)
    print(f"Summary:")
    print(f"  Total Deposits:     ${total_deposits:,.2f}")
    print(f"  Total Withdrawals:  ${total_withdrawals:,.2f}")
    print(f"  Net:                ${net:,.2f}")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()