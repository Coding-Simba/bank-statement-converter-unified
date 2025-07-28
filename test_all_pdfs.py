#!/usr/bin/env python3
"""Test all user PDFs and verify transaction extraction"""

from backend.universal_parser import parse_universal_pdf
import os
import json
from datetime import datetime
import re

# List of PDFs to test
pdf_files = [
    '/Users/MAC/Desktop/pdfs/merged_statements_2025-07-26.pdf',
    '/Users/MAC/Desktop/pdfs/Bank-Statement-Template-4-TemplateLab.pdf',
    '/Users/MAC/Desktop/pdfs/dummy_statement.pdf',
    '/Users/MAC/Desktop/pdfs/Bank Statement Example Final.pdf',
    '/Users/MAC/Desktop/pdfs/1/Canada RBC (1).pdf',
    '/Users/MAC/Desktop/pdfs/1/Australia Westpac bank statement.pdf',
    '/Users/MAC/Desktop/pdfs/1/Australia Bendigo Bank Statement.pdf',
    '/Users/MAC/Desktop/pdfs/1/Canada RBC.pdf',
    '/Users/MAC/Desktop/pdfs/1/United Kingdom Metro Bank.pdf',
    '/Users/MAC/Desktop/pdfs/1/UK Nationwide word pdf.pdf',
    '/Users/MAC/Desktop/pdfs/1/USA Woodforest.pdf',
    '/Users/MAC/Desktop/pdfs/1/USA PNC 2.pdf',
    '/Users/MAC/Desktop/pdfs/1/USA Citizens Bank.pdf',
    '/Users/MAC/Desktop/pdfs/1/USA Fifth Third Bank.pdf',
    '/Users/MAC/Desktop/pdfs/1/USA Suntrust.pdf',
    '/Users/MAC/Desktop/pdfs/1/USA Ohio Huntington bank statement 7  page.pdf',
    '/Users/MAC/Desktop/pdfs/1/USA Chase bank.pdf',
    '/Users/MAC/Desktop/pdfs/1/USA Discover Bank.pdf',
    '/Users/MAC/Desktop/pdfs/1/USA Netspend Bank Statement.pdf',
    '/Users/MAC/Desktop/pdfs/1/Australia ANZ.pdf',
    '/Users/MAC/Desktop/pdfs/1/Australia Commonwealth J C.pdf'
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
    if 'error' not in result:
        issues = []
        
        # Check for too few transactions
        if result['total'] <= 3:
            issues.append(f"Only {result['total']} transaction(s) found")
        
        # Check for missing dates/amounts
        if 'transactions' in result:
            missing_dates = sum(1 for t in result['transactions'] if not t.get('date_string'))
            missing_amounts = sum(1 for t in result['transactions'] if t.get('amount') is None)
            
            if missing_dates > 0:
                issues.append(f"{missing_dates} transactions missing dates")
            if missing_amounts > 0:
                issues.append(f"{missing_amounts} transactions missing amounts")
                
            # Check for unrealistic amounts
            amounts = [t.get('amount', 0) for t in result['transactions'] if t.get('amount') is not None]
            huge_amounts = [a for a in amounts if abs(a) > 1000000]
            if huge_amounts:
                issues.append(f"{len(huge_amounts)} suspiciously large amounts")
        
        if issues:
            print(f"\n⚠️  {os.path.basename(pdf_path)}:")
            for issue in issues:
                print(f"    - {issue}")

# Save detailed results
print("\n\nSaving detailed results to test_results.json...")
with open('test_results.json', 'w') as f:
    # Convert to serializable format
    serializable_results = {}
    for pdf, result in all_results.items():
        if 'transactions' in result:
            # Only save summary, not full transactions
            serializable_results[os.path.basename(pdf)] = {
                'total': result['total'],
                'deposits': result['deposits'],
                'withdrawals': result['withdrawals'],
                'sample_transactions': result['transactions'][:5] if result['transactions'] else []
            }
        else:
            serializable_results[os.path.basename(pdf)] = result
    
    json.dump(serializable_results, f, indent=2, default=str)
print("Results saved!")