#!/usr/bin/env python3
import sys
sys.path.insert(0, '.')
from backend.dummy_pdf_parser import parse_dummy_pdf

pdf = '/Users/MAC/Desktop/pdfs/dummy_statement.pdf'
print('Testing dummy parser directly:')
trans = parse_dummy_pdf(pdf)
print(f'Found {len(trans)} raw transactions from dummy parser\n')

print('All transactions:')
for i, t in enumerate(trans, 1):
    print(f'{i}. {t.get("date_string")} | {t.get("description")} | ${t.get("amount")}')