#!/usr/bin/env python3
"""Test the improved bank parser"""

from backend.improved_bank_parser import parse_improved_bank_pdf
import os

# Test PDFs
test_pdfs = [
    './failed_pdfs/20250727_005210_a17b26f9_Bank Statement Example Final.pdf',
    './uploads/11a56e83-e80a-4725-adf3-e33f19ee8f36.pdf',
]

for pdf_path in test_pdfs:
    print(f"\n{'='*60}")
    print(f"Testing: {pdf_path}")
    print('='*60)
    
    if not os.path.exists(pdf_path):
        print(f"File not found: {pdf_path}")
        continue
    
    transactions = parse_improved_bank_pdf(pdf_path)
    
    print(f"\nTotal transactions: {len(transactions)}")
    
    # Analyze results
    deposits = [t for t in transactions if t.get('amount', 0) > 0]
    withdrawals = [t for t in transactions if t.get('amount', 0) < 0]
    
    print(f"Deposits: {len(deposits)}")
    print(f"Withdrawals: {len(withdrawals)}")
    
    # Show first few transactions
    print("\nFirst 5 transactions:")
    for i, trans in enumerate(transactions[:5]):
        print(f"\n{i+1}. {trans.get('date_string', 'No date')}")
        print(f"   Description: {trans.get('description')}")
        print(f"   Amount: ${trans.get('amount', 0):.2f}")
        print(f"   Balance: ${trans.get('balance', 0):.2f}")
    
    # Summary
    if transactions:
        total_deposits = sum(t['amount'] for t in deposits)
        total_withdrawals = sum(t['amount'] for t in withdrawals)
        print(f"\nSummary:")
        print(f"  Total deposits: ${total_deposits:.2f}")
        print(f"  Total withdrawals: ${total_withdrawals:.2f}")
        print(f"  Net change: ${total_deposits + total_withdrawals:.2f}")