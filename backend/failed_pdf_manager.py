"""Manager for handling failed PDF parsing attempts"""

import os
import shutil
import json
import hashlib
from datetime import datetime
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

class FailedPDFManager:
    """Manages PDFs that fail to parse correctly"""
    
    def __init__(self, failed_pdfs_dir: str = "failed_pdfs"):
        """Initialize the failed PDF manager
        
        Args:
            failed_pdfs_dir: Directory to store failed PDFs
        """
        self.failed_pdfs_dir = failed_pdfs_dir
        self.metadata_file = os.path.join(failed_pdfs_dir, "failed_pdfs_metadata.json")
        
        # Create directory if it doesn't exist
        os.makedirs(failed_pdfs_dir, exist_ok=True)
        
        # Load existing metadata
        self.metadata = self._load_metadata()
    
    def _load_metadata(self) -> Dict:
        """Load metadata about failed PDFs"""
        if os.path.exists(self.metadata_file):
            try:
                with open(self.metadata_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading metadata: {e}")
                return {}
        return {}
    
    def _save_metadata(self):
        """Save metadata to file"""
        try:
            with open(self.metadata_file, 'w') as f:
                json.dump(self.metadata, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Error saving metadata: {e}")
    
    def _get_file_hash(self, file_path: str) -> str:
        """Generate SHA256 hash of file"""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    
    def check_parsing_success(self, pdf_path: str, transactions: List[Dict]) -> bool:
        """Check if PDF was parsed successfully
        
        Args:
            pdf_path: Path to the PDF file
            transactions: List of extracted transactions
            
        Returns:
            True if parsing was successful, False otherwise
        """
        # Define criteria for successful parsing
        if not transactions:
            logger.info(f"No transactions found in {pdf_path}")
            return False
        
        # Check if transactions have required fields
        valid_transactions = 0
        for trans in transactions:
            # A valid transaction should have at least a description or amount
            if trans.get('description') or trans.get('amount') is not None:
                # Check if amount is reasonable (not 0 or extremely large)
                amount = trans.get('amount', 0)
                if amount != 0 and abs(amount) < 1000000:  # Less than 1 million
                    valid_transactions += 1
        
        # Consider it a failure if less than 50% of transactions are valid
        if valid_transactions < len(transactions) * 0.5:
            logger.info(f"Only {valid_transactions}/{len(transactions)} valid transactions found")
            return False
        
        # Check if most transactions are missing dates
        transactions_with_dates = sum(1 for t in transactions if t.get('date'))
        if transactions_with_dates < len(transactions) * 0.3:  # Less than 30% have dates
            logger.info(f"Only {transactions_with_dates}/{len(transactions)} transactions have dates")
            return False
        
        return True
    
    def save_failed_pdf(self, pdf_path: str, transactions: List[Dict], 
                       error_info: Optional[str] = None) -> Optional[str]:
        """Save a PDF that failed to parse correctly
        
        Args:
            pdf_path: Path to the original PDF
            transactions: List of extracted transactions (if any)
            error_info: Additional error information
            
        Returns:
            Path to saved file if successful, None otherwise
        """
        try:
            # Get file hash to avoid duplicates
            file_hash = self._get_file_hash(pdf_path)
            
            # Check if we already have this PDF
            if file_hash in self.metadata:
                logger.info(f"PDF already saved with hash {file_hash}")
                return None
            
            # Generate filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            original_name = os.path.basename(pdf_path)
            saved_name = f"{timestamp}_{file_hash[:8]}_{original_name}"
            saved_path = os.path.join(self.failed_pdfs_dir, saved_name)
            
            # Copy the PDF
            shutil.copy2(pdf_path, saved_path)
            
            # Save metadata
            self.metadata[file_hash] = {
                'original_name': original_name,
                'saved_name': saved_name,
                'saved_path': saved_path,
                'timestamp': timestamp,
                'date_saved': datetime.now().isoformat(),
                'transactions_found': len(transactions),
                'valid_transactions': sum(1 for t in transactions if t.get('amount') is not None),
                'transactions_with_dates': sum(1 for t in transactions if t.get('date')),
                'error_info': error_info,
                'sample_transactions': transactions[:3] if transactions else [],  # Save first 3 as sample
                'file_size': os.path.getsize(pdf_path),
                'status': 'pending_review'
            }
            
            self._save_metadata()
            
            logger.info(f"Saved failed PDF to {saved_path}")
            return saved_path
            
        except Exception as e:
            logger.error(f"Error saving failed PDF: {e}")
            return None
    
    def get_failed_pdfs(self, status: Optional[str] = None) -> List[Dict]:
        """Get list of failed PDFs
        
        Args:
            status: Filter by status (pending_review, reviewed, fixed)
            
        Returns:
            List of failed PDF metadata
        """
        pdfs = []
        for file_hash, info in self.metadata.items():
            if status is None or info.get('status') == status:
                pdfs.append({
                    'hash': file_hash,
                    **info
                })
        
        # Sort by date saved (newest first)
        pdfs.sort(key=lambda x: x.get('date_saved', ''), reverse=True)
        return pdfs
    
    def update_status(self, file_hash: str, status: str, notes: Optional[str] = None):
        """Update the status of a failed PDF
        
        Args:
            file_hash: Hash of the PDF file
            status: New status (pending_review, reviewed, fixed)
            notes: Optional notes about the fix
        """
        if file_hash in self.metadata:
            self.metadata[file_hash]['status'] = status
            self.metadata[file_hash]['last_updated'] = datetime.now().isoformat()
            if notes:
                self.metadata[file_hash]['notes'] = notes
            self._save_metadata()
            logger.info(f"Updated status for {file_hash} to {status}")
    
    def get_statistics(self) -> Dict:
        """Get statistics about failed PDFs"""
        total = len(self.metadata)
        pending = sum(1 for info in self.metadata.values() if info.get('status') == 'pending_review')
        reviewed = sum(1 for info in self.metadata.values() if info.get('status') == 'reviewed')
        fixed = sum(1 for info in self.metadata.values() if info.get('status') == 'fixed')
        
        # Calculate common failure patterns
        no_transactions = sum(1 for info in self.metadata.values() if info.get('transactions_found', 0) == 0)
        no_dates = sum(1 for info in self.metadata.values() 
                      if info.get('transactions_found', 0) > 0 and info.get('transactions_with_dates', 0) == 0)
        
        return {
            'total_failed_pdfs': total,
            'pending_review': pending,
            'reviewed': reviewed,
            'fixed': fixed,
            'common_failures': {
                'no_transactions_found': no_transactions,
                'transactions_without_dates': no_dates,
            },
            'total_size_mb': sum(info.get('file_size', 0) for info in self.metadata.values()) / (1024 * 1024)
        }