#!/usr/bin/env python3
"""Test Huntington parser directly"""

import sys
sys.path.append('backend')

from huntington_parser import parse_huntington

pdf_path = '/Users/MAC/Desktop/pdfs/1/USA Ohio Huntington bank statement 7  page.pdf'
print(f"Testing Huntington parser on: {pdf_path}")

transactions = parse_huntington(pdf_path)
print(f"\nFound {len(transactions)} transactions")

if transactions:
    print("\nFirst 10 transactions:")
    for i, trans in enumerate(transactions[:10]):
        date_str = trans.get('date').strftime('%Y-%m-%d') if trans.get('date') else trans.get('date_string', 'No date')
        desc = trans.get('description', 'No description')[:50]
        amount = trans.get('amount', 'No amount')
        print(f"  {i+1}. {date_str} | {desc:<50} | ${amount:>10.2f}")
    
    if len(transactions) > 10:
        print(f"\n... and {len(transactions) - 10} more transactions")
    
    # Summary
    total_credits = sum(t['amount'] for t in transactions if t.get('amount', 0) > 0)
    total_debits = sum(t['amount'] for t in transactions if t.get('amount', 0) < 0)
    print(f"\nSummary:")
    print(f"  Total credits: ${total_credits:,.2f}")
    print(f"  Total debits: ${total_debits:,.2f}")
    print(f"  Net: ${total_credits + total_debits:,.2f}")
else:
    print("\nNo transactions found. Checking PDF content...")
    
    import pdfplumber
    with pdfplumber.open(pdf_path) as pdf:
        print(f"\nPDF has {len(pdf.pages)} pages")
        
        # Show first page content
        first_page = pdf.pages[0]
        text = first_page.extract_text()
        if text:
            print("\nFirst 1000 chars of page 1:")
            print("-" * 80)
            print(text[:1000])
            print("-" * 80)