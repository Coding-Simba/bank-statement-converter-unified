#!/usr/bin/env python3
"""Test OCR capabilities with a scanned PDF"""

import sys
sys.path.append('.')

from backend.ocr_parser import check_ocr_requirements, is_scanned_pdf
from backend.universal_parser import parse_universal_pdf

def test_ocr_setup():
    """Test if OCR is properly set up"""
    print("=" * 70)
    print("OCR SETUP CHECK")
    print("=" * 70)
    
    ocr_ready, message = check_ocr_requirements()
    
    if ocr_ready:
        print("✅ OCR is ready to use!")
        print("\nCapabilities:")
        print("- Can process scanned PDFs")
        print("- Automatic image enhancement")
        print("- Multi-page support")
        print("- Table detection")
        print("- Error correction for common OCR mistakes")
    else:
        print(f"❌ OCR not available: {message}")
        print("\nTo enable OCR support:")
        print("1. Install Python packages:")
        print("   pip install -r requirements-ocr.txt")
        print("\n2. Install system dependencies:")
        print("   Mac: brew install tesseract poppler")
        print("   Ubuntu/Debian: sudo apt-get install tesseract-ocr poppler-utils")
        print("   Windows: Download installers from:")
        print("   - Tesseract: https://github.com/UB-Mannheim/tesseract/wiki")
        print("   - Poppler: http://blog.alivate.com.au/poppler-windows/")
    
    return ocr_ready

def demonstrate_ocr_features():
    """Demonstrate OCR features"""
    print("\n" + "=" * 70)
    print("OCR FEATURES")
    print("=" * 70)
    
    print("""
The OCR parser includes:

1. **Image Preprocessing**:
   - Grayscale conversion
   - Contrast enhancement
   - Noise reduction
   - Automatic deskewing
   - Sharpening filters

2. **Text Extraction**:
   - High-DPI scanning (300 DPI)
   - Multi-language support
   - Confidence scoring
   - Layout preservation

3. **Error Correction**:
   - Common OCR mistakes (O→0, l→1, |→1)
   - Date format fixing
   - Amount parsing with multiple formats
   - Description cleaning

4. **Transaction Detection**:
   - Multiple date formats
   - Various amount formats
   - Table structure recognition
   - Column alignment detection

5. **Supported Formats**:
   - Scanned bank statements
   - Photographed documents
   - Low-quality PDFs
   - Multi-page documents
   """)

def test_with_sample_pdf(pdf_path):
    """Test OCR with a sample PDF"""
    print("\n" + "=" * 70)
    print(f"TESTING PDF: {pdf_path}")
    print("=" * 70)
    
    # Check if it's a scanned PDF
    if is_scanned_pdf(pdf_path):
        print("📄 Detected as scanned PDF (low text content)")
    else:
        print("📝 Detected as text-based PDF")
    
    # Try parsing
    print("\nParsing PDF...")
    try:
        transactions = parse_universal_pdf(pdf_path)
        
        if transactions:
            print(f"\n✅ Successfully extracted {len(transactions)} transactions!")
            
            # Show sample transactions
            print("\nSample transactions:")
            for i, trans in enumerate(transactions[:5]):
                date_str = trans['date'].strftime('%Y-%m-%d') if trans.get('date') else 'No date'
                desc = trans.get('description', 'No description')
                amount = trans.get('amount', 0)
                print(f"{i+1}. {date_str} | {desc[:40]:40} | ${amount:>10.2f}")
                
            if len(transactions) > 5:
                print(f"... and {len(transactions) - 5} more transactions")
        else:
            print("\n❌ No transactions found")
            
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")

if __name__ == "__main__":
    # Check OCR setup
    ocr_ready = test_ocr_setup()
    
    # Demonstrate features
    demonstrate_ocr_features()
    
    # Test with a PDF if provided
    if len(sys.argv) > 1:
        pdf_path = sys.argv[1]
        test_with_sample_pdf(pdf_path)
    else:
        print("\n" + "=" * 70)
        print("USAGE")
        print("=" * 70)
        print("To test with a PDF:")
        print(f"  python3 {sys.argv[0]} /path/to/your/scanned.pdf")
        print("\nThe parser will automatically detect if OCR is needed.")