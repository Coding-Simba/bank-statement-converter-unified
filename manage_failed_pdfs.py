#!/usr/bin/env python3
"""Utility to manage and review failed PDFs"""

import sys
sys.path.append('.')

from backend.failed_pdf_manager import FailedPDFManager
import argparse

def list_failed_pdfs(manager, status=None):
    """List all failed PDFs"""
    pdfs = manager.get_failed_pdfs(status)
    
    if not pdfs:
        print("No failed PDFs found.")
        return
    
    print(f"\nFound {len(pdfs)} failed PDFs:")
    print("-" * 100)
    
    for pdf in pdfs:
        print(f"\nFile: {pdf['original_name']}")
        print(f"  Saved: {pdf['date_saved']}")
        print(f"  Status: {pdf['status']}")
        print(f"  Transactions found: {pdf['transactions_found']}")
        print(f"  Valid transactions: {pdf['valid_transactions']}")
        print(f"  Transactions with dates: {pdf['transactions_with_dates']}")
        print(f"  Hash: {pdf['hash'][:8]}...")
        
        if pdf.get('error_info'):
            print(f"  Error: {pdf['error_info']}")
        
        if pdf.get('sample_transactions'):
            print("  Sample transactions:")
            for trans in pdf['sample_transactions']:
                desc = trans.get('description', 'No description')[:40]
                amount = trans.get('amount', 0)
                date = trans.get('date_string', 'No date')
                print(f"    - {date}: {desc} ${amount}")

def show_statistics(manager):
    """Show statistics about failed PDFs"""
    stats = manager.get_statistics()
    
    print("\nFailed PDF Statistics:")
    print("-" * 50)
    print(f"Total failed PDFs: {stats['total_failed_pdfs']}")
    print(f"Pending review: {stats['pending_review']}")
    print(f"Reviewed: {stats['reviewed']}")
    print(f"Fixed: {stats['fixed']}")
    print(f"\nCommon failures:")
    print(f"  No transactions found: {stats['common_failures']['no_transactions_found']}")
    print(f"  Transactions without dates: {stats['common_failures']['transactions_without_dates']}")
    print(f"\nTotal storage used: {stats['total_size_mb']:.2f} MB")

def update_pdf_status(manager, file_hash, status, notes=None):
    """Update the status of a failed PDF"""
    manager.update_status(file_hash, status, notes)
    print(f"Updated status for {file_hash} to {status}")

def main():
    parser = argparse.ArgumentParser(description='Manage failed PDFs')
    parser.add_argument('command', choices=['list', 'stats', 'update'], 
                       help='Command to execute')
    parser.add_argument('--status', help='Filter by status (pending_review, reviewed, fixed)')
    parser.add_argument('--hash', help='File hash for update command')
    parser.add_argument('--new-status', help='New status for update command')
    parser.add_argument('--notes', help='Notes for update command')
    
    args = parser.parse_args()
    
    manager = FailedPDFManager()
    
    if args.command == 'list':
        list_failed_pdfs(manager, args.status)
    elif args.command == 'stats':
        show_statistics(manager)
    elif args.command == 'update':
        if not args.hash or not args.new_status:
            print("Error: --hash and --new-status are required for update command")
            sys.exit(1)
        update_pdf_status(manager, args.hash, args.new_status, args.notes)

if __name__ == '__main__':
    main()