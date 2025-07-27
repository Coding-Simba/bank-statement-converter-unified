#!/usr/bin/env python3
"""Test a sample of PDFs to verify parsers are working"""

from backend.universal_parser import parse_universal_pdf

test_pdfs = [
    ('USA Bank of America.pdf', '/Users/MAC/Desktop/pdfs/1/USA Bank of America.pdf', 69),
    ('USA PayPal Account Statement.pdf', '/Users/MAC/Desktop/pdfs/1/USA PayPal Account Statement.pdf', 10),
    ('UK Monzo Bank st. word.pdf', '/Users/MAC/Desktop/pdfs/1/Monzo Bank st. word.pdf', 28),
    ('Australia Commonwealth J C.pdf', '/Users/MAC/Desktop/pdfs/1/Australia Commonwealth J C.pdf', 461),
    ('Canada RBC.pdf', '/Users/MAC/Desktop/pdfs/1/Canada RBC.pdf', 50)
]

print("SAMPLE PDF PARSER TEST")
print("=" * 60)

for name, path, expected in test_pdfs:
    print(f"\nTesting: {name}")
    try:
        transactions = parse_universal_pdf(path)
        count = len(transactions)
        
        if count == expected:
            print(f"✅ PASS: Found {count} transactions (expected {expected})")
        else:
            print(f"⚠️  WARN: Found {count} transactions (expected {expected})")
            
        # Show first transaction
        if transactions:
            t = transactions[0]
            print(f"   First: {t.get('date_string', 'N/A')} - {t.get('description', 'N/A')[:30]}... ${t['amount']:.2f}")
    except Exception as e:
        print(f"❌ FAIL: {str(e)}")

print("\n" + "=" * 60)