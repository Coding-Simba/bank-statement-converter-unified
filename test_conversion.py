#!/usr/bin/env python3
"""Test the PDF to CSV conversion functionality"""

import requests
import json
import os

# Test file path
pdf_path = "/Users/MAC/Downloads/RA_A_NL13RABO0122118650_EUR_202506.pdf"

# API endpoint
api_url = "http://localhost:5000/api/convert"

# Check if file exists
if not os.path.exists(pdf_path):
    print(f"Error: File not found at {pdf_path}")
    exit(1)

print(f"Testing conversion with: {pdf_path}")

# Prepare the file for upload
with open(pdf_path, 'rb') as f:
    files = {'file': ('bank_statement.pdf', f, 'application/pdf')}
    
    # Make the request
    try:
        # Create a session to maintain cookies
        session = requests.Session()
        response = session.post(api_url, files=files)
        
        if response.status_code == 200:
            result = response.json()
            print("Conversion successful!")
            print(f"Statement ID: {result['id']}")
            print(f"Created at: {result['created_at']}")
            print(f"Original filename: {result['original_filename']}")
            
            # Try to download the converted CSV using the same session
            download_url = f"http://localhost:5000/api/statement/{result['id']}/download"
            download_response = session.get(download_url)
            
            if download_response.status_code == 200:
                # Save the CSV
                csv_filename = f"converted_{result['id']}.csv"
                with open(csv_filename, 'w') as csv_file:
                    csv_file.write(download_response.text)
                print(f"\nCSV saved to: {csv_filename}")
                print("\nFirst 10 lines of CSV:")
                print("-" * 50)
                lines = download_response.text.split('\n')[:10]
                for line in lines:
                    print(line)
            else:
                print(f"Download failed: {download_response.status_code}")
                print(download_response.text)
        else:
            print(f"Conversion failed: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"Error: {e}")