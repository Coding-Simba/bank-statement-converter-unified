#!/usr/bin/env python3
"""Test PDF parser with example bank statement"""

from backend.universal_parser import parse_universal_pdf
import json

pdf_path = './uploads/b354da97-b72c-4aae-9339-a5bf33f2212b.pdf'
print(f'Testing PDF: {pdf_path}')
print('=' * 50)

try:
    transactions = parse_universal_pdf(pdf_path)
    print(f'\nExtracted {len(transactions)} transactions')
    print('\nFirst 5 transactions:')
    for i, trans in enumerate(transactions[:5]):
        print(f'\n{i+1}. Date: {trans.get("date_string", "N/A")}')
        print(f'   Description: {trans.get("description", "N/A")}')
        print(f'   Amount: ${trans.get("amount", 0):.2f}')
        
    # Show if any headers were captured
    print('\n\nChecking for header/non-transaction content:')
    for trans in transactions:
        desc = trans.get('description', '').lower()
        if any(word in desc for word in ['bank', 'america', 'p.o.', 'box', 'statement', 'account', 'issue', 'period']):
            print(f'HEADER FOUND: {trans.get("description")} - ${trans.get("amount", 0):.2f}')
            
except Exception as e:
    print(f'Error: {e}')
    import traceback
    traceback.print_exc()