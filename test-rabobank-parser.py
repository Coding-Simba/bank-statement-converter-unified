#!/usr/bin/env python3
"""Test script to debug Rabobank PDF parsing"""

import os
import sys
sys.path.append('backend')

import importlib.util
spec = importlib.util.spec_from_file_location("split_by_date", "backend/split-by-date.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
extract_transactions_from_pdf = module.extract_transactions_from_pdf
parse_date = module.parse_date
import json

def test_pdf_extraction(pdf_path):
    """Test PDF extraction with detailed output"""
    print(f"Testing PDF: {pdf_path}")
    print("-" * 50)
    
    if not os.path.exists(pdf_path):
        print(f"ERROR: File not found: {pdf_path}")
        return
    
    # Extract transactions
    transactions = extract_transactions_from_pdf(pdf_path)
    
    print(f"Total transactions found: {len(transactions)}")
    
    if transactions:
        print("\nFirst 5 transactions:")
        for i, trans in enumerate(transactions[:5]):
            print(f"\nTransaction {i+1}:")
            print(f"  Date: {trans.get('date_string')} -> {trans.get('date')}")
            print(f"  Description: {trans.get('description', 'N/A')}")
            print(f"  Amount: {trans.get('amount_string')} -> {trans.get('amount')}")
        
        # Date range
        dates = [t['date'] for t in transactions if t.get('date')]
        if dates:
            print(f"\nDate range: {min(dates)} to {max(dates)}")
    else:
        print("\nNo transactions found. Let's debug...")
        
        # Try to extract raw text
        try:
            import PyPDF2
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                print(f"\nPDF has {len(pdf_reader.pages)} pages")
                
                # Show first page text
                if len(pdf_reader.pages) > 0:
                    text = pdf_reader.pages[0].extract_text()
                    print("\nFirst 500 characters of page 1:")
                    print(text[:500])
        except Exception as e:
            print(f"Error reading PDF: {e}")

if __name__ == "__main__":
    # Get PDF file path from command line or use default
    if len(sys.argv) > 1:
        pdf_path = sys.argv[1]
    else:
        pdf_path = "RA_A_NL13RABO0122118650_EUR_202506.pdf"
    
    test_pdf_extraction(pdf_path)