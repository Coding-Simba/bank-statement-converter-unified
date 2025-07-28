#\!/usr/bin/env python3
"""Test a single PDF at a time"""

from backend.universal_parser import parse_universal_pdf
import os
import sys

def test_pdf(pdf_path):
    print(f"\nTesting: {os.path.basename(pdf_path)}")
    print("="*60)
    
    try:
        trans = parse_universal_pdf(pdf_path)
        print(f"✓ Found {len(trans)} transactions")
        
        if trans:
            print("\nFirst 5 transactions:")
            print("-"*60)
            for i, t in enumerate(trans[:5], 1):
                date = t.get('date_string', 'No date')
                desc = t.get('description', 'No description')[:40]
                amount = t.get('amount', 0)
                print(f"{i}. {date:<10} | {desc:<40} | ${amount:>10.2f}")
            
            if len(trans) > 5:
                print(f"... and {len(trans) - 5} more transactions")
                
            # Check quality
            missing_dates = sum(1 for t in trans if not t.get('date_string'))
            missing_amounts = sum(1 for t in trans if t.get('amount') is None)
            
            if missing_dates or missing_amounts:
                print(f"\n⚠️  Quality issues:")
                if missing_dates:
                    print(f"   - {missing_dates} transactions missing dates")
                if missing_amounts:
                    print(f"   - {missing_amounts} transactions missing amounts")
                    
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        pdf_path = sys.argv[1]
    else:
        # Default test
        pdf_path = "/Users/MAC/Desktop/pdfs/dummy_statement.pdf"
    
    if os.path.exists(pdf_path):
        test_pdf(pdf_path)
    else:
        print(f"File not found: {pdf_path}")
EOF < /dev/null