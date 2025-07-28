#!/usr/bin/env python3
import sys
sys.path.insert(0, '.')
from backend.universal_parser_enhanced import parse_universal_pdf_enhanced

pdf = '/Users/MAC/Desktop/pdfs/example_bank_statement.pdf'
trans = parse_universal_pdf_enhanced(pdf)
print(f'\n✓ Enhanced parser found {len(trans)} transactions from {pdf}')

if trans:
    print('\nTransactions:')
    for i, t in enumerate(trans, 1):
        print(f"{i}. {t.get('date_string')} | {t.get('description')} | ${t.get('amount'):.2f}")