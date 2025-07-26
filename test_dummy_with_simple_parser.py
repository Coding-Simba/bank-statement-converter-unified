#!/usr/bin/env python3
"""Test dummy PDF with a simpler parser approach"""

import sys
sys.path.append('.')

from pdf2image import convert_from_path
import pytesseract
import re
from datetime import datetime

def simple_ocr_parse(pdf_path):
    """Simple OCR parser for the dummy PDF format"""
    transactions = []
    
    # Convert to images
    images = convert_from_path(pdf_path, dpi=300)
    
    for page_num, image in enumerate(images):
        # Get OCR text
        text = pytesseract.image_to_string(image)
        lines = text.split('\n')
        
        # Look for different transaction patterns
        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
            
            # Pattern 1: Check entries (e.g., "1234 10/05 $9.98")
            check_match = re.search(r'(\d{4})\*?\s+(\d{1,2}/\d{1,2})\s+\$?([\d,]+\.\d{2})', line)
            if check_match:
                check_num = check_match.group(1)
                date_str = check_match.group(2)
                amount_str = check_match.group(3)
                
                transactions.append({
                    'description': f'CHECK {check_num}',
                    'date_string': date_str,
                    'amount': -float(amount_str.replace(',', '')),
                    'page': page_num + 1
                })
                continue
            
            # Pattern 2: POS/ATM transactions on page 1 (amount in next column)
            if 'POS PURCHASE' in line or 'ATM WITHDRAWAL' in line or 'PREAUTHORIZED CREDIT' in line:
                # Look for amount in the same line or nearby
                amount_match = re.search(r'([\d,]+\.\d{2})', line)
                if amount_match:
                    amount = float(amount_match.group(1).replace(',', ''))
                    if 'CREDIT' in line:
                        amount = abs(amount)
                    else:
                        amount = -abs(amount)
                    
                    # Clean description
                    desc = line
                    if amount_match:
                        desc = line[:line.find(amount_match.group(1))].strip()
                    
                    transactions.append({
                        'description': desc,
                        'amount': amount,
                        'page': page_num + 1
                    })
            
            # Pattern 3: Date at start of line (e.g., "10/05 POS PURCHASE...")
            date_match = re.match(r'^(\d{1,2}/\d{1,2})\s+(.+)', line)
            if date_match:
                date_str = date_match.group(1)
                rest = date_match.group(2)
                
                # Look for amount in the rest of the line
                amount_match = re.search(r'\$?([\d,]+\.\d{2})', rest)
                if amount_match:
                    amount = float(amount_match.group(1).replace(',', ''))
                    desc = rest[:rest.find(amount_match.group(0))].strip()
                else:
                    desc = rest.strip()
                    amount = 0  # Will need to find amount elsewhere
                
                # Determine if debit or credit
                if any(word in desc.upper() for word in ['CREDIT', 'DEPOSIT', 'INTEREST']):
                    amount = abs(amount)
                elif amount > 0:
                    amount = -amount
                
                transactions.append({
                    'description': desc,
                    'date_string': date_str,
                    'amount': amount,
                    'page': page_num + 1
                })
    
    return transactions

# Test the dummy PDF
pdf_path = "/Users/MAC/Downloads/dummy_statement.pdf"
print(f"Testing simple OCR parser on: {pdf_path}")
print("=" * 70)

transactions = simple_ocr_parse(pdf_path)

print(f"\nFound {len(transactions)} transactions")

if transactions:
    # Group by page
    for page in [1, 2]:
        page_trans = [t for t in transactions if t.get('page') == page]
        if page_trans:
            print(f"\n--- Page {page} ({len(page_trans)} transactions) ---")
            for trans in page_trans[:10]:  # Show first 10
                date_str = trans.get('date_string', 'No date')
                desc = trans['description'][:50]
                amount = trans['amount']
                print(f"{date_str:8} | {desc:50} | ${amount:>10.2f}")
            
            if len(page_trans) > 10:
                print(f"... and {len(page_trans) - 10} more")
    
    # Summary
    total_credits = sum(t['amount'] for t in transactions if t['amount'] > 0)
    total_debits = sum(t['amount'] for t in transactions if t['amount'] < 0)
    print(f"\nSummary:")
    print(f"Total credits: ${total_credits:,.2f}")
    print(f"Total debits: ${total_debits:,.2f}")
    print(f"Net: ${total_credits + total_debits:,.2f}")
else:
    print("\nNo transactions found!")