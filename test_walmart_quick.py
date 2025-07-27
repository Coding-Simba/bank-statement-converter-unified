#!/usr/bin/env python3
"""Quick test for Walmart detection"""

import PyPDF2

pdf_path = '/Users/MAC/Desktop/pdfs/1/Walmart Money Card Bank Statement 3 page.pdf'

with open(pdf_path, 'rb') as file:
    pdf_reader = PyPDF2.PdfReader(file)
    if len(pdf_reader.pages) > 0:
        first_page = pdf_reader.pages[0].extract_text()
        print("First page text sample:")
        print(first_page[:500])
        print("\nChecking for 'walmart':", 'walmart' in first_page.lower())
        print("Checking for 'money card':", 'money card' in first_page.lower())