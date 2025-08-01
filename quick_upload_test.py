#!/usr/bin/env python3
"""
Quick Upload Test for bankcsvconverter.com
Tests key file upload functionality and security
"""

import requests
import time
from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import io
import tempfile

def create_test_pdf(filename, size_kb=None):
    """Create a simple test PDF"""
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    p.drawString(100, 750, "Test Bank Statement")
    p.drawString(100, 700, "Date        Description                Amount")
    p.drawString(100, 680, "2024-01-01  Test Transaction 1         -50.00")
    p.drawString(100, 660, "2024-01-02  Test Transaction 2         100.00")
    p.save()
    
    pdf_data = buffer.getvalue()
    
    # Pad to specific size if requested
    if size_kb:
        target_size = size_kb * 1024
        if len(pdf_data) < target_size:
            pdf_data += b' ' * (target_size - len(pdf_data))
    
    with open(filename, 'wb') as f:
        f.write(pdf_data)
    
    return Path(filename)

def test_upload(filepath, description):
    """Test uploading a file"""
    try:
        with open(filepath, 'rb') as f:
            files = {'file': (filepath.name, f, 'application/pdf')}
            response = requests.post(
                "https://bankcsvconverter.com/api/convert",
                files=files,
                timeout=30
            )
        
        print(f"[{response.status_code}] {description}")
        if response.status_code == 200:
            data = response.json()
            print(f"  SUCCESS: File processed, ID: {data.get('id', 'N/A')}")
            return True
        else:
            print(f"  RESPONSE: {response.text[:200]}")
            return False
    
    except Exception as e:
        print(f"[ERROR] {description}: {str(e)}")
        return False

def main():
    print("Quick Upload Test for bankcsvconverter.com")
    print("=" * 50)
    
    results = {}
    
    # Test 1: Standard PDF
    print("\n1. Testing standard PDF upload...")
    pdf_path = create_test_pdf("test_standard.pdf")
    results['standard'] = test_upload(pdf_path, "Standard PDF")
    
    # Test 2: Empty file
    print("\n2. Testing empty file...")
    empty_path = Path("test_empty.pdf")
    empty_path.touch()
    results['empty'] = test_upload(empty_path, "Empty file")
    
    # Test 3: Large file (1MB)
    print("\n3. Testing large file (1MB)...")
    large_path = create_test_pdf("test_large.pdf", size_kb=1024)
    results['large'] = test_upload(large_path, "Large file (1MB)")
    
    # Test 4: Non-PDF file
    print("\n4. Testing non-PDF file...")
    text_path = Path("test_fake.pdf")
    with open(text_path, 'w') as f:
        f.write("This is not a PDF file")
    
    try:
        with open(text_path, 'rb') as f:
            files = {'file': (text_path.name, f, 'text/plain')}
            response = requests.post(
                "https://bankcsvconverter.com/api/convert",
                files=files,
                timeout=30
            )
        print(f"[{response.status_code}] Non-PDF file test")
        results['non_pdf'] = response.status_code in [400, 422]
    except Exception as e:
        print(f"[ERROR] Non-PDF test: {str(e)}")
        results['non_pdf'] = False
    
    # Test 5: Security headers
    print("\n5. Testing security headers...")
    try:
        response = requests.get("https://bankcsvconverter.com", timeout=10)
        headers = response.headers
        
        security_headers = [
            'X-Content-Type-Options',
            'X-Frame-Options', 
            'Strict-Transport-Security',
            'Content-Security-Policy'
        ]
        
        found = [h for h in security_headers if h in headers]
        print(f"  Found security headers: {found}")
        results['security_headers'] = len(found) >= 2
    except Exception as e:
        print(f"  Error testing headers: {str(e)}")
        results['security_headers'] = False
    
    # Summary
    print("\n" + "=" * 50)
    print("QUICK TEST RESULTS:")
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    print(f"Passed: {passed}/{total}")
    
    for test, result in results.items():
        status = "PASS" if result else "FAIL"
        print(f"  [{status}] {test}")
    
    # Cleanup
    for file in ["test_standard.pdf", "test_empty.pdf", "test_large.pdf", "test_fake.pdf"]:
        try:
            Path(file).unlink(missing_ok=True)
        except:
            pass

if __name__ == "__main__":
    main()