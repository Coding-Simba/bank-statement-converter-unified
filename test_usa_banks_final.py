#!/usr/bin/env python3
"""Test all USA bank PDFs including Huntington fix"""

import sys
import os
import json
from datetime import datetime

sys.path.append('backend')
from universal_parser import parse_universal_pdf

def test_bank_pdf(pdf_path, bank_name):
    """Test a single bank PDF"""
    print(f"\n{'='*60}")
    print(f"Testing: {bank_name}")
    print(f"File: {os.path.basename(pdf_path)}")
    print(f"{'='*60}")
    
    if not os.path.exists(pdf_path):
        print(f"❌ ERROR: File not found")
        return {
            'bank': bank_name,
            'success': False,
            'error': 'File not found',
            'transaction_count': 0
        }
    
    try:
        transactions = parse_universal_pdf(pdf_path)
        print(f"✓ Found {len(transactions)} transactions")
        
        if transactions:
            # Show first few transactions
            print("\nFirst 3 transactions:")
            for i, trans in enumerate(transactions[:3]):
                date_str = trans.get('date').strftime('%Y-%m-%d') if trans.get('date') else 'No date'
                desc = trans.get('description', 'No description')[:40]
                amount = trans.get('amount', 'No amount')
                if isinstance(amount, (int, float)):
                    print(f"  {i+1}. {date_str} | {desc:<40} | ${amount:>10.2f}")
                else:
                    print(f"  {i+1}. {date_str} | {desc:<40} | {amount}")
        
        return {
            'bank': bank_name,
            'success': len(transactions) > 0,
            'transaction_count': len(transactions),
            'error': None if transactions else 'No transactions found'
        }
        
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return {
            'bank': bank_name,
            'success': False,
            'error': str(e),
            'transaction_count': 0
        }

def main():
    """Test all USA bank PDFs"""
    print("🏦 USA BANK STATEMENT EXTRACTION TEST")
    print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Define test PDFs
    base_path = "/Users/MAC/Desktop/pdfs/1"
    test_pdfs = [
        ("USA Chase bank.pdf", "Chase Bank"),
        ("USA Discover Bank.pdf", "Discover Bank"),
        ("USA Wells Fargo 7 pages.pdf", "Wells Fargo"),
        ("USA Bank of America.pdf", "Bank of America"),
        ("USA Ohio Huntington bank statement 7  page.pdf", "Huntington Bank")
    ]
    
    results = []
    
    for pdf_file, bank_name in test_pdfs:
        pdf_path = os.path.join(base_path, pdf_file)
        result = test_bank_pdf(pdf_path, bank_name)
        results.append(result)
    
    # Summary report
    print(f"\n{'='*60}")
    print("SUMMARY REPORT")
    print(f"{'='*60}")
    
    successful = sum(1 for r in results if r['success'])
    total_transactions = sum(r['transaction_count'] for r in results)
    
    print(f"\n📈 Overall Results:")
    print(f"   Banks tested: {len(results)}")
    print(f"   Successful extractions: {successful}/{len(results)}")
    print(f"   Total transactions extracted: {total_transactions}")
    
    print(f"\n📊 Bank-by-Bank Results:")
    for result in results:
        status = "✅" if result['success'] else "❌"
        count = result['transaction_count']
        bank = result['bank']
        print(f"   {status} {bank:<20} | {count:>3} transactions")
    
    # Show any failures
    failed = [r for r in results if not r['success']]
    if failed:
        print(f"\n❌ Failed Banks:")
        for result in failed:
            print(f"   {result['bank']}: {result['error']}")
    
    # All successful?
    if successful == len(results):
        print(f"\n✅ SUCCESS: All {len(results)} USA banks parsed successfully!")
    else:
        print(f"\n⚠️  WARNING: {len(failed)} banks failed to parse")
    
    return successful == len(results)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)