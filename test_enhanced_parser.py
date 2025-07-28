#!/usr/bin/env python3
"""Test enhanced parser against current parser"""
import sys
sys.path.insert(0, '.')
from backend.universal_parser import parse_universal_pdf
from backend.universal_parser_enhanced import parse_universal_pdf_enhanced
import os

def test_pdf(pdf_path):
    """Compare parsers on a single PDF"""
    filename = os.path.basename(pdf_path)
    print(f"\n{'='*80}")
    print(f"Testing: {filename}")
    print(f"{'='*80}")
    
    if not os.path.exists(pdf_path):
        print("❌ File not found!")
        return
    
    # Test current parser
    print("\n📊 Current Parser:")
    try:
        trans1 = parse_universal_pdf(pdf_path)
        print(f"   Found {len(trans1)} transactions")
        if trans1 and len(trans1) <= 5:
            for t in trans1:
                print(f"   - {t.get('date_string', 'No date')} | {t.get('amount', 0):.2f}")
    except Exception as e:
        print(f"   Error: {e}")
        trans1 = []
    
    # Test enhanced parser
    print("\n🚀 Enhanced Parser:")
    try:
        trans2 = parse_universal_pdf_enhanced(pdf_path)
        print(f"   Found {len(trans2)} transactions")
        if trans2 and len(trans2) <= 5:
            for t in trans2:
                print(f"   - {t.get('date_string', 'No date')} | {t.get('amount', 0):.2f}")
    except Exception as e:
        print(f"   Error: {e}")
        trans2 = []
    
    # Compare results
    if len(trans2) > len(trans1):
        print(f"\n✅ Enhanced parser found {len(trans2) - len(trans1)} more transactions!")
    elif len(trans2) < len(trans1):
        print(f"\n⚠️  Enhanced parser found {len(trans1) - len(trans2)} fewer transactions")
    else:
        print(f"\n➡️  Both parsers found the same number of transactions")

def main():
    """Test key PDFs"""
    test_pdfs = [
        "/Users/MAC/Desktop/pdfs/dummy_statement.pdf",
        "/Users/MAC/Desktop/pdfs/Bank Statement Example Final.pdf",
        "/Users/MAC/Desktop/pdfs/1/USA Chase bank.pdf",
        "/Users/MAC/Desktop/pdfs/1/USA Wells Fargo 7 pages.pdf",
        "/Users/MAC/Desktop/pdfs/1/Australia Commonwealth J C.pdf"
    ]
    
    for pdf_path in test_pdfs:
        test_pdf(pdf_path)
    
    print(f"\n{'='*80}")
    print("SUMMARY")
    print(f"{'='*80}")
    print("Enhanced parser improvements:")
    print("- Validates dates to exclude phone numbers")
    print("- Filters unrealistic amounts (>$1M)")
    print("- Uses pdfplumber as primary method")
    print("- Better integration of all parsing methods")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        test_pdf(sys.argv[1])
    else:
        main()