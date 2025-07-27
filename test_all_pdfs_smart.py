#!/usr/bin/env python3
"""
Comprehensive PDF testing with AI analysis
Tests each PDF individually and provides detailed analysis
"""
import os
import sys
from datetime import datetime
import json
from typing import List, Dict

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.smart_pdf_analyzer import SmartPDFAnalyzer
from backend.universal_parser import parse_universal_pdf

def analyze_transactions(transactions: List[Dict]) -> Dict:
    """Analyze transaction quality and patterns"""
    if not transactions:
        return {
            'count': 0,
            'quality': 'No transactions found',
            'issues': ['No transactions extracted']
        }
    
    analysis = {
        'count': len(transactions),
        'date_formats': set(),
        'missing_dates': 0,
        'missing_descriptions': 0,
        'missing_amounts': 0,
        'zero_amounts': 0,
        'huge_amounts': 0,
        'negative_amounts': 0,
        'positive_amounts': 0,
        'amount_range': {'min': float('inf'), 'max': float('-inf')},
        'quality': 'Good',
        'issues': []
    }
    
    for trans in transactions:
        # Check dates
        date_str = trans.get('date_string', '')
        if not date_str:
            analysis['missing_dates'] += 1
        else:
            # Detect date format
            if '/' in date_str:
                if len(date_str.split('/')[0]) == 4:
                    analysis['date_formats'].add('YYYY/MM/DD')
                else:
                    analysis['date_formats'].add('MM/DD/YYYY')
            elif '-' in date_str:
                if len(date_str.split('-')[0]) == 4:
                    analysis['date_formats'].add('YYYY-MM-DD')
                else:
                    analysis['date_formats'].add('MM-DD-YYYY')
            else:
                analysis['date_formats'].add('Other')
        
        # Check descriptions
        desc = trans.get('description', '')
        if not desc or len(desc) < 3:
            analysis['missing_descriptions'] += 1
        
        # Check amounts
        amount = trans.get('amount')
        if amount is None:
            analysis['missing_amounts'] += 1
        else:
            if amount == 0:
                analysis['zero_amounts'] += 1
            elif abs(amount) > 1000000:
                analysis['huge_amounts'] += 1
            
            if amount < 0:
                analysis['negative_amounts'] += 1
            else:
                analysis['positive_amounts'] += 1
            
            analysis['amount_range']['min'] = min(analysis['amount_range']['min'], amount)
            analysis['amount_range']['max'] = max(analysis['amount_range']['max'], amount)
    
    # Convert date formats to list
    analysis['date_formats'] = list(analysis['date_formats'])
    
    # Determine quality
    total = analysis['count']
    if analysis['missing_amounts'] > total * 0.1:
        analysis['quality'] = 'Poor'
        analysis['issues'].append(f"{analysis['missing_amounts']} transactions missing amounts")
    elif analysis['missing_dates'] > total * 0.1:
        analysis['quality'] = 'Fair'
        analysis['issues'].append(f"{analysis['missing_dates']} transactions missing dates")
    elif analysis['huge_amounts'] > 0:
        analysis['quality'] = 'Warning'
        analysis['issues'].append(f"{analysis['huge_amounts']} suspiciously large amounts")
    
    if analysis['missing_descriptions'] > total * 0.5:
        analysis['issues'].append(f"{analysis['missing_descriptions']} transactions missing descriptions")
    
    return analysis

