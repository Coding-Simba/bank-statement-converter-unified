#!/usr/bin/env python3
"""
Script to fetch failed PDFs from the past 24 hours from the server
"""

import os
import json
import shutil
from datetime import datetime, timedelta
import paramiko
from scp import SCPClient

# Configuration
SERVER_IP = "3.235.19.83"
SERVER_USER = "ubuntu"
KEY_PATH = "/Users/MAC/Downloads/bank-statement-converter.pem"
REMOTE_FAILED_PDFS_DIR = "/home/ubuntu/bank-statement-converter-unified/backend/failed_pdfs"
LOCAL_FAILED_PDFS_DIR = "./retrieved_failed_pdfs"

def fetch_failed_pdfs_from_server():
    """Fetch failed PDFs from the past 24 hours from the server"""
    
    # Create local directory for failed PDFs
    os.makedirs(LOCAL_FAILED_PDFS_DIR, exist_ok=True)
    
    # Setup SSH connection
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        # Connect to server
        ssh.connect(SERVER_IP, username=SERVER_USER, key_filename=KEY_PATH)
        print(f"Connected to server {SERVER_IP}")
        
        # First, fetch the metadata file to see what failed PDFs exist
        with SCPClient(ssh.get_transport()) as scp:
            metadata_path = f"{REMOTE_FAILED_PDFS_DIR}/failed_pdfs_metadata.json"
            local_metadata_path = os.path.join(LOCAL_FAILED_PDFS_DIR, "failed_pdfs_metadata.json")
            
            try:
                scp.get(metadata_path, local_metadata_path)
                print("Downloaded metadata file")
            except Exception as e:
                print(f"No metadata file found or error downloading: {e}")
                return
        
        # Parse metadata to find PDFs from last 24 hours
        with open(local_metadata_path, 'r') as f:
            metadata = json.load(f)
        
        # Calculate 24 hours ago
        cutoff_time = datetime.now() - timedelta(hours=24)
        
        # Find PDFs saved in the last 24 hours
        recent_pdfs = []
        for file_hash, info in metadata.items():
            try:
                saved_date = datetime.fromisoformat(info.get('date_saved', ''))
                if saved_date > cutoff_time:
                    recent_pdfs.append({
                        'hash': file_hash,
                        'saved_name': info.get('saved_name'),
                        'original_name': info.get('original_name'),
                        'date_saved': info.get('date_saved'),
                        'transactions_found': info.get('transactions_found', 0),
                        'status': info.get('status', 'unknown')
                    })
            except Exception as e:
                print(f"Error parsing date for {file_hash}: {e}")
        
        print(f"\nFound {len(recent_pdfs)} failed PDFs from the last 24 hours:")
        
        # Download each recent PDF
        with SCPClient(ssh.get_transport()) as scp:
            for pdf_info in recent_pdfs:
                saved_name = pdf_info['saved_name']
                if saved_name:
                    remote_path = f"{REMOTE_FAILED_PDFS_DIR}/{saved_name}"
                    local_path = os.path.join(LOCAL_FAILED_PDFS_DIR, saved_name)
                    
                    try:
                        scp.get(remote_path, local_path)
                        print(f"✓ Downloaded: {saved_name}")
                        print(f"  - Original: {pdf_info['original_name']}")
                        print(f"  - Saved at: {pdf_info['date_saved']}")
                        print(f"  - Transactions found: {pdf_info['transactions_found']}")
                        print(f"  - Status: {pdf_info['status']}")
                        print()
                    except Exception as e:
                        print(f"✗ Failed to download {saved_name}: {e}")
        
        # Create summary report
        summary_path = os.path.join(LOCAL_FAILED_PDFS_DIR, "summary_report.txt")
        with open(summary_path, 'w') as f:
            f.write(f"Failed PDFs Report - Generated at {datetime.now()}\n")
            f.write("=" * 80 + "\n\n")
            f.write(f"Total failed PDFs in last 24 hours: {len(recent_pdfs)}\n\n")
            
            for pdf_info in recent_pdfs:
                f.write(f"File: {pdf_info['original_name']}\n")
                f.write(f"  Saved as: {pdf_info['saved_name']}\n")
                f.write(f"  Date: {pdf_info['date_saved']}\n")
                f.write(f"  Transactions: {pdf_info['transactions_found']}\n")
                f.write(f"  Status: {pdf_info['status']}\n")
                f.write("-" * 40 + "\n")
        
        print(f"\nSummary report saved to: {summary_path}")
        
    except Exception as e:
        print(f"Error connecting to server: {e}")
        print("\nAlternative: Run this command when server is accessible:")
        print(f"scp -r -i {KEY_PATH} {SERVER_USER}@{SERVER_IP}:{REMOTE_FAILED_PDFS_DIR} ./")
    
    finally:
        ssh.close()


def fetch_with_simple_commands():
    """Alternative method using simple SSH/SCP commands"""
    print("\nAlternative commands to run manually:\n")
    
    # Create directory
    print(f"1. Create local directory:")
    print(f"   mkdir -p {LOCAL_FAILED_PDFS_DIR}")
    
    # Fetch metadata
    print(f"\n2. Fetch metadata file:")
    print(f"   scp -i {KEY_PATH} {SERVER_USER}@{SERVER_IP}:{REMOTE_FAILED_PDFS_DIR}/failed_pdfs_metadata.json {LOCAL_FAILED_PDFS_DIR}/")
    
    # List files from last 24 hours
    print(f"\n3. List failed PDFs from last 24 hours on server:")
    print(f"   ssh -i {KEY_PATH} {SERVER_USER}@{SERVER_IP} \"find {REMOTE_FAILED_PDFS_DIR} -name '*.pdf' -mtime -1 -ls\"")
    
    # Download all PDFs from last 24 hours
    print(f"\n4. Download all PDFs modified in last 24 hours:")
    print(f"   ssh -i {KEY_PATH} {SERVER_USER}@{SERVER_IP} \"cd {REMOTE_FAILED_PDFS_DIR} && find . -name '*.pdf' -mtime -1 -exec tar -cf - {{}} +\" | tar -xf - -C {LOCAL_FAILED_PDFS_DIR}/")


if __name__ == "__main__":
    print("Attempting to fetch failed PDFs from server...")
    
    # Check if we have the required libraries
    try:
        import paramiko
        from scp import SCPClient
        fetch_failed_pdfs_from_server()
    except ImportError:
        print("Required libraries not installed. Install with:")
        print("  pip install paramiko scp")
        print("\nShowing manual commands instead:")
        fetch_with_simple_commands()