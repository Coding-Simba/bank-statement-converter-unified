#!/usr/bin/env python3
"""Test the complete PDF parsing system with various PDFs"""

import sys
sys.path.append('.')

from backend.universal_parser import parse_universal_pdf

# Test PDFs
test_pdfs = [
    ("/Users/MAC/Downloads/dummy_statement.pdf", "Dummy Statement"),
    ("/Users/MAC/Downloads/merged_statements_2025-07-26.pdf", "Merged Statements")
]

for pdf_path, name in test_pdfs:
    print(f"\n{'='*70}")
    print(f"Testing: {name}")
    print(f"File: {pdf_path}")
    print('='*70)
    
    try:
        transactions = parse_universal_pdf(pdf_path)
        
        print(f"\nTotal transactions found: {len(transactions)}")
        
        if transactions:
            # Show first 5 transactions
            print("\nFirst 5 transactions:")
            for i, trans in enumerate(transactions[:5]):
                date_str = trans.get('date_string', trans.get('date', 'No date'))
                if hasattr(date_str, 'strftime'):
                    date_str = date_str.strftime('%Y-%m-%d')
                desc = trans.get('description', 'No description')[:50]
                amount = trans.get('amount', 0.0)
                print(f"{i+1}. {str(date_str)[:10]:10} | {desc:50} | ${amount:>10.2f}")
            
            if len(transactions) > 5:
                print(f"... and {len(transactions) - 5} more transactions")
            
            # Summary
            total_credits = sum(t.get('amount', 0) for t in transactions if t.get('amount', 0) > 0)
            total_debits = sum(t.get('amount', 0) for t in transactions if t.get('amount', 0) < 0)
            
            print(f"\nSummary:")
            print(f"Total credits: ${total_credits:,.2f}")
            print(f"Total debits: ${total_debits:,.2f}")
            print(f"Net: ${total_credits + total_debits:,.2f}")
        else:
            print("\nNo transactions found!")
            
    except FileNotFoundError:
        print(f"File not found: {pdf_path}")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

print("\n" + "="*70)
print("Testing complete!")