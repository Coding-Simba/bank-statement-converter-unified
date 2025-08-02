#!/usr/bin/env python3
"""
Test Robust Parser with Training PDFs
====================================

Tests the new parser architecture with all provided training PDFs
and generates a comprehensive report.
"""

import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path
import pandas as pd

# Add backend to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from parsers.integration_layer import process_multiple_pdfs, parse_universal_pdf

# Training PDFs
TRAINING_PDFS = [
    "/Users/MAC/Desktop/pdfs/1/Australia Westpac bank statement.pdf",
    "/Users/MAC/Desktop/pdfs/1/Australia Bendigo Bank Statement.pdf",
    "/Users/MAC/Desktop/pdfs/1/Canada RBC.pdf",
    "/Users/MAC/Desktop/pdfs/1/United Kingdom Metro Bank.pdf",
    "/Users/MAC/Desktop/pdfs/1/UK Nationwide word pdf.pdf",
    "/Users/MAC/Desktop/pdfs/1/USA Woodforest.pdf",
    "/Users/MAC/Desktop/pdfs/1/USA PNC 2.pdf",
    "/Users/MAC/Desktop/pdfs/1/USA Citizens Bank.pdf",
    "/Users/MAC/Desktop/pdfs/1/USA Fifth Third Bank.pdf",
    "/Users/MAC/Desktop/pdfs/1/USA Suntrust.pdf",
    "/Users/MAC/Desktop/pdfs/1/USA Ohio Huntington bank statement 7 page.pdf",
    "/Users/MAC/Desktop/pdfs/1/USA Chase bank.pdf",
    "/Users/MAC/Desktop/pdfs/1/USA Discover Bank.pdf",
    "/Users/MAC/Desktop/pdfs/1/USA Wells Fargo 7 pages.pdf",
    "/Users/MAC/Desktop/pdfs/1/USA Bank of America.pdf",
    "/Users/MAC/Desktop/pdfs/1/Australia Commonwealth J C.pdf",
    "/Users/MAC/Desktop/pdfs/merged_statements_2025-07-26.pdf",
    "/Users/MAC/Desktop/pdfs/Bank-Statement-Template-4-TemplateLab.pdf",
    "/Users/MAC/Desktop/pdfs/dummy_statement.pdf",
    "/Users/MAC/Desktop/pdfs/Bank Statement Example Final.pdf"
]

def test_single_pdf(pdf_path: str) -> dict:
    """Test a single PDF and return results"""
    print(f"\n📄 Testing: {os.path.basename(pdf_path)}")
    
    start_time = datetime.now()
    result = {
        'pdf': os.path.basename(pdf_path),
        'path': pdf_path,
        'exists': os.path.exists(pdf_path)
    }
    
    if not result['exists']:
        print(f"  ❌ File not found")
        result['error'] = 'File not found'
        return result
    
    try:
        # Parse PDF
        transactions = parse_universal_pdf(pdf_path)
        parse_time = (datetime.now() - start_time).total_seconds()
        
        result['success'] = True
        result['parse_time'] = parse_time
        result['transaction_count'] = len(transactions)
        
        if transactions:
            # Analyze transactions
            dates = [tx['date'] for tx in transactions if 'date' in tx]
            amounts = [tx['amount'] for tx in transactions if 'amount' in tx]
            
            result['date_range'] = {
                'start': min(dates).strftime('%Y-%m-%d') if dates else None,
                'end': max(dates).strftime('%Y-%m-%d') if dates else None
            }
            
            result['amount_summary'] = {
                'total_debits': sum(a for a in amounts if a < 0),
                'total_credits': sum(a for a in amounts if a > 0),
                'average_amount': sum(amounts) / len(amounts) if amounts else 0
            }
            
            # Sample transactions
            result['sample_transactions'] = [
                {
                    'date': tx.get('date_string', ''),
                    'description': tx.get('description', '')[:50],
                    'amount': tx.get('amount', 0)
                }
                for tx in transactions[:3]
            ]
            
            print(f"  ✅ Success: {len(transactions)} transactions in {parse_time:.2f}s")
            print(f"     Date range: {result['date_range']['start']} to {result['date_range']['end']}")
            print(f"     Credits: ${result['amount_summary']['total_credits']:.2f}, "
                  f"Debits: ${abs(result['amount_summary']['total_debits']):.2f}")
        else:
            result['success'] = False
            result['error'] = 'No transactions found'
            print(f"  ⚠️  No transactions found")
            
    except Exception as e:
        result['success'] = False
        result['error'] = str(e)
        print(f"  ❌ Error: {e}")
    
    return result

