#!/usr/bin/env python3
"""
Analyze bank PDFs to identify parsing issues and document findings
"""

import os
import sys
import json
import PyPDF2
import pandas as pd
from datetime import datetime
from pathlib import Path

# Add backend directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

try:
    from universal_parser import UniversalParser
except ImportError:
    print("Warning: Could not import UniversalParser")
    UniversalParser = None

class PDFAnalyzer:
    def __init__(self):
        self.results = {}
        self.parser = UniversalParser() if UniversalParser else None
        
    def analyze_pdf_structure(self, pdf_path):
        """Analyze PDF structure and content"""
        analysis = {
            'file_name': os.path.basename(pdf_path),
            'file_size': os.path.getsize(pdf_path),
            'pages': 0,
            'text_length': 0,
            'has_tables': False,
            'date_formats_found': [],
            'amount_formats_found': [],
            'potential_issues': []
        }
        
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                analysis['pages'] = len(pdf_reader.pages)
                
                # Extract text from all pages
                full_text = ""
                for page_num in range(len(pdf_reader.pages)):
                    page = pdf_reader.pages[page_num]
                    text = page.extract_text()
                    full_text += text + "\n"
                
                analysis['text_length'] = len(full_text)
                
                # Check for common table indicators
                table_indicators = ['Date', 'Description', 'Amount', 'Balance', 
                                  'Debit', 'Credit', 'Transaction', 'Reference']
                for indicator in table_indicators:
                    if indicator.lower() in full_text.lower():
                        analysis['has_tables'] = True
                        break
                
                # Find date patterns
                import re
                date_patterns = [
                    (r'\d{1,2}/\d{1,2}/\d{2,4}', 'MM/DD/YYYY or DD/MM/YYYY'),
                    (r'\d{1,2}-\d{1,2}-\d{2,4}', 'MM-DD-YYYY or DD-MM-YYYY'),
                    (r'\d{4}-\d{1,2}-\d{1,2}', 'YYYY-MM-DD'),
                    (r'\d{1,2}-[A-Za-z]{3}-\d{2,4}', 'DD-MMM-YYYY'),
                    (r'[A-Za-z]{3} \d{1,2}, \d{4}', 'MMM DD, YYYY')
                ]
                
                for pattern, format_name in date_patterns:
                    if re.search(pattern, full_text):
                        analysis['date_formats_found'].append(format_name)
                
                # Find amount patterns
                amount_patterns = [
                    (r'\$[\d,]+\.\d{2}', 'USD with $'),
                    (r'£[\d,]+\.\d{2}', 'GBP with £'),
                    (r'[\d,]+\.\d{2} USD', 'USD suffix'),
                    (r'\([\d,]+\.\d{2}\)', 'Negative in parentheses'),
                    (r'-[\d,]+\.\d{2}', 'Negative with minus'),
                    (r'[\d,]+\.\d{2} CR', 'Credit indicator'),
                    (r'[\d,]+\.\d{2} DR', 'Debit indicator')
                ]
                
                for pattern, format_name in amount_patterns:
                    if re.search(pattern, full_text):
                        analysis['amount_formats_found'].append(format_name)
                
                # Check for potential issues
                if not analysis['has_tables']:
                    analysis['potential_issues'].append("No table headers found")
                if analysis['text_length'] < 100:
                    analysis['potential_issues'].append("Very little text extracted")
                if not analysis['date_formats_found']:
                    analysis['potential_issues'].append("No date patterns found")
                if not analysis['amount_formats_found']:
                    analysis['potential_issues'].append("No amount patterns found")
                    
        except Exception as e:
            analysis['error'] = str(e)
            analysis['potential_issues'].append(f"Error reading PDF: {e}")
            
        return analysis
    
    def parse_with_universal_parser(self, pdf_path):
        """Try parsing with UniversalParser and analyze results"""
        if not self.parser:
            return {'error': 'UniversalParser not available'}
            
        try:
            transactions = self.parser.extract_transactions(pdf_path)
            
            result = {
                'transactions_found': len(transactions),
                'has_dates': any('date' in t for t in transactions),
                'has_descriptions': any('description' in t for t in transactions),
                'has_amounts': any('amount' in t for t in transactions),
                'sample_transactions': transactions[:3] if transactions else [],
                'date_range': None,
                'total_amount': None
            }
            
            if transactions:
                # Get date range
                dates = [t.get('date') for t in transactions if t.get('date')]
                if dates:
                    result['date_range'] = {
                        'start': min(dates).strftime('%Y-%m-%d') if hasattr(min(dates), 'strftime') else str(min(dates)),
                        'end': max(dates).strftime('%Y-%m-%d') if hasattr(max(dates), 'strftime') else str(max(dates))
                    }
                
                # Calculate total
                amounts = [t.get('amount', 0) for t in transactions if isinstance(t.get('amount'), (int, float))]
                if amounts:
                    result['total_amount'] = sum(amounts)
                    
            return result
            
        except Exception as e:
            return {'error': str(e)}
    
    def analyze_pdf(self, pdf_path):
        """Complete analysis of a single PDF"""
        print(f"\nAnalyzing: {os.path.basename(pdf_path)}")
        print("-" * 50)
        
        # Structure analysis
        structure = self.analyze_pdf_structure(pdf_path)
        print(f"Pages: {structure['pages']}")
        print(f"Text length: {structure['text_length']} characters")
        print(f"Has tables: {structure['has_tables']}")
        print(f"Date formats: {', '.join(structure['date_formats_found']) or 'None found'}")
        print(f"Amount formats: {', '.join(structure['amount_formats_found']) or 'None found'}")
        
        # Parser analysis
        parser_result = self.parse_with_universal_parser(pdf_path)
        if 'error' not in parser_result:
            print(f"\nParser Results:")
            print(f"Transactions found: {parser_result['transactions_found']}")
            print(f"Has dates: {parser_result['has_dates']}")
            print(f"Has descriptions: {parser_result['has_descriptions']}")
            print(f"Has amounts: {parser_result['has_amounts']}")
            if parser_result['date_range']:
                print(f"Date range: {parser_result['date_range']['start']} to {parser_result['date_range']['end']}")
            if parser_result['total_amount'] is not None:
                print(f"Total amount: ${parser_result['total_amount']:,.2f}")
        else:
            print(f"\nParser error: {parser_result['error']}")
        
        # Potential issues
        if structure['potential_issues']:
            print(f"\nPotential issues:")
            for issue in structure['potential_issues']:
                print(f"  - {issue}")
        
        # Store results
        self.results[pdf_path] = {
            'structure': structure,
            'parser': parser_result
        }
        
        return structure, parser_result
    
    def generate_report(self, output_file='pdf_analysis_report.json'):
        """Generate analysis report"""
        report = {
            'analysis_date': datetime.now().isoformat(),
            'total_files': len(self.results),
            'results': self.results,
            'summary': {
                'successful_parses': 0,
                'failed_parses': 0,
                'files_with_issues': 0
            }
        }
        
        for path, result in self.results.items():
            if 'error' not in result['parser']:
                report['summary']['successful_parses'] += 1
            else:
                report['summary']['failed_parses'] += 1
                
            if result['structure']['potential_issues']:
                report['summary']['files_with_issues'] += 1
        
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)
            
        print(f"\nReport saved to: {output_file}")
        return report


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
    
    analyzer = PDFAnalyzer()
    
    # Analyze each PDF
    for pdf_path in pdf_files:
        if os.path.exists(pdf_path):
            try:
                analyzer.analyze_pdf(pdf_path)
            except Exception as e:
                print(f"\nError analyzing {pdf_path}: {e}")
        else:
            print(f"\nFile not found: {pdf_path}")
    
    # Generate report
    analyzer.generate_report()
    
    # Summary
    print("\n" + "=" * 50)
    print("ANALYSIS SUMMARY")
    print("=" * 50)
    print(f"Total PDFs analyzed: {len(analyzer.results)}")
    
    successful = sum(1 for r in analyzer.results.values() if 'error' not in r['parser'])
    print(f"Successfully parsed: {successful}")
    print(f"Failed to parse: {len(analyzer.results) - successful}")
    
    # Files needing attention
    print("\nFiles needing attention:")
    for path, result in analyzer.results.items():
        issues = []
        if 'error' in result['parser']:
            issues.append("Parser error")
        if result['parser'].get('transactions_found', 0) == 0:
            issues.append("No transactions found")
        if result['structure']['potential_issues']:
            issues.extend(result['structure']['potential_issues'])
            
        if issues:
            print(f"\n{os.path.basename(path)}:")
            for issue in issues:
                print(f"  - {issue}")


if __name__ == "__main__":
    main()