#!/usr/bin/env python3
"""Debug OCR on dummy_statement.pdf"""

import sys
sys.path.append('.')

from pdf2image import convert_from_path
import pytesseract
from PIL import Image, ImageEnhance

pdf_path = "/Users/MAC/Downloads/dummy_statement.pdf"

print("Converting PDF to images...")
images = convert_from_path(pdf_path, dpi=300)
print(f"Got {len(images)} pages")

for i, image in enumerate(images):
    print(f"\n{'='*70}")
    print(f"PAGE {i+1}")
    print(f"{'='*70}")
    
    # Show image properties
    print(f"Image size: {image.size}")
    print(f"Image mode: {image.mode}")
    
    # Try OCR without preprocessing
    print("\n1. OCR without preprocessing:")
    text = pytesseract.image_to_string(image)
    print(f"   Text length: {len(text)} characters")
    if text.strip():
        print("   Text preview:")
        print("-" * 50)
        print(text[:1000])
    else:
        print("   No text extracted!")
    
    # Try with enhancement
    print("\n2. OCR with contrast enhancement:")
    enhanced = ImageEnhance.Contrast(image).enhance(2.0)
    text2 = pytesseract.image_to_string(enhanced)
    print(f"   Text length: {len(text2)} characters")
    if text2.strip() and text2 != text:
        print("   Additional text found:")
        print("-" * 50)
        print(text2[:500])
    
    # Try different OCR modes
    print("\n3. OCR with different page segmentation modes:")
    for psm in [3, 6, 11, 12]:  # Different page segmentation modes
        try:
            config = f'--psm {psm}'
            text_psm = pytesseract.image_to_string(image, config=config)
            if text_psm.strip():
                print(f"   PSM {psm}: Found {len(text_psm)} characters")
                if len(text_psm) > len(text):
                    print(f"      Better result! First 200 chars: {text_psm[:200]}")
        except:
            pass
    
    # Save first page for inspection
    if i == 0:
        image.save("dummy_page1_original.png")
        enhanced.save("dummy_page1_enhanced.png")
        print(f"\n   Saved page 1 as dummy_page1_original.png and dummy_page1_enhanced.png for inspection")