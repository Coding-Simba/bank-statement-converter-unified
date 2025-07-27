#!/usr/bin/env python3
"""Batch test PDFs with timeout and detailed results"""
import sys
sys.path.insert(0, '.')
from backend.universal_parser import parse_universal_pdf
import os
import signal
import json
from datetime import datetime

class TimeoutException(Exception):
    pass

def timeout_handler(signum, frame):
    raise TimeoutException("PDF processing timed out")

def test_pdf_with_timeout(pdf_path, timeout=30):
    """Test PDF with timeout"""
    result = {
        'filename': os.path.basename(pdf_path),
        'path': pdf_path,
        'timestamp': datetime.now().isoformat()
    }
    
    if not os.path.exists(pdf_path):
        result['status'] = 'not_found'
        return result
    
    # Set timeout
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(timeout)
    
    try:
        trans = parse_universal_pdf(pdf_path)
        signal.alarm(0)  # Cancel timeout
        
        result['status'] = 'success'
        result['transaction_count'] = len(trans)
        
        # Analyze transactions
        if trans:
            result['sample_transactions'] = []
            for t in trans[:3]:  # First 3 transactions
                result['sample_transactions'].append({
                    'date': t.get('date_string', 'No date'),
                    'description': (t.get('description', 'No description') or '')[:50],
                    'amount': t.get('amount', 0) or 0
                })
            
            # Quality check
            missing_dates = sum(1 for t in trans if not t.get('date_string'))
            missing_amounts = sum(1 for t in trans if t.get('amount') is None)
            
            result['quality'] = {
                'missing_dates': missing_dates,
                'missing_amounts': missing_amounts,
                'quality_score': 'Good' if missing_dates == 0 and missing_amounts == 0 else 'Fair'
            }
        else:
            result['quality'] = {'quality_score': 'No transactions'}
            
    except TimeoutException:
        signal.alarm(0)  # Cancel timeout
        result['status'] = 'timeout'
        result['error'] = f'Processing exceeded {timeout} seconds'
    except Exception as e:
        signal.alarm(0)  # Cancel timeout
        result['status'] = 'error'
        result['error'] = str(e)
    
    return result

def main():
    # List of PDFs
    pdf_files = [
        "/Users/MAC/Desktop/pdfs/dummy_statement.pdf",
        "/Users/MAC/Desktop/pdfs/Bank Statement Example Final.pdf",
        "/Users/MAC/Desktop/pdfs/Bank-Statement-Template-4-TemplateLab.pdf",
        "/Users/MAC/Desktop/pdfs/merged_statements_2025-07-26.pdf",
        "/Users/MAC/Desktop/pdfs/1/Canada RBC.pdf",
        "/Users/MAC/Desktop/pdfs/1/Canada RBC (1).pdf",
        "/Users/MAC/Desktop/pdfs/1/Australia Westpac bank statement.pdf",
        "/Users/MAC/Desktop/pdfs/1/Australia Bendigo Bank Statement.pdf",
        "/Users/MAC/Desktop/pdfs/1/Australia Commonwealth J C.pdf",
        "/Users/MAC/Desktop/pdfs/1/United Kingdom Metro Bank.pdf",
        "/Users/MAC/Desktop/pdfs/1/UK Nationwide word pdf.pdf",
        "/Users/MAC/Desktop/pdfs/1/USA Woodforest.pdf",
        "/Users/MAC/Desktop/pdfs/1/USA PNC 2.pdf",
        "/Users/MAC/Desktop/pdfs/1/USA Citizens Bank.pdf",
        "/Users/MAC/Desktop/pdfs/1/USA Fifth Third Bank.pdf",
        "/Users/MAC/Desktop/pdfs/1/USA Suntrust.pdf",
        "/Users/MAC/Desktop/pdfs/1/USA Ohio Huntington bank statement 7  page.pdf",
        "/Users/MAC/Desktop/pdfs/1/USA Chase bank.pdf",
        "/Users/MAC/Desktop/pdfs/1/USA Discover Bank.pdf",
        "/Users/MAC/Desktop/pdfs/1/USA Netspend Bank Statement.pdf",
        "/Users/MAC/Desktop/pdfs/1/USA Wells Fargo 7 pages.pdf"
    ]
    
    results = []
    
    for i, pdf_path in enumerate(pdf_files, 1):
        print(f"\n[{i}/{len(pdf_files)}] Testing: {os.path.basename(pdf_path)}")
        print("-" * 60)
        
        result = test_pdf_with_timeout(pdf_path, timeout=30)
        
        # Print summary
        if result['status'] == 'success':
            print(f"✓ Success: {result['transaction_count']} transactions")
            if result.get('sample_transactions'):
                print("  Sample transactions:")
                for j, t in enumerate(result['sample_transactions'], 1):
                    print(f"    {j}. {t['date']} - {t['description']} - ${t['amount']:.2f}")
        elif result['status'] == 'timeout':
            print(f"⏱ Timeout: {result['error']}")
        elif result['status'] == 'not_found':
            print("❌ File not found")
        else:
            print(f"❌ Error: {result.get('error', 'Unknown error')}")
        
        results.append(result)
    
    # Save results
    with open('batch_test_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    
    successful = [r for r in results if r['status'] == 'success']
    failed = [r for r in results if r['status'] != 'success']
    
    print(f"Total PDFs: {len(results)}")
    print(f"Successful: {len(successful)}")
    print(f"Failed: {len(failed)}")
    
    if successful:
        total_trans = sum(r['transaction_count'] for r in successful)
        print(f"Total transactions extracted: {total_trans}")
        
        # PDFs with issues
        low_trans = [r for r in successful if r['transaction_count'] < 5]
        if low_trans:
            print(f"\nPDFs with few transactions (<5):")
            for r in low_trans:
                print(f"  - {r['filename']}: {r['transaction_count']} transactions")

if __name__ == "__main__":
    main()