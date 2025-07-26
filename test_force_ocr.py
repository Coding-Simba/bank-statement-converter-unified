
import os
os.environ['FORCE_OCR'] = '1'
from backend.universal_parser import parse_universal_pdf

# Temporarily patch to force OCR
import backend.universal_parser as up
original_is_scanned = up.is_scanned_pdf
up.is_scanned_pdf = lambda x: True  # Force it to think it's scanned

try:
    transactions = parse_universal_pdf('./test_example.pdf')
    print(f"Transactions with forced OCR: {len(transactions)}")
    
    for i, trans in enumerate(transactions[:10]):
        print(f"\nTransaction {i+1}:")
        print(f"  Date: {trans.get('date_string', 'N/A')}")
        print(f"  Description: {trans.get('description', 'N/A')}")
        print(f"  Amount: ${trans.get('amount', 0):.2f}")
finally:
    # Restore
    up.is_scanned_pdf = original_is_scanned
