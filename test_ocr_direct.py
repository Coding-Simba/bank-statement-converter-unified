#!/usr/bin/env python3
import sys
sys.path.insert(0, '.')
from backend.advanced_ocr_parser import parse_scanned_pdf_advanced

pdf = '/Users/MAC/Desktop/pdfs/dummy_statement.pdf'
print('Testing advanced OCR directly:')
trans = parse_scanned_pdf_advanced(pdf)
print(f'Found {len(trans)} transactions\n')

for i, t in enumerate(trans, 1):
    desc = t.get("description", "")[:40]
    print(f'{i}. {t.get("date_string")} | {desc} | ${t.get("amount")}')