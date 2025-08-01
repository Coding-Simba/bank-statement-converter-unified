#!/usr/bin/env python3
"""
Comprehensive File Upload Test Suite for bankcsvconverter.com
Tests various PDF formats, file sizes, security aspects, and robustness
"""

import requests
import time
import os
import subprocess
import tempfile
from pathlib import Path
import json
from datetime import datetime
import threading
import hashlib
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import io

class UploadTestSuite:
    def __init__(self):
        self.base_url = "https://bankcsvconverter.com"
        self.api_url = f"{self.base_url}/api"
        self.results = {}
        self.test_files_dir = Path("test_files")
        self.test_files_dir.mkdir(exist_ok=True)
        
    def log_result(self, test_name, result, details=""):
        """Log test results"""
        self.results[test_name] = {
            "result": result,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        print(f"[{result.upper()}] {test_name}: {details}")
    
    def create_test_pdf(self, filename, content="Test bank statement", pages=1, size_kb=None):
        """Create a test PDF file"""
        filepath = self.test_files_dir / filename
        
        # Create PDF
        buffer = io.BytesIO()
        p = canvas.Canvas(buffer, pagesize=letter)
        
        for page in range(pages):
            p.drawString(100, 750 - (page * 50), f"{content} - Page {page + 1}")
            p.drawString(100, 700, "Date        Description                Amount")
            p.drawString(100, 680, "2024-01-01  Test Transaction 1         -50.00")
            p.drawString(100, 660, "2024-01-02  Test Transaction 2         100.00")
            p.drawString(100, 640, "2024-01-03  Test Transaction 3         -25.50")
            if page < pages - 1:
                p.showPage()
        
        p.save()
        pdf_data = buffer.getvalue()
        
        # If specific size requested, pad or truncate
        if size_kb:
            target_size = size_kb * 1024
            if len(pdf_data) < target_size:
                # Pad with whitespace
                pdf_data += b' ' * (target_size - len(pdf_data))
            elif len(pdf_data) > target_size:
                # This is approximate - in real scenario, we'd recreate the PDF
                pdf_data = pdf_data[:target_size]
        
        with open(filepath, 'wb') as f:
            f.write(pdf_data)
        
        return filepath
    
    def create_corrupted_pdf(self, filename):
        """Create a corrupted PDF file"""
        filepath = self.test_files_dir / filename
        with open(filepath, 'wb') as f:
            # Write partial PDF header and corrupt data
            f.write(b'%PDF-1.4\n')
            f.write(b'This is not valid PDF content' * 100)
        return filepath
    
    def create_non_pdf_file(self, filename, content="Not a PDF"):
        """Create a non-PDF file"""
        filepath = self.test_files_dir / filename
        with open(filepath, 'w') as f:
            f.write(content)
        return filepath
    
    def upload_file(self, filepath, timeout=30):
        """Upload a file to the API"""
        try:
            with open(filepath, 'rb') as f:
                files = {'file': (filepath.name, f, 'application/pdf')}
                response = requests.post(
                    f"{self.api_url}/convert",
                    files=files,
                    timeout=timeout
                )
            return response
        except Exception as e:
            return None, str(e)
    
    def test_various_pdf_formats(self):
        """Test 1: Various PDF formats"""
        print("\n=== Testing Various PDF Formats ===")
        
        # Standard PDF
        pdf_path = self.create_test_pdf("standard.pdf", "Standard Bank Statement")
        response = self.upload_file(pdf_path)
        if response and response.status_code == 200:
            self.log_result("standard_pdf", "PASS", "Standard PDF uploaded successfully")
        else:
            status = response.status_code if response else "TIMEOUT"
            self.log_result("standard_pdf", "FAIL", f"Status: {status}")
        
        # Multi-page PDF
        pdf_path = self.create_test_pdf("multipage.pdf", "Multi-page Statement", pages=5)
        response = self.upload_file(pdf_path)
        if response and response.status_code == 200:
            self.log_result("multipage_pdf", "PASS", "Multi-page PDF uploaded successfully")
        else:
            status = response.status_code if response else "TIMEOUT"
            self.log_result("multipage_pdf", "FAIL", f"Status: {status}")
        
        # Large PDF (simulated)
        pdf_path = self.create_test_pdf("large.pdf", "Large Statement", pages=1, size_kb=500)
        response = self.upload_file(pdf_path)
        if response and response.status_code == 200:
            self.log_result("large_pdf", "PASS", "Large PDF uploaded successfully")
        else:
            status = response.status_code if response else "TIMEOUT"
            self.log_result("large_pdf", "FAIL", f"Status: {status}")
    
    def test_file_size_validation(self):
        """Test 2: File size validation"""
        print("\n=== Testing File Size Validation ===")
        
        # Empty file
        empty_path = self.test_files_dir / "empty.pdf"
        empty_path.touch()
        response = self.upload_file(empty_path)
        if response and response.status_code in [400, 422]:
            self.log_result("empty_file", "PASS", "Empty file rejected appropriately")
        else:
            status = response.status_code if response else "TIMEOUT"
            self.log_result("empty_file", "FAIL", f"Unexpected status: {status}")
        
        # Very large file (simulated 50MB+)
        try:
            large_path = self.create_test_pdf("very_large.pdf", "Very Large PDF", pages=1, size_kb=50*1024)
            response = self.upload_file(large_path, timeout=60)
            if response and response.status_code in [413, 400]:
                self.log_result("oversized_file", "PASS", "Oversized file rejected")
            elif response and response.status_code == 200:
                self.log_result("oversized_file", "WARNING", "Large file accepted - no size limit detected")
            else:
                status = response.status_code if response else "TIMEOUT"
                self.log_result("oversized_file", "FAIL", f"Unexpected response: {status}")
        except Exception as e:
            self.log_result("oversized_file", "ERROR", f"Test error: {str(e)}")
    
    def test_concurrent_uploads(self):
        """Test 3: Concurrent uploads"""
        print("\n=== Testing Concurrent Uploads ===")
        
        def upload_worker(worker_id):
            pdf_path = self.create_test_pdf(f"concurrent_{worker_id}.pdf", f"Concurrent Upload {worker_id}")
            response = self.upload_file(pdf_path)
            return worker_id, response
        
        # Test with 5 concurrent uploads
        threads = []
        results = []
        
        for i in range(5):
            thread = threading.Thread(target=lambda i=i: results.append(upload_worker(i)))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads
        for thread in threads:
            thread.join()
        
        success_count = sum(1 for _, resp in results if resp and resp.status_code == 200)
        
        if success_count >= 3:
            self.log_result("concurrent_uploads", "PASS", f"{success_count}/5 concurrent uploads succeeded")
        else:
            self.log_result("concurrent_uploads", "FAIL", f"Only {success_count}/5 uploads succeeded")
    
    def test_malformed_files(self):
        """Test 5: Malformed files"""
        print("\n=== Testing Malformed Files ===")
        
        # Corrupted PDF
        corrupt_path = self.create_corrupted_pdf("corrupted.pdf")
        response = self.upload_file(corrupt_path)
        if response and response.status_code in [400, 422, 500]:
            self.log_result("corrupted_pdf", "PASS", "Corrupted PDF handled appropriately")
        else:
            status = response.status_code if response else "TIMEOUT"
            self.log_result("corrupted_pdf", "FAIL", f"Unexpected status: {status}")
        
        # Non-PDF file with PDF extension
        non_pdf_path = self.create_non_pdf_file("fake.pdf", "This is not a PDF file")
        response = self.upload_file(non_pdf_path)
        if response and response.status_code in [400, 422]:
            self.log_result("fake_pdf", "PASS", "Non-PDF file rejected")
        else:
            status = response.status_code if response else "TIMEOUT"
            self.log_result("fake_pdf", "FAIL", f"Unexpected status: {status}")
        
        # Text file
        txt_path = self.create_non_pdf_file("document.txt", "Plain text document")
        try:
            with open(txt_path, 'rb') as f:
                files = {'file': (txt_path.name, f, 'text/plain')}
                response = requests.post(f"{self.api_url}/convert", files=files, timeout=30)
            
            if response.status_code in [400, 422]:
                self.log_result("text_file", "PASS", "Text file rejected")
            else:
                self.log_result("text_file", "FAIL", f"Text file accepted: {response.status_code}")
        except Exception as e:
            self.log_result("text_file", "ERROR", f"Test error: {str(e)}")
    
    def test_file_cleanup(self):
        """Test 4: Verify file cleanup"""
        print("\n=== Testing File Cleanup ===")
        
        # Upload a file and check if it gets cleaned up
        pdf_path = self.create_test_pdf("cleanup_test.pdf", "File Cleanup Test")
        response = self.upload_file(pdf_path)
        
        if response and response.status_code == 200:
            result_data = response.json()
            
            # Wait a bit and check if we can still access the file
            time.sleep(2)
            
            # Try to download the converted file
            try:
                download_url = f"{self.api_url}/statement/{result_data['id']}/download"
                download_response = requests.get(download_url, timeout=10)
                
                if download_response.status_code == 200:
                    self.log_result("file_cleanup", "WARNING", "File still accessible after conversion")
                else:
                    self.log_result("file_cleanup", "INFO", "File access controlled after conversion")
            except Exception as e:
                self.log_result("file_cleanup", "INFO", f"File access test failed: {str(e)}")
        else:
            self.log_result("file_cleanup", "SKIP", "Cannot test cleanup - upload failed")
    
    def test_security_headers(self):
        """Test 6: Check security headers and measures"""
        print("\n=== Testing Security Headers ===")
        
        # Check main site security headers
        try:
            response = requests.get(self.base_url, timeout=10)
            headers = response.headers
            
            security_headers = {
                'X-Content-Type-Options': 'nosniff',
                'X-Frame-Options': 'DENY',
                'X-XSS-Protection': '1; mode=block',
                'Strict-Transport-Security': 'max-age=',
                'Content-Security-Policy': 'default-src'
            }
            
            found_headers = []
            for header, expected_value in security_headers.items():
                if header in headers and expected_value in headers[header]:
                    found_headers.append(header)
            
            if len(found_headers) >= 2:
                self.log_result("security_headers", "PASS", f"Found security headers: {found_headers}")
            else:
                self.log_result("security_headers", "WARNING", f"Limited security headers: {found_headers}")
        
        except Exception as e:
            self.log_result("security_headers", "ERROR", f"Cannot test headers: {str(e)}")
    
    def test_file_storage_permissions(self):
        """Test 8: File permissions and storage"""
        print("\n=== Testing File Storage Security ===")
        
        # Upload a file and try to access it directly
        pdf_path = self.create_test_pdf("storage_test.pdf", "Storage Security Test")
        response = self.upload_file(pdf_path)
        
        if response and response.status_code == 200:
            result_data = response.json()
            
            # Try to guess file storage locations
            potential_paths = [
                f"{self.base_url}/uploads/{result_data['filename']}",
                f"{self.base_url}/files/{result_data['filename']}",
                f"{self.base_url}/temp/{result_data['filename']}",
                f"{self.base_url}/static/{result_data['filename']}"
            ]
            
            accessible_files = []
            for path in potential_paths:
                try:
                    test_response = requests.get(path, timeout=5)
                    if test_response.status_code == 200:
                        accessible_files.append(path)
                except:
                    pass
            
            if accessible_files:
                self.log_result("file_storage", "FAIL", f"Files accessible at: {accessible_files}")
            else:
                self.log_result("file_storage", "PASS", "Files not directly accessible")
        else:
            self.log_result("file_storage", "SKIP", "Cannot test storage - upload failed")
    
    def test_virus_scanning(self):
        """Test 6: Check for virus scanning capabilities"""
        print("\n=== Testing Virus Scanning ===")
        
        # Create a test file with EICAR test string (harmless virus test)
        eicar_string = r'X5O!P%@AP[4\PZX54(P^)7CC)7}$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*'
        
        # Create a PDF with potentially suspicious content
        suspicious_path = self.test_files_dir / "suspicious.pdf"
        try:
            # Create a basic PDF structure with the test string
            with open(suspicious_path, 'wb') as f:
                f.write(b'%PDF-1.4\n')
                f.write(f'Test content with suspicious pattern: {eicar_string}'.encode())
                f.write(b'\n%%EOF')
            
            response = self.upload_file(suspicious_path)
            
            if response and response.status_code in [400, 403, 422]:
                self.log_result("virus_scanning", "PASS", "Suspicious file rejected")
            elif response and response.status_code == 200:
                self.log_result("virus_scanning", "WARNING", "Suspicious file accepted - no virus scanning detected")
            else:
                status = response.status_code if response else "TIMEOUT"
                self.log_result("virus_scanning", "INFO", f"Unexpected response: {status}")
        
        except Exception as e:
            self.log_result("virus_scanning", "ERROR", f"Test error: {str(e)}")
    
    def run_all_tests(self):
        """Run all test suites"""
        print("Starting Comprehensive Upload Test Suite")
        print(f"Target: {self.base_url}")
        print("=" * 50)
        
        start_time = time.time()
        
        try:
            self.test_various_pdf_formats()
            self.test_file_size_validation()
            self.test_concurrent_uploads()
            self.test_file_cleanup()
            self.test_malformed_files()
            self.test_virus_scanning()
            self.test_security_headers()
            self.test_file_storage_permissions()
        except KeyboardInterrupt:
            print("\nTest suite interrupted by user")
        except Exception as e:
            print(f"\nTest suite error: {str(e)}")
        
        end_time = time.time()
        
        # Generate report
        self.generate_report(end_time - start_time)
    
    def generate_report(self, duration):
        """Generate final test report"""
        print("\n" + "=" * 50)
        print("COMPREHENSIVE UPLOAD TEST REPORT")
        print("=" * 50)
        
        total_tests = len(self.results)
        passed = sum(1 for r in self.results.values() if r['result'] == 'PASS')
        failed = sum(1 for r in self.results.values() if r['result'] == 'FAIL')
        warnings = sum(1 for r in self.results.values() if r['result'] == 'WARNING')
        errors = sum(1 for r in self.results.values() if r['result'] == 'ERROR')
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed}")
        print(f"Failed: {failed}")
        print(f"Warnings: {warnings}")
        print(f"Errors: {errors}")
        print(f"Duration: {duration:.2f} seconds")
        print()
        
        # Detailed results
        for test_name, result in self.results.items():
            status = result['result']
            details = result['details']
            print(f"[{status}] {test_name}: {details}")
        
        # Save report to file
        report_file = f"upload_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump({
                'summary': {
                    'total_tests': total_tests,
                    'passed': passed,
                    'failed': failed,
                    'warnings': warnings,
                    'errors': errors,
                    'duration': duration,
                    'timestamp': datetime.now().isoformat()
                },
                'results': self.results
            }, f, indent=2)
        
        print(f"\nDetailed report saved to: {report_file}")

if __name__ == "__main__":
    # Install required dependencies if needed
    try:
        import reportlab
    except ImportError:
        print("Installing reportlab...")
        subprocess.check_call(["pip", "install", "reportlab"])
        import reportlab
    
    test_suite = UploadTestSuite()
    test_suite.run_all_tests()