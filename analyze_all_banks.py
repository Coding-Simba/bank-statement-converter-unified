#!/usr/bin/env python3
"""Comprehensive analysis of all bank PDFs to identify which need custom parsers"""

import os
import sys
import json
from datetime import datetime
from typing import List, Dict, Tuple

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

# Import parsers
from universal_parser_enhanced import parse_universal_pdf_enhanced
from dummy_pdf_parser_enhanced import parse_dummy_pdf_enhanced
import PyPDF2
import pdfplumber

def analyze_pdf(pdf_path: str) -> Dict:
    """Analyze a single PDF and return extraction results"""
    result = {
        'pdf_path': pdf_path,
        'filename': os.path.basename(pdf_path),
        'bank_name': extract_bank_name(pdf_path),
        'extraction_status': 'unknown',
        'transaction_count': 0,
        'issues': [],
        'sample_transactions': [],
        'needs_custom_parser': False,
        'pdf_characteristics': {}
    }
    
    try:
        # Get PDF characteristics
        result['pdf_characteristics'] = get_pdf_characteristics(pdf_path)
        
        # Try parsing with enhanced universal parser
        transactions = parse_universal_pdf_enhanced(pdf_path)
        
        result['transaction_count'] = len(transactions)
        result['extraction_status'] = 'success' if transactions else 'no_transactions'
        
        # Get sample transactions
        if transactions:
            result['sample_transactions'] = [
                {
                    'date': t.get('date_string', 'N/A'),
                    'description': t.get('description', 'N/A')[:50],
                    'amount': t.get('amount', 0)
                }
                for t in transactions[:3]  # First 3 transactions
            ]
        
        # Analyze quality
        issues = analyze_extraction_quality(transactions, result['pdf_characteristics'])
        result['issues'] = issues
        result['needs_custom_parser'] = len(issues) > 0 or result['transaction_count'] == 0
        
    except Exception as e:
        result['extraction_status'] = 'error'
        result['issues'].append(f"Parsing error: {str(e)}")
        result['needs_custom_parser'] = True
    
    return result

def extract_bank_name(pdf_path: str) -> str:
    """Extract bank name from filename or content"""
    filename = os.path.basename(pdf_path).lower()
    
    # Common bank name mappings
    bank_mappings = {
        'anz': 'ANZ Bank',
        'commonwealth': 'Commonwealth Bank',
        'westpac': 'Westpac',
        'scotiabank': 'Scotiabank',
        'lloyds': 'Lloyds Bank',
        'nationwide': 'Nationwide',
        'metro bank': 'Metro Bank',
        'becu': 'BECU',
        'citizens': 'Citizens Bank',
        'discover': 'Discover Bank',
        'green dot': 'Green Dot Bank',
        'netspend': 'Netspend',
        'paypal': 'PayPal',
        'suntrust': 'SunTrust',
        'woodforest': 'Woodforest National Bank',
        'walmart': 'Walmart MoneyCard'
    }
    
    for key, name in bank_mappings.items():
        if key in filename:
            return name
    
    # Try to extract from PDF content
    try:
        with pdfplumber.open(pdf_path) as pdf:
            if pdf.pages:
                first_page_text = pdf.pages[0].extract_text()[:500].lower()
                for key, name in bank_mappings.items():
                    if key in first_page_text:
                        return name
    except:
        pass
    
    return 'Unknown Bank'

