#!/usr/bin/env python3
"""Test all PDFs with the fixed universal parser"""

from backend.universal_parser import parse_universal_pdf
import os

# Test PDFs
test_pdfs = [
    ('./uploads/11a56e83-e80a-4725-adf3-e33f19ee8f36.pdf', 'merged_statements_2025-07-26.pdf'),
    ('./failed_pdfs/20250727_005204_0c55e666_Bank-Statement-Template-4-TemplateLab.pdf', 'Bank-Statement-Template-4-TemplateLab.pdf'),
    ('./uploads/ce491615-a3b4-444e-a079-4dfdb82819bd.pdf', 'dummy_statement.pdf'),
    ('./failed_pdfs/20250727_005210_a17b26f9_Bank Statement Example Final.pdf', 'Bank Statement Example Final.pdf'),
]

for pdf_path, name in test_pdfs:
    print(f"\n{'='*60}")
    print(f"Testing: {name}")
    print('='*60)
    
    if not os.path.exists(pdf_path):
        print(f"File not found: {pdf_path}")
        continue
    
    try:
        transactions = parse_universal_pdf(pdf_path)
        
        print(f"\nTotal transactions: {len(transactions)}")
        
        # Analyze results
        deposits = [t for t in transactions if t.get('amount', 0) > 0]
        withdrawals = [t for t in transactions if t.get('amount', 0) < 0]
        
        print(f"Deposits: {len(deposits)}")
        print(f"Withdrawals: {len(withdrawals)}")
        
        if transactions:
            total_deposits = sum(t['amount'] for t in deposits)
            total_withdrawals = sum(t['amount'] for t in withdrawals)
            print(f"\nSummary:")
            print(f"  Total deposits: ${total_deposits:.2f}")
            print(f"  Total withdrawals: ${total_withdrawals:.2f}")
            print(f"  Net change: ${total_deposits + total_withdrawals:.2f}")
            
            # Show first few transactions
            print("\nSample transactions:")
            for i, trans in enumerate(transactions[:3]):
                print(f"  {i+1}. {trans.get('date_string', 'N/A')} - {trans.get('description', 'N/A')}: ${trans.get('amount', 0):.2f}")
                
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()