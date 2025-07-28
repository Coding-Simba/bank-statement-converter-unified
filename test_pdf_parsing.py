#!/usr/bin/env python3
"""
Test PDF parsing for bank statements
"""

import os
import sys
import PyPDF2
import pandas as pd
from datetime import datetime

# Add backend to path
backend_path = os.path.join(os.path.dirname(__file__), 'backend')
sys.path.insert(0, backend_path)

# Import the parser
try:
    from universal_parser import UniversalParser
    parser_available = True
except ImportError as e:
    print(f"Failed to import UniversalParser: {e}")
    parser_available = False

def quick_test_pdf(pdf_path):
    """Quick test of PDF parsing"""
    print(f"\n{'='*60}")
    print(f"Testing: {os.path.basename(pdf_path)}")
    print(f"{'='*60}")
    
    if not os.path.exists(pdf_path):
        print(f"ERROR: File not found!")
        return
    
    # Basic PDF info
    try:
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            num_pages = len(pdf_reader.pages)
            print(f"Pages: {num_pages}")
            
            # Get first page text sample
            if num_pages > 0:
                first_page_text = pdf_reader.pages[0].extract_text()
                print(f"First 200 chars: {first_page_text[:200].replace(chr(10), ' ')}")
    except Exception as e:
        print(f"ERROR reading PDF: {e}")
        return
    
    # Try parsing with UniversalParser
    if parser_available:
        try:
            parser = UniversalParser()
            transactions = parser.extract_transactions(pdf_path)
            
            print(f"\nParsing Results:")
            print(f"Transactions found: {len(transactions)}")
            
            if transactions:
                # Show first few transactions
                print(f"\nFirst 3 transactions:")
                for i, trans in enumerate(transactions[:3]):
                    print(f"\nTransaction {i+1}:")
                    for key, value in trans.items():
                        print(f"  {key}: {value}")
                
                # Summary statistics
                dates = [t.get('date') for t in transactions if t.get('date')]
                amounts = [t.get('amount', 0) for t in transactions if isinstance(t.get('amount'), (int, float))]
                
                if dates:
                    print(f"\nDate range: {min(dates)} to {max(dates)}")
                if amounts:
                    print(f"Total amount: ${sum(amounts):,.2f}")
                    print(f"Transaction count: {len(amounts)}")
            else:
                print("No transactions extracted!")
                
        except Exception as e:
            print(f"\nERROR during parsing: {e}")
            import traceback
            traceback.print_exc()
    else:
        print("\nUniversalParser not available - check imports")


def main():
    # Test a few key PDFs first
    test_pdfs = [
        "/Users/MAC/Desktop/pdfs/1/USA Bank of America.pdf",
        "/Users/MAC/Desktop/pdfs/1/USA Wells Fargo 7 pages.pdf",
        "/Users/MAC/Desktop/pdfs/1/Canada RBC.pdf",
        "/Users/MAC/Desktop/pdfs/dummy_statement.pdf"
    ]
    
    for pdf_path in test_pdfs:
        quick_test_pdf(pdf_path)
    
    print(f"\n{'='*60}")
    print("Testing complete!")


if __name__ == "__main__":
    main()