def get_pdf_characteristics(pdf_path: str) -> Dict:
    """Get characteristics of the PDF"""
    chars = {
        'total_pages': 0,
        'has_tables': False,
        'is_scanned': False,
        'has_forms': False,
        'text_extraction_quality': 'unknown'
    }
    
    try:
        # Check with PyPDF2
        with open(pdf_path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            chars['total_pages'] = len(reader.pages)
            
            # Check if has forms
            if reader.get_form_text_fields():
                chars['has_forms'] = True
        
        # Check with pdfplumber
        with pdfplumber.open(pdf_path) as pdf:
            total_chars = 0
            table_count = 0
            
            for i, page in enumerate(pdf.pages[:3]):  # Check first 3 pages
                # Check text
                text = page.extract_text()
                if text:
                    total_chars += len(text.strip())
                
                # Check tables
                tables = page.extract_tables()
                if tables:
                    table_count += len(tables)
            
            chars['has_tables'] = table_count > 0
            
            # Determine if scanned based on text density
            avg_chars_per_page = total_chars / min(3, len(pdf.pages))
            if avg_chars_per_page < 100:
                chars['is_scanned'] = True
                chars['text_extraction_quality'] = 'poor'
            elif avg_chars_per_page < 500:
                chars['text_extraction_quality'] = 'medium'
            else:
                chars['text_extraction_quality'] = 'good'
    
    except Exception as e:
        chars['error'] = str(e)
    
    return chars

def analyze_extraction_quality(transactions: List[Dict], pdf_chars: Dict) -> List[str]:
    """Analyze the quality of extracted transactions"""
    issues = []
    
    if not transactions:
        issues.append("No transactions extracted")
        return issues
    
    # Check for common issues
    valid_dates = sum(1 for t in transactions if t.get('date'))
    valid_amounts = sum(1 for t in transactions if t.get('amount') is not None)
    valid_descriptions = sum(1 for t in transactions if t.get('description', '').strip())
    
    total = len(transactions)
    
    # Date issues
    if valid_dates < total * 0.9:
        issues.append(f"Missing dates: {total - valid_dates}/{total} transactions")
    
    # Amount issues
    if valid_amounts < total * 0.95:
        issues.append(f"Missing amounts: {total - valid_amounts}/{total} transactions")
    
    # Description issues
    if valid_descriptions < total * 0.8:
        issues.append(f"Missing descriptions: {total - valid_descriptions}/{total} transactions")
    
    # Check for unrealistic amounts
    amounts = [t.get('amount', 0) for t in transactions if t.get('amount') is not None]
    if amounts:
        max_amount = max(abs(a) for a in amounts)
        if max_amount > 1000000:
            issues.append(f"Unrealistic amounts detected (max: ${max_amount:,.2f})")
    
    # Check if extraction count seems too low for page count
    if pdf_chars.get('total_pages', 1) > 1:
        trans_per_page = total / pdf_chars['total_pages']
        if trans_per_page < 5:
            issues.append(f"Low extraction rate: {trans_per_page:.1f} transactions/page")
    
    return issues

def generate_analysis_report(results: List[Dict]) -> str:
    """Generate a comprehensive analysis report"""
    report = []
    report.append("# Bank PDF Analysis Report")
    report.append(f"\nGenerated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Summary
    total_pdfs = len(results)
    successful = sum(1 for r in results if r['extraction_status'] == 'success' and not r['issues'])
    needs_custom = sum(1 for r in results if r['needs_custom_parser'])
    
    report.append("## Summary")
    report.append(f"- Total PDFs analyzed: {total_pdfs}")
    report.append(f"- Successful extractions: {successful}")
    report.append(f"- Needs custom parser: {needs_custom}")
    report.append("")
    
    # Group by bank
    banks = {}
    for result in results:
        bank = result['bank_name']
        if bank not in banks:
            banks[bank] = []
        banks[bank].append(result)
    
    # Detailed analysis by bank
    report.append("## Detailed Analysis by Bank\n")
    
    for bank, bank_results in sorted(banks.items()):
        report.append(f"### {bank}")
        
        for result in bank_results:
            report.append(f"\n**File:** `{result['filename']}`")
            report.append(f"- Status: {result['extraction_status']}")
            report.append(f"- Transactions found: {result['transaction_count']}")
            report.append(f"- Pages: {result['pdf_characteristics'].get('total_pages', 'N/A')}")
            report.append(f"- Has tables: {result['pdf_characteristics'].get('has_tables', False)}")
            report.append(f"- Text quality: {result['pdf_characteristics'].get('text_extraction_quality', 'unknown')}")
            
            if result['issues']:
                report.append(f"- **Issues:**")
                for issue in result['issues']:
                    report.append(f"  - {issue}")
            
            if result['sample_transactions']:
                report.append(f"- **Sample transactions:**")
                for trans in result['sample_transactions']:
                    report.append(f"  - {trans['date']} | {trans['description']} | ${trans['amount']:.2f}")
            
            if result['needs_custom_parser']:
                report.append(f"- **⚠️ NEEDS CUSTOM PARSER**")
        
        report.append("")
    
    return "\n".join(report)

def main():
    """Main analysis function"""
    # List of PDFs to analyze
    pdf_files = [
        "/Users/MAC/Desktop/pdfs/1/Australia ANZ.pdf",
        "/Users/MAC/Desktop/pdfs/1/Australia Commonwealth J C.pdf",
        "/Users/MAC/Desktop/pdfs/1/Australia Westpac bank statement.pdf",
        "/Users/MAC/Desktop/pdfs/1/Canada Scotiabank.pdf",
        "/Users/MAC/Desktop/pdfs/1/UK Lloyds Bank.pdf",
        "/Users/MAC/Desktop/pdfs/1/UK Nationwide word pdf.pdf",
        "/Users/MAC/Desktop/pdfs/1/United Kingdom Metro Bank.pdf",
        "/Users/MAC/Desktop/pdfs/1/USA BECU statement 4 pages.pdf",
        "/Users/MAC/Desktop/pdfs/1/USA Citizens Bank.pdf",
        "/Users/MAC/Desktop/pdfs/1/USA Discover Bank.pdf",
        "/Users/MAC/Desktop/pdfs/1/USA Green Dot Bank Statement 3 page.pdf",
        "/Users/MAC/Desktop/pdfs/1/USA Netspend Bank Statement.pdf",
        "/Users/MAC/Desktop/pdfs/1/USA PayPal Account Statement.pdf",
        "/Users/MAC/Desktop/pdfs/1/USA Suntrust.pdf",
        "/Users/MAC/Desktop/pdfs/1/USA Woodforest.pdf",
        "/Users/MAC/Desktop/pdfs/1/Walmart Money Card Bank Statement 3 page.pdf",
        "/Users/MAC/Desktop/pdfs/example_bank_statement.pdf",
        "/Users/MAC/Desktop/pdfs/merged_statements_2025-07-26.pdf",
        "/Users/MAC/Desktop/pdfs/Bank-Statement-Template-4-TemplateLab.pdf",
        "/Users/MAC/Desktop/pdfs/dummy_statement.pdf",
        "/Users/MAC/Desktop/pdfs/Bank Statement Example Final.pdf"
    ]
    
    print(f"Starting analysis of {len(pdf_files)} PDF files...\n")
    
    results = []
    for i, pdf_path in enumerate(pdf_files):
        print(f"[{i+1}/{len(pdf_files)}] Analyzing: {os.path.basename(pdf_path)}")
        
        if os.path.exists(pdf_path):
            result = analyze_pdf(pdf_path)
            results.append(result)
            
            # Quick status
            status = "✓" if result['extraction_status'] == 'success' and not result['issues'] else "✗"
            print(f"  {status} Found {result['transaction_count']} transactions")
            if result['issues']:
                print(f"  Issues: {', '.join(result['issues'][:2])}")
        else:
            print(f"  ✗ File not found")
            results.append({
                'pdf_path': pdf_path,
                'filename': os.path.basename(pdf_path),
                'bank_name': extract_bank_name(pdf_path),
                'extraction_status': 'file_not_found',
                'transaction_count': 0,
                'issues': ['File not found'],
                'needs_custom_parser': False
            })
        print()
    
    # Generate report
    report = generate_analysis_report(results)
    
    # Save report
    report_path = "BANK_PDF_ANALYSIS_REPORT.md"
    with open(report_path, 'w') as f:
        f.write(report)
    
    print(f"\nAnalysis complete! Report saved to: {report_path}")
    
    # Also save raw results as JSON
    json_path = "bank_pdf_analysis_results.json"
    with open(json_path, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"Raw results saved to: {json_path}")

if __name__ == "__main__":
    main()