def test_pdf(pdf_path: str, use_smart: bool = True) -> Dict:
    """Test a single PDF and return detailed results"""
    filename = os.path.basename(pdf_path)
    print(f"\n{'='*80}")
    print(f"Testing: {filename}")
    print(f"{'='*80}")
    
    result = {
        'filename': filename,
        'path': pdf_path,
        'file_size': os.path.getsize(pdf_path) if os.path.exists(pdf_path) else 0,
        'exists': os.path.exists(pdf_path)
    }
    
    if not result['exists']:
        print("❌ File not found!")
        result['error'] = 'File not found'
        return result
    
    try:
        # Use smart analyzer
        if use_smart:
            print("\n🔍 Analyzing PDF structure...")
            analyzer = SmartPDFAnalyzer(pdf_path)
            print(f"   PDF Info: {analyzer.pdf_info}")
            print(f"   Chosen Parser: {analyzer.choose_best_parser()}")
            
            print("\n🔄 Extracting transactions with Smart Analyzer...")
            transactions = analyzer.extract_transactions()
        else:
            print("\n🔄 Extracting transactions with Universal Parser...")
            transactions = parse_universal_pdf(pdf_path)
        
        # Analyze results
        analysis = analyze_transactions(transactions)
        
        print(f"\n✅ Extraction Results:")
        print(f"   Total Transactions: {analysis['count']}")
        print(f"   Quality: {analysis['quality']}")
        print(f"   Date Formats: {', '.join(analysis.get('date_formats', [])) if analysis.get('date_formats') else 'None'}")
        if 'amount_range' in analysis and analysis['amount_range']['min'] != float('inf'):
            print(f"   Amount Range: ${analysis['amount_range']['min']:.2f} to ${analysis['amount_range']['max']:.2f}")
        
        if analysis['issues']:
            print(f"\n⚠️  Issues:")
            for issue in analysis['issues']:
                print(f"   - {issue}")
        
        # Show sample transactions
        if transactions:
            print(f"\n📊 Sample Transactions (first 5):")
            print(f"{'Date':<15} {'Description':<40} {'Amount':>12}")
            print("-" * 70)
            for trans in transactions[:5]:
                date = trans.get('date_string', 'No date')[:15]
                desc = trans.get('description', 'No description')[:40]
                amount = trans.get('amount', 0)
                print(f"{date:<15} {desc:<40} ${amount:>11.2f}")
        
        result['transactions'] = transactions
        result['analysis'] = analysis
        result['success'] = True
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        result['error'] = str(e)
        result['success'] = False
    
    return result

def main():
    """Test all PDFs"""
    # List of PDFs to test
    pdf_files = [
        "/Users/MAC/Desktop/pdfs/1/Canada RBC (1).pdf",
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
        "/Users/MAC/Desktop/pdfs/1/USA Ohio Huntington bank statement 7  page.pdf",
        "/Users/MAC/Desktop/pdfs/1/USA Chase bank.pdf",
        "/Users/MAC/Desktop/pdfs/1/USA Discover Bank.pdf",
        "/Users/MAC/Desktop/pdfs/1/USA Netspend Bank Statement.pdf",
        "/Users/MAC/Desktop/pdfs/1/USA Wells Fargo 7 pages.pdf",
        "/Users/MAC/Desktop/pdfs/1/Australia Commonwealth J C.pdf",
        "/Users/MAC/Desktop/pdfs/merged_statements_2025-07-26.pdf",
        "/Users/MAC/Desktop/pdfs/Bank-Statement-Template-4-TemplateLab.pdf",
        "/Users/MAC/Desktop/pdfs/dummy_statement.pdf",
        "/Users/MAC/Desktop/pdfs/Bank Statement Example Final.pdf"
    ]
    
    # Test each PDF
    all_results = []
    
    for pdf_path in pdf_files:
        result = test_pdf(pdf_path, use_smart=True)
        all_results.append(result)
        
        # Brief pause to avoid overwhelming the system
        import time
        time.sleep(0.5)
    
    # Summary
    print(f"\n{'='*80}")
    print("SUMMARY")
    print(f"{'='*80}")
    
    successful = [r for r in all_results if r.get('success', False)]
    failed = [r for r in all_results if not r.get('success', False)]
    
    print(f"\n📈 Overall Results:")
    print(f"   Total PDFs: {len(all_results)}")
    print(f"   Successful: {len(successful)}")
    print(f"   Failed: {len(failed)}")
    
    if successful:
        total_transactions = sum(r.get('analysis', {}).get('count', 0) for r in successful)
        print(f"   Total Transactions Extracted: {total_transactions}")
        
        # Quality breakdown
        quality_counts = {}
        for r in successful:
            quality = r.get('analysis', {}).get('quality', 'Unknown')
            quality_counts[quality] = quality_counts.get(quality, 0) + 1
        
        print(f"\n📊 Quality Distribution:")
        for quality, count in quality_counts.items():
            print(f"   {quality}: {count} PDFs")
    
    # Save detailed results
    results_file = 'pdf_test_results_detailed.json'
    with open(results_file, 'w') as f:
        # Remove transaction data for file size
        clean_results = []
        for r in all_results:
            clean_r = r.copy()
            if 'transactions' in clean_r:
                clean_r['transaction_count'] = len(clean_r['transactions'])
                clean_r['sample_transactions'] = clean_r['transactions'][:3]
                del clean_r['transactions']
            clean_results.append(clean_r)
        
        json.dump(clean_results, f, indent=2, default=str)
    
    print(f"\n💾 Detailed results saved to: {results_file}")

if __name__ == "__main__":
    # Test single PDF if provided as argument
    if len(sys.argv) > 1:
        pdf_path = sys.argv[1]
        test_pdf(pdf_path, use_smart=True)
    else:
        # Test all PDFs
        main()