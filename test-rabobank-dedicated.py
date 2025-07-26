#!/usr/bin/env python3
"""Test the dedicated Rabobank parser"""

import sys
sys.path.append('backend')

from rabobank_parser import parse_rabobank_pdf

def test_parser(pdf_path):
    print(f"Testing Rabobank parser on: {pdf_path}")
    print("-" * 50)
    
    transactions = parse_rabobank_pdf(pdf_path)
    
    print(f"Total transactions found: {len(transactions)}")
    
    if transactions:
        print("\nFirst 10 transactions:")
        for i, trans in enumerate(transactions[:10]):
            print(f"\nTransaction {i+1}:")
            print(f"  Date: {trans.get('date_string')} -> {trans.get('date')}")
            print(f"  Type: {trans.get('type')}")
            print(f"  Description: {trans.get('description', 'N/A')}")
            print(f"  Amount: {trans.get('amount_string')} -> €{trans.get('amount')}")
        
        # Summary
        total_debit = sum(t['amount'] for t in transactions if t['amount'] < 0)
        total_credit = sum(t['amount'] for t in transactions if t['amount'] > 0)
        
        print(f"\nSummary:")
        print(f"  Total debits: €{total_debit:.2f}")
        print(f"  Total credits: €{total_credit:.2f}")
        print(f"  Net: €{(total_credit + total_debit):.2f}")

if __name__ == "__main__":
    pdf_path = sys.argv[1] if len(sys.argv) > 1 else "~/Downloads/RA_A_NL13RABO0122118650_EUR_202506.pdf"
    test_parser(pdf_path)