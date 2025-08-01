#!/usr/bin/env python3
"""
Test concurrent uploads and file cleanup
"""

import requests
import threading
import time
from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import io

def create_test_pdf(filename):
    """Create a simple test PDF"""
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    p.drawString(100, 750, f"Test Bank Statement - {filename}")
    p.drawString(100, 700, "Date        Description                Amount")
    p.drawString(100, 680, "2024-01-01  Test Transaction 1         -50.00")
    p.drawString(100, 660, "2024-01-02  Test Transaction 2         100.00")
    p.save()
    
    with open(filename, 'wb') as f:
        f.write(buffer.getvalue())
    
    return Path(filename)

def upload_worker(worker_id, results):
    """Worker function for concurrent uploads"""
    try:
        pdf_path = create_test_pdf(f"concurrent_{worker_id}.pdf")
        
        with open(pdf_path, 'rb') as f:
            files = {'file': (pdf_path.name, f, 'application/pdf')}
            response = requests.post(
                "https://bankcsvconverter.com/api/convert",
                files=files,
                timeout=45
            )
        
        results[worker_id] = {
            'status': response.status_code,
            'success': response.status_code == 200,
            'response_data': response.json() if response.status_code == 200 else None
        }
        
        print(f"Worker {worker_id}: {response.status_code}")
        
        # Cleanup
        pdf_path.unlink(missing_ok=True)
        
    except Exception as e:
        results[worker_id] = {
            'status': 'ERROR',
            'success': False,
            'error': str(e)
        }
        print(f"Worker {worker_id} error: {str(e)}")

def test_concurrent_uploads():
    """Test concurrent file uploads"""
    print("Testing concurrent uploads...")
    
    results = {}
    threads = []
    
    # Start 5 concurrent uploads
    for i in range(5):
        thread = threading.Thread(target=upload_worker, args=(i, results))
        threads.append(thread)
        thread.start()
    
    # Wait for all to complete
    for thread in threads:
        thread.join()
    
    # Analyze results
    successful = sum(1 for r in results.values() if r['success'])
    total = len(results)
    
    print(f"\nConcurrent Upload Results: {successful}/{total} successful")
    
    for worker_id, result in results.items():
        status = "SUCCESS" if result['success'] else f"FAILED ({result['status']})"
        print(f"  Worker {worker_id}: {status}")
    
    return successful >= 3

def test_file_cleanup():
    """Test if uploaded files are cleaned up"""
    print("\nTesting file cleanup...")
    
    # Upload a file
    pdf_path = create_test_pdf("cleanup_test.pdf")
    
    try:
        with open(pdf_path, 'rb') as f:
            files = {'file': (pdf_path.name, f, 'application/pdf')}
            response = requests.post(
                "https://bankcsvconverter.com/api/convert",
                files=files,
                timeout=30
            )
        
        if response.status_code == 200:
            data = response.json()
            file_id = data['id']
            
            print(f"File uploaded successfully, ID: {file_id}")
            
            # Try to download immediately
            download_url = f"https://bankcsvconverter.com/api/statement/{file_id}/download"
            download_response = requests.get(download_url, timeout=10)
            
            if download_response.status_code == 200:
                print("  File accessible immediately after upload")
                
                # Wait 5 minutes and check again
                print("  Waiting 5 minutes to test cleanup...")
                time.sleep(300)  # 5 minutes
                
                late_response = requests.get(download_url, timeout=10)
                if late_response.status_code == 200:
                    print("  WARNING: File still accessible after 5 minutes")
                    return False
                else:
                    print(f"  File cleaned up properly (status: {late_response.status_code})")
                    return True
            else:
                print(f"  File not accessible (status: {download_response.status_code})")
                return True
        else:
            print(f"Upload failed: {response.status_code}")
            return False
    
    except Exception as e:
        print(f"Cleanup test error: {str(e)}")
        return False
    
    finally:
        pdf_path.unlink(missing_ok=True)

def test_file_storage_security():
    """Test file storage security"""
    print("\nTesting file storage security...")
    
    # Upload a file
    pdf_path = create_test_pdf("security_test.pdf")
    
    try:
        with open(pdf_path, 'rb') as f:
            files = {'file': (pdf_path.name, f, 'application/pdf')}
            response = requests.post(
                "https://bankcsvconverter.com/api/convert",
                files=files,
                timeout=30
            )
        
        if response.status_code == 200:
            data = response.json()
            filename = data['filename']
            
            # Try common upload directories
            test_urls = [
                f"https://bankcsvconverter.com/uploads/{filename}",
                f"https://bankcsvconverter.com/files/{filename}",
                f"https://bankcsvconverter.com/temp/{filename}",
                f"https://bankcsvconverter.com/static/{filename}",
                f"https://bankcsvconverter.com/backend/uploads/{filename}"
            ]
            
            accessible = []
            for url in test_urls:
                try:
                    test_response = requests.get(url, timeout=5)
                    if test_response.status_code == 200:
                        accessible.append(url)
                except:
                    pass
            
            if accessible:
                print(f"  SECURITY ISSUE: Files accessible at: {accessible}")
                return False
            else:
                print("  Files properly secured - not directly accessible")
                return True
        
        else:
            print(f"Upload failed: {response.status_code}")
            return False
    
    except Exception as e:
        print(f"Security test error: {str(e)}")
        return False
    
    finally:
        pdf_path.unlink(missing_ok=True)

def main():
    print("File Upload Robustness Testing")
    print("=" * 40)
    
    results = {}
    
    # Test concurrent uploads
    results['concurrent'] = test_concurrent_uploads()
    
    # Test file storage security
    results['storage_security'] = test_file_storage_security()
    
    # Test file cleanup (this takes 5+ minutes)
    # Commented out for quick testing
    # results['cleanup'] = test_file_cleanup()
    
    print("\n" + "=" * 40)
    print("ROBUSTNESS TEST RESULTS:")
    for test, result in results.items():
        status = "PASS" if result else "FAIL"
        print(f"  [{status}] {test}")

if __name__ == "__main__":
    main()