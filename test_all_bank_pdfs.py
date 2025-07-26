#!/usr/bin/env python3
"""Test all bank PDFs systematically and report issues"""

import os
import sys
from backend.universal_parser import parse_universal_pdf
from datetime import datetime
import json

# List of all PDFs to test
PDF_FILES = [
    # Australia
    '/Users/MAC/Desktop/pdfs/1/Australia ANZ.pdf',
    '/Users/MAC/Desktop/pdfs/1/Australia Commonwealth J C.pdf',
    '/Users/MAC/Desktop/pdfs/1/Australia Westpac bank statement.pdf',
    
    # Canada
    '/Users/MAC/Desktop/pdfs/1/Canada RBC.pdf',
    
    # UK
    '/Users/MAC/Desktop/pdfs/1/Monzo Bank st. word.pdf',
    '/Users/MAC/Desktop/pdfs/1/UK Monese Bank Statement.pdf',
    '/Users/MAC/Desktop/pdfs/1/UK Santander.pdf',
    
    # USA
    '/Users/MAC/Desktop/pdfs/1/USA Bank of America.zip',  # Note: This is a ZIP file
    '/Users/MAC/Desktop/pdfs/1/USA BECU statement 4 pages.pdf',
    '/Users/MAC/Desktop/pdfs/1/USA Citizens Bank.pdf',
    '/Users/MAC/Desktop/pdfs/1/USA Discover Bank.pdf',
    '/Users/MAC/Desktop/pdfs/1/USA Green Dot Bank Statement 3 page.pdf',
    '/Users/MAC/Desktop/pdfs/1/USA Netspend Bank Statement.pdf',
    '/Users/MAC/Desktop/pdfs/1/USA PayPal Account Statement.pdf',
    '/Users/MAC/Desktop/pdfs/1/USA Suntrust.pdf',
    '/Users/MAC/Desktop/pdfs/1/USA Woodforest.pdf',
    '/Users/MAC/Desktop/pdfs/1/Walmart Money Card Bank Statement 3 page.pdf'
]

def test_pdf(pdf_path):
    """Test a single PDF and return detailed results"""
    result = {
        'path': pdf_path,
        'filename': os.path.basename(pdf_path),
        'status': 'not_tested',
        'total_transactions': 0,
        'deposits': 0,
        'withdrawals': 0,
        'errors': [],
        'warnings': [],
        'transactions': []
    }
    
    # Check if file exists
    if not os.path.exists(pdf_path):
        result['status'] = 'file_not_found'
        result['errors'].append(f"File not found: {pdf_path}")
        return result
    
    # Check if it's a ZIP file
    if pdf_path.endswith('.zip'):
        result['status'] = 'zip_file'
        result['warnings'].append("This is a ZIP file - needs to be extracted first")
        return result
    
    # Try to parse the PDF
    try:
        print(f"\nParsing: {result['filename']}")
        print("-" * 80)
        
        transactions = parse_universal_pdf(pdf_path)
        
        result['status'] = 'parsed'
        result['total_transactions'] = len(transactions)
        result['transactions'] = transactions
        
        # Analyze transactions
        deposits = [t for t in transactions if t.get('amount', 0) > 0]
        withdrawals = [t for t in transactions if t.get('amount', 0) < 0]
        
        result['deposits'] = len(deposits)
        result['withdrawals'] = len(withdrawals)
        
        # Calculate totals
        total_deposits = sum(t['amount'] for t in deposits) if deposits else 0
        total_withdrawals = sum(t['amount'] for t in withdrawals) if withdrawals else 0
        
        result['total_deposits_amount'] = total_deposits
        result['total_withdrawals_amount'] = total_withdrawals
        
        # Warnings
        if result['total_transactions'] == 0:
            result['warnings'].append("No transactions found - PDF might not be parsed correctly")
        elif result['total_transactions'] <= 2:
            result['warnings'].append(f"Only {result['total_transactions']} transactions found - might be incomplete")
        
        if result['deposits'] == 0 and result['total_transactions'] > 0:
            result['warnings'].append("No deposits found - all transactions marked as withdrawals")
        elif result['withdrawals'] == 0 and result['total_transactions'] > 0:
            result['warnings'].append("No withdrawals found - all transactions marked as deposits")
        
        # Print summary
        print(f"Total transactions: {result['total_transactions']}")
        print(f"Deposits: {result['deposits']} (${total_deposits:,.2f})")
        print(f"Withdrawals: {result['withdrawals']} (${total_withdrawals:,.2f})")
        
        if result['warnings']:
            print("\nWarnings:")
            for warning in result['warnings']:
                print(f"  ⚠️  {warning}")
        
    except Exception as e:
        result['status'] = 'error'
        result['errors'].append(str(e))
        print(f"Error parsing PDF: {e}")
        import traceback
        traceback.print_exc()
    
    return result

def main():
    """Test all PDFs and generate report"""
    print("=" * 80)
    print("TESTING ALL BANK STATEMENT PDFs")
    print("=" * 80)
    print(f"Total PDFs to test: {len(PDF_FILES)}")
    
    # Create results directory
    os.makedirs('test_results', exist_ok=True)
    
    all_results = []
    summary = {
        'total_pdfs': len(PDF_FILES),
        'successful': 0,
        'failed': 0,
        'warnings': 0,
        'not_found': 0,
        'zip_files': 0
    }
    
    # Test each PDF
    for i, pdf_path in enumerate(PDF_FILES, 1):
        print(f"\n\n[{i}/{len(PDF_FILES)}] Testing: {os.path.basename(pdf_path)}")
        result = test_pdf(pdf_path)
        all_results.append(result)
        
        # Update summary
        if result['status'] == 'parsed':
            summary['successful'] += 1
            if result['warnings']:
                summary['warnings'] += 1
        elif result['status'] == 'error':
            summary['failed'] += 1
        elif result['status'] == 'file_not_found':
            summary['not_found'] += 1
        elif result['status'] == 'zip_file':
            summary['zip_files'] += 1
    
    # Print final summary
    print("\n\n" + "=" * 80)
    print("FINAL SUMMARY")
    print("=" * 80)
    print(f"Total PDFs tested: {summary['total_pdfs']}")
    print(f"✅ Successfully parsed: {summary['successful']}")
    print(f"⚠️  Parsed with warnings: {summary['warnings']}")
    print(f"❌ Failed to parse: {summary['failed']}")
    print(f"📁 ZIP files: {summary['zip_files']}")
    print(f"🚫 Files not found: {summary['not_found']}")
    
    # Save detailed results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = f"test_results/test_results_{timestamp}.json"
    
    with open(results_file, 'w') as f:
        json.dump({
            'timestamp': timestamp,
            'summary': summary,
            'results': all_results
        }, f, indent=2, default=str)
    
    print(f"\nDetailed results saved to: {results_file}")
    
    # Print PDFs that need attention
    print("\n\nPDFs THAT NEED ATTENTION:")
    print("-" * 40)
    
    for result in all_results:
        if result['status'] != 'parsed' or result['warnings'] or result['errors']:
            print(f"\n{result['filename']}:")
            if result['status'] == 'error':
                print(f"  Status: ERROR")
                for error in result['errors']:
                    print(f"  Error: {error}")
            elif result['status'] == 'file_not_found':
                print(f"  Status: FILE NOT FOUND")
            elif result['status'] == 'zip_file':
                print(f"  Status: ZIP FILE (needs extraction)")
            elif result['warnings']:
                print(f"  Status: PARSED WITH WARNINGS")
                for warning in result['warnings']:
                    print(f"  Warning: {warning}")

if __name__ == "__main__":
    main()