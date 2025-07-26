#!/usr/bin/env python3
"""Test PDF format detection"""

import sys
sys.path.append('.')

import PyPDF2

pdf_path = "/Users/MAC/Downloads/dummy_statement.pdf"

with open(pdf_path, 'rb') as file:
    pdf_reader = PyPDF2.PdfReader(file)
    if len(pdf_reader.pages) > 0:
        first_page = pdf_reader.pages[0].extract_text()
        
        print("First page text:")
        print("-" * 50)
        print(first_page[:500])
        print("-" * 50)
        
        print("\nChecking conditions:")
        print(f"'SAMPLE' in first_page: {'SAMPLE' in first_page}")
        print(f"'Statement of Account' in first_page: {'Statement of Account' in first_page}")
        print(f"'JAMES C. MORRISON' in first_page: {'JAMES C. MORRISON' in first_page}")
        
        all_conditions = 'SAMPLE' in first_page and 'Statement of Account' in first_page and 'JAMES C. MORRISON' in first_page
        print(f"\nAll conditions met: {all_conditions}")