#!/usr/bin/env python3
"""Test OCR specifically on page 2 of the PDF"""

from pdf2image import convert_from_path
from PIL import Image
import pytesseract
import os

pdf_path = './test_example.pdf'

print("=== PAGE 2 OCR TEST ===")
print("=" * 60)

# Convert PDF pages to images
print("\n1. Converting PDF to images...")
try:
    images = convert_from_path(pdf_path, dpi=300)
    print(f"Successfully converted {len(images)} pages to images")
    
    if len(images) >= 2:
        # Save page 2 as an image for inspection
        page2_image = images[1]  # 0-indexed
        page2_image.save('page2_image.png')
        print("Saved page 2 as page2_image.png")
        
        # Run OCR on page 2
        print("\n2. Running OCR on page 2...")
        text = pytesseract.image_to_string(page2_image)
        
        print("\n3. OCR Text from page 2:")
        print("-" * 40)
        print(text)
        print("-" * 40)
        print(f"\nTotal characters extracted: {len(text)}")
        
        # Look for transaction patterns
        print("\n4. Looking for transaction patterns...")
        import re
        lines = text.split('\n')
        transaction_count = 0
        
        for i, line in enumerate(lines):
            # Look for dates
            if re.search(r'\d{1,2}[/-]\d{1,2}', line):
                print(f"Potential transaction line {i}: {line.strip()}")
                transaction_count += 1
            # Look for amounts
            elif re.search(r'\$?\d+\.\d{2}', line) and len(line.strip()) > 5:
                print(f"Potential amount line {i}: {line.strip()}")
        
        print(f"\nFound {transaction_count} potential transaction lines")
        
        # Also try with different OCR settings
        print("\n5. Trying OCR with table detection mode...")
        custom_config = r'--oem 3 --psm 6'  # PSM 6 = Uniform block of text
        text_table = pytesseract.image_to_string(page2_image, config=custom_config)
        
        if text_table != text:
            print("Different result with table mode:")
            print(text_table[:500] + "..." if len(text_table) > 500 else text_table)
            
    else:
        print("ERROR: PDF has less than 2 pages!")
        
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()

# Also try extracting the image directly from PDF
print("\n\n6. Extracting images directly from PDF...")
try:
    import fitz  # PyMuPDF
    
    doc = fitz.open(pdf_path)
    if len(doc) >= 2:
        page = doc[1]  # Page 2
        image_list = page.get_images()
        print(f"Found {len(image_list)} images on page 2")
        
        if image_list:
            # Extract first image
            xref = image_list[0][0]
            pix = fitz.Pixmap(doc, xref)
            
            if pix.n - pix.alpha < 4:  # GRAY or RGB
                pix.save("page2_extracted.png")
                print("Saved extracted image as page2_extracted.png")
                
                # Run OCR on extracted image
                img = Image.open("page2_extracted.png")
                text = pytesseract.image_to_string(img)
                print("\nOCR from extracted image:")
                print(text[:500] + "..." if len(text) > 500 else text)
            else:
                pix1 = fitz.Pixmap(fitz.csRGB, pix)
                pix1.save("page2_extracted.png")
                pix = pix1
                
except ImportError:
    print("PyMuPDF not installed, skipping direct image extraction")