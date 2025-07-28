#!/usr/bin/env python3
"""
Test PDF analysis using available parsers
"""

import os
import sys
import json
import tabula
import pdfplumber
import PyPDF2
from datetime import datetime

def analyze_pdf_with_tabula(pdf_path):
    """Use tabula-py to extract tables"""
    results = []
    try:
        # Try different extraction methods
        tables = tabula.read_pdf(pdf_path, pages='all', multiple_tables=True, silent=True)
        
        for i, table in enumerate(tables):
            if not table.empty:
                results.append({
                    'method': 'tabula',
                    'table_num': i,
                    'rows': len(table),
                    'columns': list(table.columns),
                    'sample': table.head(3).to_dict()
                })
    except Exception as e:
        results.append({'method': 'tabula', 'error': str(e)})
    
    return results


def analyze_pdf_with_pdfplumber(pdf_path):
    """Use pdfplumber to extract content"""
    results = []
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages):
                # Extract tables
                tables = page.extract_tables()
                for i, table in enumerate(tables):
                    if table:
                        results.append({
                            'method': 'pdfplumber',
                            'page': page_num + 1,
                            'table_num': i,
                            'rows': len(table),
                            'columns': len(table[0]) if table else 0,
                            'sample': table[:3] if len(table) >= 3 else table
                        })
                
                # Extract text
                text = page.extract_text()
                if text:
                    # Look for transaction patterns
                    lines = text.split('\n')
                    transaction_lines = []
                    for line in lines:
                        # Simple heuristic: lines with dates and amounts
                        if any(char.isdigit() for char in line) and ('.' in line or '$' in line or '£' in line):
                            transaction_lines.append(line)
                    
                    if transaction_lines:
                        results.append({
                            'method': 'pdfplumber_text',
                            'page': page_num + 1,
                            'potential_transactions': len(transaction_lines),
                            'sample': transaction_lines[:3]
                        })
                        
    except Exception as e:
        results.append({'method': 'pdfplumber', 'error': str(e)})
    
    return results


def analyze_single_pdf(pdf_path):
    """Comprehensive analysis of a single PDF"""
    print(f"\n{'='*80}")
    print(f"Analyzing: {os.path.basename(pdf_path)}")
    print(f"{'='*80}")
    
    if not os.path.exists(pdf_path):
        print("ERROR: File not found!")
        return None
    
    # Basic info
    try:
        with open(pdf_path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            num_pages = len(reader.pages)
            print(f"Pages: {num_pages}")
    except Exception as e:
        print(f"Error reading PDF: {e}")
        return None
    
    # Try tabula
    print("\nTabula-py Results:")
    tabula_results = analyze_pdf_with_tabula(pdf_path)
    for result in tabula_results:
        if 'error' in result:
            print(f"  Error: {result['error']}")
        else:
            print(f"  Table {result['table_num']}: {result['rows']} rows, columns: {result['columns']}")
            if result['sample']:
                print(f"  Sample: {json.dumps(result['sample'], indent=2)[:200]}...")
    
    # Try pdfplumber
    print("\nPDFPlumber Results:")
    plumber_results = analyze_pdf_with_pdfplumber(pdf_path)
    for result in plumber_results:
        if 'error' in result:
            print(f"  Error: {result['error']}")
        else:
            if result['method'] == 'pdfplumber':
                print(f"  Page {result['page']}, Table {result['table_num']}: {result['rows']} rows")
                if result['sample']:
                    print(f"  First row: {result['sample'][0][:5] if result['sample'][0] else 'Empty'}")
            else:
                print(f"  Page {result['page']}: {result['potential_transactions']} potential transactions")
                for line in result['sample'][:2]:
                    print(f"    {line}")
    
    return {
        'filename': os.path.basename(pdf_path),
        'pages': num_pages,
        'tabula_results': tabula_results,
        'plumber_results': plumber_results
    }


def main():
    # Test key PDFs
    test_pdfs = [
        "/Users/MAC/Desktop/pdfs/1/USA Bank of America.pdf",
        "/Users/MAC/Desktop/pdfs/1/USA Wells Fargo 7 pages.pdf",
        "/Users/MAC/Desktop/pdfs/1/Canada RBC.pdf",
        "/Users/MAC/Desktop/pdfs/1/Australia Commonwealth J C.pdf",
        "/Users/MAC/Desktop/pdfs/dummy_statement.pdf"
    ]
    
    all_results = []
    
    for pdf_path in test_pdfs:
        result = analyze_single_pdf(pdf_path)
        if result:
            all_results.append(result)
    
    # Summary
    print(f"\n{'='*80}")
    print("SUMMARY")
    print(f"{'='*80}")
    print(f"Analyzed {len(all_results)} PDFs")
    
    # Count successes
    tabula_success = sum(1 for r in all_results 
                        for t in r['tabula_results'] 
                        if 'error' not in t)
    plumber_success = sum(1 for r in all_results 
                         for p in r['plumber_results'] 
                         if 'error' not in p)
    
    print(f"Tabula extracted tables: {tabula_success}")
    print(f"PDFPlumber extracted data: {plumber_success}")
    
    # Save results
    with open('pdf_extraction_analysis.json', 'w') as f:
        json.dump(all_results, f, indent=2, default=str)
    print(f"\nDetailed results saved to: pdf_extraction_analysis.json")


if __name__ == "__main__":
    main()