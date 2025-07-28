#!/usr/bin/env python3
import sys
sys.path.insert(0, '.')
from backend.universal_parser_enhanced import parse_universal_pdf_enhanced
from backend.universal_parser import parse_universal_pdf

pdf = '/Users/MAC/Desktop/pdfs/example_bank_statement.pdf'

print("="*80)
print("CURRENT PARSER")
print("="*80)
trans1 = parse_universal_pdf(pdf)
print(f'Found {len(trans1)} transactions')

print("\n" + "="*80)
print("ENHANCED PARSER")
print("="*80)
trans2 = parse_universal_pdf_enhanced(pdf)
print(f'Found {len(trans2)} transactions')

if trans2:
    print('\nAll transactions:')
    print(f"{'Date':<15} {'Description':<40} {'Amount':>12}")
    print('-' * 70)
    for t in trans2:
        date = t.get('date_string', 'No date')[:15]
        desc = (t.get('description', 'No description') or 'No description')[:40]
        amount = t.get('amount', 0) or 0
        print(f"{date:<15} {desc:<40} ${amount:>11.2f}")
    
    # Summary
    total = sum(t.get('amount', 0) for t in trans2)
    print('-' * 70)
    print(f"{'Total':<56} ${total:>11.2f}")