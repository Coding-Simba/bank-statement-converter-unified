#!/usr/bin/env python3
"""
Comprehensive PDF analysis for all bank statements
"""

import os
import sys
import json
import pandas as pd
from datetime import datetime
import importlib
import re

# Add backend to path
backend_path = os.path.join(os.path.dirname(__file__), 'backend')
sys.path.insert(0, backend_path)

# Import specific parsers
parsers = {}
parser_modules = [
    ('boa_parser', 'BOAParser', ['bank of america', 'bofa', 'boa']),
    ('wells_fargo_parser', 'WellsFargoParser', ['wells fargo', 'wells']),
    ('citizens_parser', 'CitizensParser', ['citizens bank', 'citizens']),
    ('pnc_parser', 'PNCParser', ['pnc bank', 'pnc']),
    ('navy_federal_parser', 'NavyFederalParser', ['navy federal', 'nfcu']),
    ('dcu_parser', 'DCUParser', ['dcu', 'digital federal']),
    ('usaa_parser', 'USAAParser', ['usaa']),
    ('becu_parser', 'BECUParser', ['becu', 'boeing employees']),
    ('paypal_parser', 'PayPalParser', ['paypal']),
    ('rbc_parser', 'RBCParser', ['rbc', 'royal bank']),
    ('westpac_parser', 'WestpacParser', ['westpac']),
    ('bendigo_parser', 'BendigoParser', ['bendigo']),
    ('commonwealth_parser', 'CommonwealthParser', ['commonwealth']),
    ('metro_parser', 'MetroParser', ['metro bank']),
    ('nationwide_parser', 'NationwideParser', ['nationwide']),
    ('woodforest_parser', 'WoodforestParser', ['woodforest'])
]

# Try to import each parser
for module_name, class_name, keywords in parser_modules:
    try:
        module = importlib.import_module(module_name)
        parser_class = getattr(module, class_name)
        for keyword in keywords:
            parsers[keyword] = parser_class
        print(f"✓ Loaded {class_name}")
    except (ImportError, AttributeError) as e:
        print(f"✗ Failed to load {class_name}: {e}")

# Import the universal parser if available
try:
    from pdf_parser import PDFParser
    universal_parser = PDFParser()
    print("✓ Loaded universal PDFParser")
except ImportError:
    universal_parser = None
    print("✗ Universal PDFParser not available")


def detect_bank(filename, pdf_text=""):
    """Detect bank from filename or content"""
    filename_lower = filename.lower()
    text_lower = pdf_text.lower()
    
    # Check each bank keyword
    bank_keywords = [
        ('bank of america', ['bank of america', 'bofa']),
        ('wells fargo', ['wells fargo']),
        ('citizens bank', ['citizens bank']),
        ('pnc bank', ['pnc']),
        ('navy federal', ['navy federal', 'nfcu']),
        ('dcu', ['dcu', 'digital federal']),
        ('usaa', ['usaa']),
        ('becu', ['becu', 'boeing employees']),
        ('paypal', ['paypal']),
        ('rbc', ['rbc', 'royal bank']),
        ('westpac', ['westpac']),
        ('bendigo', ['bendigo']),
        ('commonwealth', ['commonwealth']),
        ('metro bank', ['metro bank']),
        ('nationwide', ['nationwide']),
        ('woodforest', ['woodforest'])
    ]
    
    for bank_name, keywords in bank_keywords:
        for keyword in keywords:
            if keyword in filename_lower or keyword in text_lower:
                return bank_name
    
    return None


