#!/usr/bin/env python3
"""Test a single PDF to debug issues"""

from backend.universal_parser import parse_universal_pdf
import sys
import os

# Test second PDF - Australia Commonwealth
pdf_path = '/Users/MAC/Desktop/pdfs/1/Australia Commonwealth J C.pdf'

print(f"Testing: {os.path.basename(pdf_path)}")
print("=" * 60)

if not os.path.exists(pdf_path):
    print(f"ERROR: File not found - {pdf_path}")
    sys.exit(1)

try:
    transactions = parse_universal_pdf(pdf_path)
    
    print(f"\nTotal transactions: {len(transactions)}")
    
    # Group by type
    deposits = [t for t in transactions if t.get('amount', 0) > 0]
    withdrawals = [t for t in transactions if t.get('amount', 0) < 0]
    
    print(f"Deposits: {len(deposits)}")
    print(f"Withdrawals: {len(withdrawals)}")
    
    # Show first few transactions
    if transactions:
        print("\nFirst 5 transactions:")
        for i, trans in enumerate(transactions[:5]):
            print(f"{i+1}. Date: {trans.get('date_string', 'N/A')}")
            print(f"   Description: {trans.get('description', 'N/A')}")
            print(f"   Amount: ${trans.get('amount', 0):.2f}")
            print()
            
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()