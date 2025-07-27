#\!/usr/bin/env python3
import sys
sys.path.insert(0, '.')
from backend.universal_parser import parse_universal_pdf
import os

pdf = sys.argv[1] if len(sys.argv) > 1 else "/Users/MAC/Desktop/pdfs/dummy_statement.pdf"
print(f"\nTesting: {os.path.basename(pdf)}")
print("="*60)

try:
    trans = parse_universal_pdf(pdf)
    print(f"✓ Found {len(trans)} transactions")
    
    if trans:
        print("\nFirst 5 transactions:")
        for i, t in enumerate(trans[:5], 1):
            date = t.get('date_string', 'No date')
            desc = (t.get('description', 'No description') or 'No description')[:40]
            amount = t.get('amount', 0) or 0
            print(f"{i}. {date:<15} | {desc:<40} | ${amount:>10.2f}")
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
