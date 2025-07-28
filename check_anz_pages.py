#!/usr/bin/env python3
"""Check ANZ PDF pages"""

import pdfplumber

pdf_path = "/Users/MAC/Desktop/pdfs/1/Australia ANZ.pdf"

with pdfplumber.open(pdf_path) as pdf:
    print(f"Total pages: {len(pdf.pages)}")
    
    for i, page in enumerate(pdf.pages):
        print(f"\n=== Page {i+1} ===")
        text = page.extract_text()
        if text:
            lines = text.split('\n')
            print(f"Total lines: {len(lines)}")
            
            # Look for transaction patterns
            trans_count = 0
            for line in lines:
                # ANZ transaction patterns (date at start)
                if line and (line[:2].isdigit() or line.startswith('Date')):
                    print(f"  {line[:80]}")
                    trans_count += 1
                    if trans_count > 10:
                        print("  ...")
                        break