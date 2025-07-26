#!/usr/bin/env python3
"""Test script to see raw PDF content"""

import PyPDF2
import sys

def show_pdf_content(pdf_path):
    """Show raw PDF content"""
    try:
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            print(f"PDF has {len(pdf_reader.pages)} pages")
            
            # Show first page
            if len(pdf_reader.pages) > 0:
                text = pdf_reader.pages[0].extract_text()
                lines = text.split('\n')
                
                print("\nFirst 50 lines of page 1:")
                for i, line in enumerate(lines[:50]):
                    print(f"{i:3}: {line}")
                    
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    pdf_path = sys.argv[1] if len(sys.argv) > 1 else "test.pdf"
    show_pdf_content(pdf_path)