#!/usr/bin/env python3
"""Debug column detection in bank statements"""

import subprocess
import re

def debug_pdf(pdf_path):
    print(f"\n=== DEBUGGING: {pdf_path} ===")
    
    try:
        # Get text with layout preserved
        result = subprocess.run(['pdftotext', '-layout', pdf_path, '-'], 
                                capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"pdftotext failed: {result.stderr}")
            return
            
        lines = result.stdout.split('\n')
        
        # Look for header lines
        print("\n--- SEARCHING FOR HEADER PATTERNS ---")
        for i, line in enumerate(lines[:50]):
            if 'money' in line.lower() or 'balance' in line.lower():
                print(f"Line {i}: {line}")
        
        print("\n--- SAMPLE TRANSACTION LINES ---")
        # Look for lines with transaction patterns
        count = 0
        for i, line in enumerate(lines):
            if count >= 5:
                break
            amounts = re.findall(r'[\d,]+\.\d{2}', line)
            if len(amounts) >= 2 and not any(skip in line.lower() for skip in ['total', 'balance at', 'summary']):
                print(f"\nLine {i}: '{line}'")
                print(f"  Amounts found: {amounts}")
                count += 1
                
    except Exception as e:
        print(f"Error: {e}")

# Test PDFs
pdfs = [
    './failed_pdfs/20250727_005210_a17b26f9_Bank Statement Example Final.pdf',
]

for pdf in pdfs:
    debug_pdf(pdf)