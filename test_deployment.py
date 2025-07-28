#!/usr/bin/env python3
"""Test script to verify enhanced parser deployment"""
import os
import sys
sys.path.insert(0, '.')

print("🧪 Testing Enhanced PDF Parser Deployment")
print("="*60)

# Test 1: Import check
print("\n1. Checking imports...")
try:
    from backend.universal_parser_enhanced import parse_universal_pdf_enhanced
    from backend.pdfplumber_parser import parse_with_pdfplumber
    from backend.manual_validation_interface import create_validation_interface
    print("   ✓ All modules imported successfully")
except ImportError as e:
    print(f"   ❌ Import error: {e}")
    sys.exit(1)

# Test 2: Parse dummy statement
print("\n2. Testing dummy_statement.pdf...")
pdf_path = "/Users/MAC/Desktop/pdfs/dummy_statement.pdf"
if os.path.exists(pdf_path):
    try:
        trans = parse_universal_pdf_enhanced(pdf_path)
        print(f"   ✓ Extracted {len(trans)} transactions")
        if trans:
            print(f"   Sample: {trans[0].get('date_string')} - ${trans[0].get('amount')}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
else:
    print(f"   ⚠️  Test PDF not found at {pdf_path}")

# Test 3: Parse example bank statement
print("\n3. Testing example_bank_statement.pdf...")
pdf_path2 = "/Users/MAC/Desktop/pdfs/example_bank_statement.pdf"
if os.path.exists(pdf_path2):
    try:
        trans2 = parse_universal_pdf_enhanced(pdf_path2)
        print(f"   ✓ Extracted {len(trans2)} transactions")
        total = sum(t.get('amount', 0) for t in trans2)
        print(f"   Net total: ${total:.2f}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
else:
    print(f"   ⚠️  Test PDF not found at {pdf_path2}")

# Test 4: Manual validation interface
print("\n4. Testing manual validation interface...")
try:
    if 'trans' in locals() and trans:
        validation_file = create_validation_interface(pdf_path, trans)
        print(f"   ✓ Created validation file: {validation_file}")
        # Clean up
        os.remove(validation_file)
    else:
        print("   ⚠️  No transactions to validate")
except Exception as e:
    print(f"   ❌ Error: {e}")

print("\n✅ All tests completed!")
print("\nTo deploy to server:")
print("1. SSH into the server:")
print("   ssh -i /path/to/key.pem ubuntu@bankcsvconverter.com")
print("2. Run the deployment script:")
print("   cd /home/ubuntu/bank-statement-converter")
print("   ./deploy.sh")