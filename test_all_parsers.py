#!/usr/bin/env python3
"""Test all custom bank parsers with sample PDFs"""

import os
import sys

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from universal_parser_enhanced import parse_universal_pdf_enhanced
import json
from datetime import datetime

# Test PDFs configuration
TEST_PDFS = [
    # High priority banks
    {
        'path': "/Users/MAC/Desktop/pdfs/1/Australia ANZ.pdf",
        'expected_bank': 'anz',
        'min_transactions': 1
    },
    {
        'path': "/Users/MAC/Desktop/pdfs/1/USA BECU statement 4 pages.pdf",
        'expected_bank': 'becu',
        'min_transactions': 10
    },
    {
        'path': "/Users/MAC/Desktop/pdfs/1/USA Citizens Bank.pdf",
        'expected_bank': 'citizens',
        'min_transactions': 10
    },
    {
        'path': "/Users/MAC/Desktop/pdfs/1/Australia Commonwealth J C.pdf",
        'expected_bank': 'commonwealth',
        'min_transactions': 50
    },
    {
        'path': "/Users/MAC/Desktop/pdfs/1/USA Discover Bank.pdf",
        'expected_bank': 'discover',
        'min_transactions': 1
    },
    # Medium priority banks
    {
        'path': "/Users/MAC/Desktop/pdfs/1/USA Green Dot Bank Statement 3 page.pdf",
        'expected_bank': 'green_dot',
        'min_transactions': 3
    },
    {
        'path': "/Users/MAC/Desktop/pdfs/1/UK Lloyds Bank.pdf",
        'expected_bank': 'lloyds',
        'min_transactions': 1
    },
    {
        'path': "/Users/MAC/Desktop/pdfs/1/United Kingdom Metro Bank.pdf",
        'expected_bank': 'metro',
        'min_transactions': 1
    },
    {
        'path': "/Users/MAC/Desktop/pdfs/1/UK Nationwide word pdf.pdf",
        'expected_bank': 'nationwide',
        'min_transactions': 5
    },
    {
        'path': "/Users/MAC/Desktop/pdfs/1/USA Netspend Bank Statement.pdf",
        'expected_bank': 'netspend',
        'min_transactions': 3
    },
    {
        'path': "/Users/MAC/Desktop/pdfs/1/USA PayPal Account Statement.pdf",
        'expected_bank': 'paypal',
        'min_transactions': 10
    },
    {
        'path': "/Users/MAC/Desktop/pdfs/1/Canada Scotiabank.pdf",
        'expected_bank': 'scotiabank',
        'min_transactions': 1
    },
    {
        'path': "/Users/MAC/Desktop/pdfs/1/USA Suntrust.pdf",
        'expected_bank': 'suntrust',
        'min_transactions': 10
    },
    {
        'path': "/Users/MAC/Desktop/pdfs/1/Walmart Money Card Bank Statement 3 page.pdf",
        'expected_bank': 'walmart',
        'min_transactions': 20
    },
    {
        'path': "/Users/MAC/Desktop/pdfs/1/Australia Westpac bank statement.pdf",
        'expected_bank': 'westpac',
        'min_transactions': 20
    },
    # Legacy banks that should still work
    {
        'path': "/Users/MAC/Desktop/pdfs/1/USA Woodforest.pdf",
        'expected_bank': 'woodforest',
        'min_transactions': 40
    }
]

def test_parser(pdf_info):
    """Test a single parser"""
    pdf_path = pdf_info['path']
    expected_bank = pdf_info['expected_bank']
    min_transactions = pdf_info['min_transactions']
    
    print(f"\nTesting: {os.path.basename(pdf_path)}")
    print(f"Expected bank: {expected_bank}")
    print(f"Minimum transactions expected: {min_transactions}")
    
    if not os.path.exists(pdf_path):
        print("❌ PDF file not found")
        return False
    
    try:
        # Parse the PDF
        transactions = parse_universal_pdf_enhanced(pdf_path)
        
        print(f"✓ Parsed successfully")
        print(f"  Transactions found: {len(transactions)}")
        
        # Check transaction count
        if len(transactions) < min_transactions:
            print(f"⚠️  WARNING: Found only {len(transactions)} transactions, expected at least {min_transactions}")
        
        # Check if transactions have required fields
        if transactions:
            # Check first few transactions
            print("  Sample transactions:")
            for i, trans in enumerate(transactions[:3]):
                date = trans.get('date_string', 'NO DATE')
                desc = trans.get('description', 'NO DESCRIPTION')
                amount = trans.get('amount', 0)
                
                # Validate transaction
                has_date = trans.get('date') is not None
                has_desc = bool(desc and desc != 'NO DESCRIPTION')
                has_amount = trans.get('amount') is not None
                
                status = "✓" if all([has_date, has_desc, has_amount]) else "⚠️"
                print(f"    {status} {date} | {desc[:50]}... | ${amount:.2f}")
                
                if not has_date:
                    print(f"       Missing date!")
                if not has_desc:
                    print(f"       Missing description!")
                if not has_amount:
                    print(f"       Missing amount!")
        
        return len(transactions) >= min_transactions
        
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all parser tests"""
    print("=" * 60)
    print("Testing All Custom Bank Parsers")
    print("=" * 60)
    
    results = {
        'passed': 0,
        'failed': 0,
        'warnings': 0
    }
    
    failed_banks = []
    
    for pdf_info in TEST_PDFS:
        success = test_parser(pdf_info)
        
        if success:
            results['passed'] += 1
        else:
            results['failed'] += 1
            failed_banks.append(pdf_info['expected_bank'])
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"Total PDFs tested: {len(TEST_PDFS)}")
    print(f"✓ Passed: {results['passed']}")
    print(f"✗ Failed: {results['failed']}")
    
    if failed_banks:
        print(f"\nFailed banks: {', '.join(failed_banks)}")
    
    # Save detailed results
    results_file = f"parser_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(results_file, 'w') as f:
        json.dump({
            'test_time': datetime.now().isoformat(),
            'total_tests': len(TEST_PDFS),
            'passed': results['passed'],
            'failed': results['failed'],
            'failed_banks': failed_banks
        }, f, indent=2)
    
    print(f"\nDetailed results saved to: {results_file}")
    
    # Return success if all passed
    return results['failed'] == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)