def analyze_pdf(pdf_path):
    """Analyze a single PDF"""
    result = {
        'filename': os.path.basename(pdf_path),
        'path': pdf_path,
        'detected_bank': None,
        'parser_used': None,
        'transactions_found': 0,
        'parsing_success': False,
        'error': None,
        'sample_data': None
    }
    
    # Try to detect bank
    try:
        # Read first page for bank detection
        import PyPDF2
        with open(pdf_path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            first_page_text = reader.pages[0].extract_text() if reader.pages else ""
            result['detected_bank'] = detect_bank(result['filename'], first_page_text)
    except Exception as e:
        print(f"Error reading PDF: {e}")
    
    # Try specific parser first
    if result['detected_bank'] and result['detected_bank'] in parsers:
        parser_class = parsers[result['detected_bank']]
        try:
            parser = parser_class()
            transactions = parser.extract_transactions(pdf_path)
            result['parser_used'] = parser_class.__name__
            result['transactions_found'] = len(transactions)
            result['parsing_success'] = len(transactions) > 0
            
            if transactions:
                result['sample_data'] = {
                    'first_transaction': transactions[0],
                    'last_transaction': transactions[-1],
                    'total_transactions': len(transactions)
                }
        except Exception as e:
            result['error'] = f"Specific parser error: {str(e)}"
    
    # Fall back to universal parser
    if not result['parsing_success'] and universal_parser:
        try:
            transactions = universal_parser.extract_transactions(pdf_path)
            result['parser_used'] = 'UniversalParser'
            result['transactions_found'] = len(transactions)
            result['parsing_success'] = len(transactions) > 0
            
            if transactions:
                result['sample_data'] = {
                    'first_transaction': transactions[0],
                    'last_transaction': transactions[-1],
                    'total_transactions': len(transactions)
                }
        except Exception as e:
            result['error'] = f"Universal parser error: {str(e)}"
    
    return result


def main():
    # PDF files to analyze
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
        "/Users/MAC/Desktop/pdfs/1/USA Navy Federal 5 pages.pdf",
        "/Users/MAC/Desktop/pdfs/1/USA DCU Bank Statement 5 page.pdf",
        "/Users/MAC/Desktop/pdfs/1/USA PayPal Account Statement.pdf",
        "/Users/MAC/Desktop/pdfs/1/USAA Bank Statement 5 page .pdf",
        "/Users/MAC/Desktop/pdfs/1/USA BECU statement 4 pages.pdf",
        "/Users/MAC/Desktop/pdfs/1/USA Wells Fargo 7 pages.pdf",
        "/Users/MAC/Desktop/pdfs/1/USA Bank of America.pdf",
        "/Users/MAC/Desktop/pdfs/1/Australia Commonwealth J C.pdf",
        "/Users/MAC/Desktop/pdfs/merged_statements_2025-07-26.pdf",
        "/Users/MAC/Desktop/pdfs/Bank-Statement-Template-4-TemplateLab.pdf",
        "/Users/MAC/Desktop/pdfs/dummy_statement.pdf",
        "/Users/MAC/Desktop/pdfs/Bank Statement Example Final.pdf"
    ]
    
    results = []
    
    print("\n" + "="*80)
    print("ANALYZING BANK STATEMENT PDFs")
    print("="*80 + "\n")
    
    for pdf_path in pdf_files:
        if os.path.exists(pdf_path):
            print(f"\nAnalyzing: {os.path.basename(pdf_path)}")
            print("-" * 60)
            
            result = analyze_pdf(pdf_path)
            results.append(result)
            
            print(f"Detected Bank: {result['detected_bank'] or 'Unknown'}")
            print(f"Parser Used: {result['parser_used'] or 'None'}")
            print(f"Transactions Found: {result['transactions_found']}")
            print(f"Success: {'✓' if result['parsing_success'] else '✗'}")
            
            if result['error']:
                print(f"Error: {result['error']}")
                
            if result['sample_data']:
                print(f"First transaction date: {result['sample_data']['first_transaction'].get('date', 'N/A')}")
        else:
            print(f"\nFile not found: {pdf_path}")
            results.append({
                'filename': os.path.basename(pdf_path),
                'path': pdf_path,
                'error': 'File not found'
            })
    
    # Summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    
    successful = sum(1 for r in results if r.get('parsing_success', False))
    total = len(results)
    
    print(f"\nTotal PDFs: {total}")
    print(f"Successfully parsed: {successful} ({successful/total*100:.1f}%)")
    print(f"Failed: {total - successful}")
    
    print("\nFailed PDFs:")
    for r in results:
        if not r.get('parsing_success', False):
            print(f"  - {r['filename']}: {r.get('error', 'No transactions found')}")
    
    # Save detailed report
    report_path = 'pdf_analysis_detailed_report.json'
    with open(report_path, 'w') as f:
        json.dump({
            'analysis_date': datetime.now().isoformat(),
            'summary': {
                'total_pdfs': total,
                'successful': successful,
                'failed': total - successful,
                'success_rate': successful/total if total > 0 else 0
            },
            'results': results
        }, f, indent=2, default=str)
    
    print(f"\nDetailed report saved to: {report_path}")


if __name__ == "__main__":
    main()