#!/usr/bin/env python3
"""Check all pages of the PDF for any transaction data"""

import pdfplumber
import PyPDF2
import re

pdf_path = "/Users/MAC/Downloads/merged_statements_2025-07-26.pdf"

print("Checking ALL pages of the PDF...")
print("-" * 60)

# First, let's check with PyPDF2
print("\n1. PyPDF2 Analysis:")
with open(pdf_path, 'rb') as file:
    pdf_reader = PyPDF2.PdfReader(file)
    total_pages = len(pdf_reader.pages)
    print(f"Total pages: {total_pages}")
    
    # Check each page
    for page_num in range(total_pages):
        text = pdf_reader.pages[page_num].extract_text()
        
        # Count numeric content
        numbers = re.findall(r'\d+[.,]?\d*', text)
        dates = re.findall(r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{4}[/-]\d{1,2}[/-]\d{1,2}', text)
        amounts = re.findall(r'\d+[.,]\d{2}', text)
        
        if numbers or dates or amounts:
            print(f"\nPage {page_num + 1}:")
            print(f"  - Numbers found: {len(numbers)}")
            print(f"  - Date patterns: {len(dates)}")
            print(f"  - Amount patterns: {len(amounts)}")
            
            if dates:
                print(f"  - Sample dates: {dates[:5]}")
            if amounts:
                print(f"  - Sample amounts: {amounts[:5]}")
            
            # Show lines with potential transaction data
            lines = text.split('\n')
            print(f"  - Lines with numbers:")
            for line in lines:
                if re.search(r'\d{2,}', line) and len(line) > 10:
                    print(f"    {line[:100]}")

# Now with pdfplumber for more detailed extraction
print("\n\n2. PDFPlumber Analysis:")
with pdfplumber.open(pdf_path) as pdf:
    for page_num, page in enumerate(pdf.pages):
        # Extract tables
        tables = page.extract_tables()
        
        # Extract text
        text = page.extract_text()
        
        # Look for transaction-like patterns
        if text:
            lines = text.split('\n')
            transaction_lines = []
            
            for line in lines:
                # Look for lines that might be transactions (date + description + amount)
                if re.search(r'\d', line) and len(line) > 20:
                    # Check if line has both text and numbers
                    has_letters = any(c.isalpha() for c in line)
                    has_numbers = any(c.isdigit() for c in line)
                    if has_letters and has_numbers:
                        transaction_lines.append(line)
            
            if transaction_lines or (tables and any(len(t) > 2 for t in tables)):
                print(f"\nPage {page_num + 1}:")
                print(f"  - Tables found: {len(tables)}")
                if tables:
                    for i, table in enumerate(tables):
                        if len(table) > 2:  # More than just headers
                            print(f"  - Table {i+1} has {len(table)} rows")
                
                if transaction_lines:
                    print(f"  - Potential transaction lines: {len(transaction_lines)}")
                    print("  - Samples:")
                    for line in transaction_lines[:10]:
                        print(f"    {line}")

print("\n\n3. File Summary:")
import os
file_size = os.path.getsize(pdf_path)
print(f"File size: {file_size:,} bytes ({file_size/1024/1024:.2f} MB)")
print(f"Total pages: {total_pages}")
print(f"Average bytes per page: {file_size/total_pages:,.0f}")

# Check if this might be a scanned PDF
with pdfplumber.open(pdf_path) as pdf:
    page = pdf.pages[0]
    words = page.extract_words()
    chars = page.chars if hasattr(page, 'chars') else []
    print(f"\nFirst page analysis:")
    print(f"- Words extracted: {len(words)}")
    print(f"- Characters extracted: {len(chars)}")
    print(f"- Might be scanned: {'Yes' if len(words) < 10 else 'No'}")