async def test_parallel_processing():
    """Test parallel processing capabilities"""
    print("\n🚀 Testing Parallel Processing (20 workers)")
    print("=" * 60)
    
    # Filter existing PDFs
    existing_pdfs = [pdf for pdf in TRAINING_PDFS if os.path.exists(pdf)]
    print(f"Found {len(existing_pdfs)} PDFs to process")
    
    if not existing_pdfs:
        print("❌ No PDFs found to test")
        return {}
    
    # Process in parallel
    start_time = datetime.now()
    results = await process_multiple_pdfs(existing_pdfs, num_workers=20)
    total_time = (datetime.now() - start_time).total_seconds()
    
    print(f"\n✅ Processed {len(existing_pdfs)} PDFs in {total_time:.2f} seconds")
    print(f"   Average: {total_time/len(existing_pdfs):.2f} seconds per PDF")
    print(f"   Speed: {len(existing_pdfs)/total_time:.2f} PDFs per second")
    
    return results

def generate_report(test_results: list, parallel_results: dict):
    """Generate comprehensive test report"""
    
    # Create report
    report = {
        'test_date': datetime.now().isoformat(),
        'summary': {
            'total_pdfs_tested': len(test_results),
            'successful': sum(1 for r in test_results if r.get('success', False)),
            'failed': sum(1 for r in test_results if not r.get('success', False)),
            'missing': sum(1 for r in test_results if not r.get('exists', False)),
            'total_transactions': sum(r.get('transaction_count', 0) for r in test_results),
            'average_parse_time': sum(r.get('parse_time', 0) for r in test_results if 'parse_time' in r) / 
                                sum(1 for r in test_results if 'parse_time' in r) if any('parse_time' in r for r in test_results) else 0
        },
        'individual_results': test_results,
        'parallel_processing': parallel_results.get('summary', {})
    }
    
    # Save report
    report_path = f'parser_test_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\n📊 Report saved to: {report_path}")
    
    # Generate summary table
    df = pd.DataFrame(test_results)
    
    if 'success' in df.columns:
        success_df = df[df['success'] == True]
        
        if not success_df.empty:
            print("\n📈 Success Summary:")
            print(f"{'Bank/PDF':<40} {'Transactions':<15} {'Parse Time':<15}")
            print("-" * 70)
            
            for _, row in success_df.iterrows():
                print(f"{row['pdf'][:40]:<40} {row['transaction_count']:<15} {row.get('parse_time', 0):<15.2f}s")
    
    # Print failures
    if 'success' in df.columns:
        failed_df = df[df['success'] == False]
        
        if not failed_df.empty:
            print("\n❌ Failed PDFs:")
            for _, row in failed_df.iterrows():
                print(f"  - {row['pdf']}: {row.get('error', 'Unknown error')}")
    
    return report

def main():
    """Run comprehensive tests"""
    print("🧪 Testing Robust PDF Parser")
    print("=" * 60)
    
    # Test individual PDFs
    print("\n📋 Testing Individual PDFs")
    print("-" * 60)
    
    test_results = []
    for pdf_path in TRAINING_PDFS:
        result = test_single_pdf(pdf_path)
        test_results.append(result)
    
    # Test parallel processing
    parallel_results = asyncio.run(test_parallel_processing())
    
    # Generate report
    report = generate_report(test_results, parallel_results)
    
    # Print final summary
    print("\n" + "=" * 60)
    print("🎯 FINAL SUMMARY")
    print("=" * 60)
    
    summary = report['summary']
    print(f"Total PDFs Tested: {summary['total_pdfs_tested']}")
    print(f"Successful: {summary['successful']} ({summary['successful']/summary['total_pdfs_tested']*100:.1f}%)")
    print(f"Failed: {summary['failed']}")
    print(f"Missing: {summary['missing']}")
    print(f"Total Transactions Extracted: {summary['total_transactions']:,}")
    print(f"Average Parse Time: {summary['average_parse_time']:.2f} seconds")
    
    if parallel_results.get('summary'):
        p_summary = parallel_results['summary']
        print(f"\nParallel Processing Performance:")
        print(f"  - {p_summary.get('pdfs_per_second', 0):.2f} PDFs per second")
        print(f"  - {p_summary.get('total_transactions', 0):,} total transactions")

if __name__ == "__main__":
    main()