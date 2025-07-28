#!/usr/bin/env python3
import sys
sys.path.insert(0, '.')
from backend.pymupdf_ocr_parser import parse_with_pymupdf_ocr

pdf = '/Users/MAC/Desktop/pdfs/dummy_statement.pdf'
print(f"Testing PyMuPDF OCR parser on {pdf}")
print("="*80)

try:
    transactions = parse_with_pymupdf_ocr(pdf)
    print(f"\n✓ Found {len(transactions)} transactions\n")
    
    if transactions:
        print(f"{'Date':<12} {'Description':<45} {'Amount':>12}")
        print("-" * 70)
        
        credits = []
        debits = []
        
        for t in sorted(transactions, key=lambda x: x.get('date_string', '')):
            date = t.get('date_string', 'No date')[:12]
            desc = (t.get('description', 'No description') or 'No description')[:45]
            amount = t.get('amount', 0) or 0
            print(f"{date:<12} {desc:<45} ${amount:>11.2f}")
            
            if amount > 0:
                credits.append(amount)
            else:
                debits.append(amount)
        
        print("-" * 70)
        total_credits = sum(credits)
        total_debits = sum(debits)
        net = total_credits + total_debits
        
        print(f"{'Total Credits':<58} ${total_credits:>11.2f}")
        print(f"{'Total Debits':<58} ${total_debits:>11.2f}")
        print(f"{'Net Total':<58} ${net:>11.2f}")
        
        print(f"\n✅ Accuracy check vs actual PDF:")
        print(f"Expected: 21 transactions, Credits: $1,876.28, Debits: -$1,289.57")
        print(f"Extracted: {len(transactions)} transactions, Credits: ${total_credits:.2f}, Debits: ${total_debits:.2f}")
        
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()