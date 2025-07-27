#!/usr/bin/env python3
"""Test all bank PDFs with updated parsers"""

from backend.universal_parser import parse_universal_pdf
import os
from datetime import datetime

# List of all PDFs with expected results
test_pdfs = [
    # Australia
    {
        'name': 'Australia ANZ.pdf',
        'path': '/Users/MAC/Desktop/pdfs/1/Australia ANZ.pdf',
        'expected_count': 10,  # Summary statement
        'expected_deposits': None,
        'expected_withdrawals': None
    },
    {
        'name': 'Australia Commonwealth J C.pdf',
        'path': '/Users/MAC/Desktop/pdfs/1/Australia Commonwealth J C.pdf',
        'expected_count': 461,
        'expected_deposits': 90,
        'expected_withdrawals': 371
    },
    {
        'name': 'Australia Westpac bank statement.pdf',
        'path': '/Users/MAC/Desktop/pdfs/1/Australia Westpac bank statement.pdf',
        'expected_count': 15,
        'expected_deposits': 7,
        'expected_withdrawals': 8
    },
    # Canada
    {
        'name': 'Canada RBC.pdf',
        'path': '/Users/MAC/Desktop/pdfs/1/Canada RBC.pdf',
        'expected_count': 50,
        'expected_deposits': 8,
        'expected_withdrawals': 42
    },
    # UK
    {
        'name': 'Monzo Bank st. word.pdf',
        'path': '/Users/MAC/Desktop/pdfs/1/Monzo Bank st. word.pdf',
        'expected_count': 28,
        'expected_deposits': 13,
        'expected_withdrawals': 15
    },
    {
        'name': 'UK Monese Bank Statement.pdf',
        'path': '/Users/MAC/Desktop/pdfs/1/UK Monese Bank Statement.pdf',
        'expected_count': 29,
        'expected_deposits': 6,
        'expected_withdrawals': 23
    },
    {
        'name': 'UK Santander.pdf',
        'path': '/Users/MAC/Desktop/pdfs/1/UK Santander.pdf',
        'expected_count': 27,
        'expected_deposits': 4,
        'expected_withdrawals': 23
    },
    # USA
    {
        'name': 'USA Bank of America.pdf',
        'path': '/Users/MAC/Desktop/pdfs/1/USA Bank of America.pdf',
        'expected_count': 69,
        'expected_deposits': 28,
        'expected_withdrawals': 41
    },
    {
        'name': 'USA BECU statement 4 pages.pdf',
        'path': '/Users/MAC/Desktop/pdfs/1/USA BECU statement 4 pages.pdf',
        'expected_count': 71,
        'expected_deposits': 9,
        'expected_withdrawals': 62
    },
    {
        'name': 'USA Citizens Bank.pdf',
        'path': '/Users/MAC/Desktop/pdfs/1/USA Citizens Bank.pdf',
        'expected_count': 68,
        'expected_deposits': 9,
        'expected_withdrawals': 59
    },
    {
        'name': 'USA Discover Bank.pdf',
        'path': '/Users/MAC/Desktop/pdfs/1/USA Discover Bank.pdf',
        'expected_count': 32,
        'expected_deposits': 1,
        'expected_withdrawals': 31
    },
    {
        'name': 'USA Green Dot Bank Statement 3 page.pdf',
        'path': '/Users/MAC/Desktop/pdfs/1/USA Green Dot Bank Statement 3 page.pdf',
        'expected_count': 2,
        'expected_deposits': 1,
        'expected_withdrawals': 1
    },
    {
        'name': 'USA Netspend Bank Statement.pdf',
        'path': '/Users/MAC/Desktop/pdfs/1/USA Netspend Bank Statement.pdf',
        'expected_count': 24,
        'expected_deposits': 9,
        'expected_withdrawals': 15
    },
    {
        'name': 'USA PayPal Account Statement.pdf',
        'path': '/Users/MAC/Desktop/pdfs/1/USA PayPal Account Statement.pdf',
        'expected_count': 10,
        'expected_deposits': 5,
        'expected_withdrawals': 5
    },
    {
        'name': 'USA Suntrust.pdf',
        'path': '/Users/MAC/Desktop/pdfs/1/USA Suntrust.pdf',
        'expected_count': 9,
        'expected_deposits': 0,
        'expected_withdrawals': 9
    },
    {
        'name': 'USA Woodforest.pdf',
        'path': '/Users/MAC/Desktop/pdfs/1/USA Woodforest.pdf',
        'expected_count': 51,
        'expected_deposits': 10,
        'expected_withdrawals': 41
    },
    {
        'name': 'Walmart Money Card Bank Statement 3 page.pdf',
        'path': '/Users/MAC/Desktop/pdfs/1/Walmart Money Card Bank Statement 3 page.pdf',
        'expected_count': 16,
        'expected_deposits': 3,
        'expected_withdrawals': 13
    }
]

def test_pdf(pdf_info):
    """Test a single PDF"""
    print(f"\n{'='*60}")
    print(f"Testing: {pdf_info['name']}")
    print(f"Path: {pdf_info['path']}")
    
    if not os.path.exists(pdf_info['path']):
        print(f"❌ ERROR: File not found!")
        return False
    
    try:
        # Parse the PDF
        transactions = parse_universal_pdf(pdf_info['path'])
        
        # Count transactions
        total = len(transactions)
        deposits = len([t for t in transactions if t.get('amount', 0) > 0])
        withdrawals = len([t for t in transactions if t.get('amount', 0) < 0])
        
        print(f"\nResults:")
        print(f"  Total transactions: {total}")
        print(f"  Deposits: {deposits}")
        print(f"  Withdrawals: {withdrawals}")
        
        # Check against expected
        passed = True
        if pdf_info['expected_count'] and total != pdf_info['expected_count']:
            print(f"  ⚠️  Expected {pdf_info['expected_count']} transactions, got {total}")
            passed = False
        else:
            print(f"  ✅ Transaction count matches expected")
            
        if pdf_info['expected_deposits'] is not None and deposits != pdf_info['expected_deposits']:
            print(f"  ⚠️  Expected {pdf_info['expected_deposits']} deposits, got {deposits}")
            passed = False
            
        if pdf_info['expected_withdrawals'] is not None and withdrawals != pdf_info['expected_withdrawals']:
            print(f"  ⚠️  Expected {pdf_info['expected_withdrawals']} withdrawals, got {withdrawals}")
            passed = False
            
        # Show sample transactions
        if transactions:
            print(f"\n  Sample transactions:")
            for i, trans in enumerate(transactions[:3]):
                print(f"    {trans.get('date_string', 'N/A')} - {trans.get('description', 'N/A')[:40]}... ${trans['amount']:.2f}")
                
        return passed
        
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    print("COMPREHENSIVE BANK PDF PARSER TEST")
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Total PDFs to test: {len(test_pdfs)}")
    
    passed = 0
    failed = 0
    
    for pdf_info in test_pdfs:
        if test_pdf(pdf_info):
            passed += 1
        else:
            failed += 1
    
    print("\n" + "="*60)
    print("FINAL RESULTS:")
    print(f"  ✅ Passed: {passed}")
    print(f"  ❌ Failed: {failed}")
    print(f"  Success Rate: {(passed/len(test_pdfs)*100):.1f}%")
    print("="*60)

if __name__ == "__main__":
    main()