#!/usr/bin/env python3
"""Test PDF parser with all uploaded PDFs"""

from backend.universal_parser import parse_universal_pdf
import os
import glob

# Get all PDFs in uploads directory
pdf_files = glob.glob('./uploads/*.pdf')

print(f"Found {len(pdf_files)} PDF files to test")
print("=" * 60)

results = []

for pdf_path in pdf_files:
    print(f"\nTesting: {os.path.basename(pdf_path)}")
    print("-" * 40)
    
    try:
        transactions = parse_universal_pdf(pdf_path)
        
        # Count valid vs header transactions
        valid_count = 0
        header_count = 0
        
        for trans in transactions:
            desc = trans.get('description', '').lower()
            if any(word in desc for word in ['bank', 'america', 'p.o.', 'box', 'statement', 'account', 'issue', 'period', 'customer service']):
                header_count += 1
            else:
                valid_count += 1
        
        results.append({
            'file': os.path.basename(pdf_path),
            'total': len(transactions),
            'valid': valid_count,
            'headers': header_count
        })
        
        print(f"Total transactions: {len(transactions)}")
        print(f"Valid transactions: {valid_count}")
        print(f"Header/junk entries: {header_count}")
        
        # Show first valid transaction if any
        if valid_count > 0:
            for trans in transactions:
                desc = trans.get('description', '').lower()
                if not any(word in desc for word in ['bank', 'america', 'p.o.', 'box', 'statement', 'account', 'issue', 'period', 'customer service']):
                    print(f"\nFirst valid transaction:")
                    print(f"  Date: {trans.get('date_string', 'N/A')}")
                    print(f"  Description: {trans.get('description', 'N/A')}")
                    print(f"  Amount: ${trans.get('amount', 0):.2f}")
                    break
                    
    except Exception as e:
        print(f"Error: {e}")
        results.append({
            'file': os.path.basename(pdf_path),
            'total': 0,
            'valid': 0,
            'headers': 0,
            'error': str(e)
        })

print("\n" + "=" * 60)
print("SUMMARY:")
print("=" * 60)

for result in results:
    print(f"\n{result['file']}:")
    if 'error' in result:
        print(f"  ERROR: {result['error']}")
    else:
        print(f"  Total: {result['total']}, Valid: {result['valid']}, Headers: {result['headers']}")