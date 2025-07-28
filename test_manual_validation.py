#!/usr/bin/env python3
"""Test manual validation interface with dummy statement"""
import sys
sys.path.insert(0, '.')
from backend.universal_parser_enhanced import parse_universal_pdf_enhanced
from backend.manual_validation_interface import create_validation_interface, process_validated_file
import json

pdf = '/Users/MAC/Desktop/pdfs/dummy_statement.pdf'
print(f"Testing manual validation interface with {pdf}")
print("="*80)

# Step 1: Extract transactions
print("\n1. Extracting transactions...")
transactions = parse_universal_pdf_enhanced(pdf)
print(f"   Found {len(transactions)} transactions")

# Step 2: Create validation template
print("\n2. Creating validation template...")
validation_file = create_validation_interface(pdf, transactions)
print(f"   Created: {validation_file}")

# Step 3: Show validation template content
print("\n3. Validation template content:")
with open(validation_file, 'r') as f:
    data = json.load(f)

print(f"\n   Summary:")
print(f"   - Total transactions: {data['summary']['total_transactions']}")
print(f"   - Needs review: {sum(1 for t in data['transactions'] if t['needs_review'])}")
print(f"   - Total credits: ${data['summary']['total_credits']:,.2f}")
print(f"   - Total debits: ${data['summary']['total_debits']:,.2f}")

print(f"\n   Transactions needing review:")
for trans in data['transactions']:
    if trans['needs_review']:
        print(f"   [{trans['index']}] {trans['date']} | {trans['description'][:30]} | ${trans['amount']} | Issues: {trans['issues']}")

print(f"\n4. Manual validation process:")
print("   The validation file has been created with:")
print("   - All extracted transactions")
print("   - Confidence scores")
print("   - Flagged issues (large amounts, missing data)")
print("   - Instructions for manual review")

print(f"\n   Users can:")
print("   1. Open the JSON file in a text editor")
print("   2. Review flagged transactions")
print("   3. Correct dates, descriptions, and amounts")
print("   4. Set 'validated': true for reviewed items")
print("   5. Add 'correction_notes' to explain changes")
print("   6. Save and process the validated file")

# Example of what corrected data would look like
print(f"\n5. Example of corrected transaction:")
print('   Original: {"date": "10/05", "amount": -443565.0, "issues": ["large_amount"]}')
print('   Corrected: {"date": "10/05", "amount": -11.68, "validated": true, "correction_notes": "Fixed OCR error"}')