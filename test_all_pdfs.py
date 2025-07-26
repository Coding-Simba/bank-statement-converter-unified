#!/usr/bin/env python3
"""Test all user PDFs and verify transaction extraction"""

from backend.universal_parser import parse_universal_pdf
import os

# List of PDFs to test
pdf_files = [
    '/Users/MAC/Desktop/pdfs/merged_statements_2025-07-26.pdf',
    '/Users/MAC/Desktop/pdfs/Bank-Statement-Template-4-TemplateLab.pdf',
    '/Users/MAC/Desktop/pdfs/dummy_statement.pdf',
    '/Users/MAC/Desktop/pdfs/Bank Statement Example Final.pdf'
]

print("=== TESTING ALL USER PDFs ===")
print("=" * 80)

all_results = {}

for pdf_path in pdf_files:
    print(f"\n\nTesting: {os.path.basename(pdf_path)}")
    print("-" * 60)
    
    if not os.path.exists(pdf_path):
        print(f"ERROR: PDF file not found at {pdf_path}")
        continue
    
    try:
        transactions = parse_universal_pdf(pdf_path)
        
        print(f"\nTotal transactions extracted: {len(transactions)}")
        
        # Group by type
        deposits = [t for t in transactions if t.get('amount', 0) > 0]
        withdrawals = [t for t in transactions if t.get('amount', 0) < 0]
        
        print(f"\nDeposits: {len(deposits)} transactions")
        if deposits:
            total_deposits = sum(t['amount'] for t in deposits)
            print(f"Total deposits: ${total_deposits:,.2f}")
            for i, trans in enumerate(deposits[:3]):  # Show first 3
                print(f"  {i+1}. {trans.get('date_string', 'N/A')} - {trans.get('description', 'N/A')}: ${trans.get('amount', 0):.2f}")
            if len(deposits) > 3:
                print(f"  ... and {len(deposits) - 3} more")
        
        print(f"\nWithdrawals: {len(withdrawals)} transactions")
        if withdrawals:
            total_withdrawals = sum(t['amount'] for t in withdrawals)
            print(f"Total withdrawals: ${total_withdrawals:,.2f}")
            for i, trans in enumerate(withdrawals[:3]):  # Show first 3
                print(f"  {i+1}. {trans.get('date_string', 'N/A')} - {trans.get('description', 'N/A')}: ${trans.get('amount', 0):.2f}")
            if len(withdrawals) > 3:
                print(f"  ... and {len(withdrawals) - 3} more")
        
        # Store results
        all_results[pdf_path] = {
            'total': len(transactions),
            'deposits': len(deposits),
            'withdrawals': len(withdrawals),
            'transactions': transactions
        }
        
    except Exception as e:
        print(f"ERROR parsing PDF: {e}")
        import traceback
        traceback.print_exc()
        all_results[pdf_path] = {'error': str(e)}

print("\n\n" + "=" * 80)
print("SUMMARY OF ALL TESTS")
print("=" * 80)

for pdf_path, result in all_results.items():
    print(f"\n{os.path.basename(pdf_path)}:")
    if 'error' in result:
        print(f"  ERROR: {result['error']}")
    else:
        print(f"  Total: {result['total']} transactions")
        print(f"  Deposits: {result['deposits']}")
        print(f"  Withdrawals: {result['withdrawals']}")

# Check for potential issues
print("\n\nPOTENTIAL ISSUES:")
for pdf_path, result in all_results.items():
    if 'error' not in result and result['total'] <= 1:
        print(f"⚠️  {os.path.basename(pdf_path)}: Only {result['total']} transaction(s) found - may need investigation")