# OCR Setup Guide for Scanned PDF Support

## Overview

The bank statement converter now supports scanned PDFs using OCR (Optical Character Recognition). This allows you to convert:
- Scanned bank statements
- Photographed documents
- Image-based PDFs
- Low-quality or faxed statements

## Installation

### 1. Install Python Dependencies

```bash
pip install -r requirements-ocr.txt
```

Or individually:
```bash
pip install pdf2image pillow pytesseract opencv-python
```

### 2. Install System Dependencies

#### macOS
```bash
# Install Homebrew if not already installed
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install Tesseract OCR and Poppler
brew install tesseract poppler
```

#### Ubuntu/Debian
```bash
# Update package list
sudo apt-get update

# Install Tesseract OCR and Poppler
sudo apt-get install tesseract-ocr poppler-utils

# Optional: Install additional language packs
sudo apt-get install tesseract-ocr-fra  # French
sudo apt-get install tesseract-ocr-deu  # German
sudo apt-get install tesseract-ocr-spa  # Spanish
```

#### Windows
1. Download and install Tesseract:
   - Go to: https://github.com/UB-Mannheim/tesseract/wiki
   - Download the installer for your system
   - Add Tesseract to your PATH

2. Download and install Poppler:
   - Go to: http://blog.alivate.com.au/poppler-windows/
   - Download and extract to a folder
   - Add the `bin` folder to your PATH

## Verification

Run the test script to verify OCR is working:

```bash
python3 test_ocr_capabilities.py
```

You should see:
```
✅ OCR is ready to use!
```

## Usage

### Automatic Detection

The parser automatically detects scanned PDFs and uses OCR when needed:

```python
from backend.universal_parser import parse_universal_pdf

# Works with both text-based and scanned PDFs
transactions = parse_universal_pdf("scanned_statement.pdf")
```

### Manual OCR Processing

For direct OCR control:

```python
from backend.ocr_parser import parse_scanned_pdf

# Force OCR processing
transactions = parse_scanned_pdf("scanned_statement.pdf", enhance_quality=True)
```

## Features

### 1. Automatic Image Enhancement
- Contrast adjustment
- Noise reduction
- Automatic rotation correction
- Sharpening for better text recognition

### 2. Smart Text Extraction
- Table detection
- Column alignment
- Multi-page support
- Confidence scoring

### 3. Error Correction
- Fixes common OCR mistakes (O→0, l→1, S→$)
- Date format normalization
- Amount parsing with various formats
- Description cleaning

### 4. Format Support
- US date formats (MM/DD/YYYY)
- European date formats (DD/MM/YYYY)
- Multiple currency symbols ($, €, £)
- Various decimal separators (. and ,)

## Tips for Best Results

### 1. PDF Quality
- Use high-resolution scans (300 DPI or higher)
- Ensure good contrast between text and background
- Avoid skewed or rotated pages
- Use clean, unwrinkled documents

### 2. Supported Formats
✅ **Works well with:**
- Standard bank statement layouts
- Clear table structures
- Black text on white background
- Sans-serif fonts

⚠️ **May have issues with:**
- Handwritten text
- Decorative or script fonts
- Colored backgrounds
- Very small text (< 8pt)

### 3. Performance
- OCR processing is slower than text extraction
- First page is analyzed to detect if OCR is needed
- Large PDFs may take several seconds per page
- Results are cached to avoid reprocessing

## Troubleshooting

### "OCR not available"
- Ensure Tesseract is installed: `tesseract --version`
- Check Python packages: `pip list | grep pytesseract`
- Verify path settings on Windows

### Poor OCR results
- Try enhancing the scan quality
- Ensure proper lighting if photographing
- Use black and white mode for better contrast
- Check if the document is in a supported language

### Missing transactions
- Review the extracted text for formatting issues
- Check if transactions follow standard patterns
- Manually verify the PDF is readable
- Consider preprocessing the image externally

## Examples

### Test with your PDF:
```bash
python3 test_ocr_capabilities.py /path/to/your/scanned_statement.pdf
```

### API Usage:
```bash
curl -X POST "http://localhost:5000/api/convert" \
  -F "file=@scanned_statement.pdf" \
  -F "output_format=csv"
```

The system will automatically detect that OCR is needed and process accordingly.

## Language Support

By default, English is used. To add support for other languages:

```bash
# Install language pack
sudo apt-get install tesseract-ocr-[lang]

# Use in code
custom_config = r'--oem 3 --psm 6 -l eng+fra'  # English + French
```

## Performance Optimization

For faster processing:
1. Pre-process PDFs to reduce file size
2. Use lower DPI (200 instead of 300) for simple documents
3. Process in batches for multiple files
4. Consider using a PDF optimization tool first

## Security Note

OCR processing requires converting PDFs to images, which may temporarily store image files. These are automatically cleaned up, but be aware when processing sensitive documents.