#!/usr/bin/env python3
"""Test dummy PDF parsing after removing hardcoded logic"""

import os
import sys

# Add backend to path
backend_path = os.path.join(os.path.dirname(__file__), 'backend')
sys.path.insert(0, backend_path)

# Change to backend directory for relative imports
os.chdir(backend_path)

# Now import
import universal_parser

def test_dummy_pdf():
    pdf_path = '/Users/MAC/Desktop/pdfs/dummy_statement.pdf'
    print(f"Testing: {pdf_path}")
    
    try:
        transactions = universal_parser.parse_universal_pdf(pdf_path)
        print(f"Successfully parsed {len(transactions)} transactions")
        
        # Show first few transactions
        for i, trans in enumerate(transactions[:5]):
            print(f"Transaction {i+1}:")
            print(f"  Date: {trans.get('date_string', 'N/A')}")
            print(f"  Description: {trans.get('description', 'N/A')}")
            print(f"  Amount: ${trans.get('amount', 0):.2f}")
            print()
            
        return len(transactions) > 0
    except Exception as e:
        print(f"Error parsing PDF: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_dummy_pdf()
    if success:
        print("✓ Dummy PDF parser working without hardcoded logic!")
    else:
        print("✗ Dummy PDF parser failed")
        sys.exit(1)