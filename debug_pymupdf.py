#!/usr/bin/env python3
import sys
sys.path.insert(0, '.')
import fitz

pdf = '/Users/MAC/Desktop/pdfs/dummy_statement.pdf'
print(f"Debugging PyMuPDF on {pdf}")
print("="*80)

doc = fitz.open(pdf)
print(f"Pages: {len(doc)}")

for page_num in range(len(doc)):
    page = doc[page_num]
    print(f"\nPage {page_num + 1}:")
    print(f"  Size: {page.rect.width} x {page.rect.height}")
    
    # Get text
    text = page.get_text()
    print(f"  Text length: {len(text)} characters")
    if text.strip():
        print(f"  First 200 chars: {text[:200]}")
    
    # Check for tables
    tabs = page.find_tables()
    table_list = list(tabs) if tabs else []
    print(f"  Tables found: {len(table_list)}")
    
    if table_list:
        for i, tab in enumerate(table_list):
            print(f"\n  Table {i+1}:")
            data = tab.extract()
            print(f"    Rows: {len(data)}")
            if data:
                print(f"    First row: {data[0]}")
                if len(data) > 1:
                    print(f"    Second row: {data[1]}")
    
    # Get text as dict with positions
    blocks = page.get_text("dict")
    text_count = 0
    for block in blocks.get("blocks", []):
        if block.get("type") == 0:  # Text block
            for line in block.get("lines", []):
                for span in line.get("spans", []):
                    text_count += 1
    print(f"  Text spans: {text_count}")

doc.close()