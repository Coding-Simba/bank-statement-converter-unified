#!/usr/bin/env python3
"""Analyze the exact format of bank statements to fix parsing"""

import subprocess
import re

def analyze_pdf_text(pdf_path):
    """Extract and analyze raw text from PDF"""
    print(f"\n=== ANALYZING: {pdf_path} ===")
    
    try:
        # Run pdftotext with layout preservation
        result = subprocess.run(['pdftotext', '-layout', pdf_path, '-'], 
                                capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"pdftotext failed: {result.stderr}")
            return
            
        lines = result.stdout.split('\n')
        
        # Find transaction lines
        print("\n--- LOOKING FOR TRANSACTION PATTERNS ---")
        for i, line in enumerate(lines):
            # Look for lines with multiple numeric values (potential transactions)
            amounts = re.findall(r'[\d,]+\.\d{2}', line)
            if len(amounts) >= 2 and not any(keyword in line.lower() for keyword in ['total', 'balance at', 'summary']):
                print(f"\nLine {i}: {line}")
                print(f"  Found amounts: {amounts}")
                
                # Try to identify what each amount represents
                if 'out' in lines[max(0, i-5):i+1] or 'in' in lines[max(0, i-5):i+1]:
                    print("  Likely format: Date | Description | Money out | Money In | Balance")
                    if len(amounts) >= 3:
                        print(f"  Transaction amount might be: {amounts[0]} (out) or {amounts[1]} (in)")
                        print(f"  Balance is likely: {amounts[-1]}")
                
    except Exception as e:
        print(f"Error: {e}")

# Analyze the problematic PDFs
pdfs = [
    './failed_pdfs/20250727_005210_a17b26f9_Bank Statement Example Final.pdf',
    './uploads/11a56e83-e80a-4725-adf3-e33f19ee8f36.pdf',
]

for pdf in pdfs:
    analyze_pdf_text(pdf)