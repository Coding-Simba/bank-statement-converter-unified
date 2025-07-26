#!/usr/bin/env python3
"""Test with PyMuPDF which might handle complex PDFs better"""

try:
    import fitz  # PyMuPDF
    
    pdf_path = "/Users/MAC/Downloads/merged_statements_2025-07-26.pdf"
    
    print("Testing with PyMuPDF (fitz)...")
    print("-" * 60)
    
    # Open the PDF
    doc = fitz.open(pdf_path)
    
    print(f"Total pages: {len(doc)}")
    print(f"Metadata: {doc.metadata}")
    
    # Check each page
    for page_num in range(len(doc)):
        page = doc[page_num]
        
        print(f"\n{'='*60}")
        print(f"PAGE {page_num + 1}")
        print(f"{'='*60}")
        
        # Get text with different extraction methods
        text_methods = [
            ("TEXT", page.get_text("text")),
            ("BLOCKS", page.get_text("blocks")),
            ("DICT", page.get_text("dict")),
        ]
        
        for method_name, content in text_methods[:2]:  # Skip DICT for now
            print(f"\n--- {method_name} extraction ---")
            
            if method_name == "TEXT":
                lines = content.split('\n')
                print(f"Total lines: {len(lines)}")
                for i, line in enumerate(lines):
                    if line.strip():
                        print(f"{i:3}: {line}")
                        
            elif method_name == "BLOCKS":
                print(f"Total blocks: {len(content)}")
                for i, block in enumerate(content):
                    if block[4].strip():  # text content
                        print(f"Block {i}: {block[4][:100]}")
        
        # Check for hidden text or form fields
        print("\n--- Checking for form fields ---")
        for field in page.widgets():
            print(f"Field: {field.field_name} = {field.field_value}")
        
        # Check text instances more deeply
        text_instances = page.get_text("dict")
        if "blocks" in text_instances:
            blocks_with_content = 0
            for block in text_instances["blocks"]:
                if "lines" in block:
                    for line in block["lines"]:
                        if "spans" in line:
                            for span in line["spans"]:
                                if "text" in span and span["text"].strip():
                                    blocks_with_content += 1
            print(f"\nText blocks with content: {blocks_with_content}")
        
        # Check for images that might contain the data
        image_list = page.get_images()
        if image_list:
            print(f"\n--- Found {len(image_list)} images ---")
            for img in image_list:
                print(f"Image: {img}")
    
    doc.close()
    
except ImportError:
    print("PyMuPDF (fitz) not installed. Install with: pip install PyMuPDF")
    
    # Fall back to checking if it's a scanned PDF
    import subprocess
    pdf_path = "/Users/MAC/Downloads/merged_statements_2025-07-26.pdf"
    print("\nChecking with pdftotext...")
    try:
        result = subprocess.run(['pdftotext', '-layout', pdf_path, '-'], 
                                capture_output=True, text=True)
        if result.returncode == 0:
            print("Output from pdftotext:")
            print("-" * 40)
            lines = result.stdout.split('\n')
            for i, line in enumerate(lines[:100]):  # First 100 lines
                if line.strip():
                    print(f"{i:3}: {line}")
        else:
            print(f"pdftotext failed: {result.stderr}")
    except FileNotFoundError:
        print("pdftotext not found")