"""
Integration Layer for Robust Parser
===================================

Connects the new robust parser architecture to the existing system
while maintaining backward compatibility.
"""

import asyncio
import logging
from typing import List, Dict, Optional
from datetime import datetime
import os
import sys

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from parsers.robust_parser_architecture import (
    BankStatementParser, 
    process_bank_statements,
    Transaction,
    BankStatement
)

logger = logging.getLogger(__name__)

class UniversalParserV2:
    """
    Drop-in replacement for the existing universal_parser.py
    Uses the new robust architecture under the hood.
    """
    
    def __init__(self):
        self.parser = None
        self._loop = None
    
    def _get_event_loop(self):
        """Get or create event loop"""
        try:
            if self._loop is None or self._loop.is_closed():
                self._loop = asyncio.new_event_loop()
                asyncio.set_event_loop(self._loop)
            return self._loop
        except RuntimeError:
            # Create new loop if in different thread
            self._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._loop)
            return self._loop
    
    def parse_universal_pdf(self, pdf_path: str) -> List[Dict]:
        """
        Main entry point - compatible with existing code
        Returns list of transaction dictionaries
        """
        try:
            # Initialize parser if needed
            if self.parser is None:
                self.parser = BankStatementParser(num_workers=4)  # Reduced for single PDF
            
            # Get or create event loop
            loop = self._get_event_loop()
            
            # Parse PDF
            statement = loop.run_until_complete(self.parser.parse_pdf(pdf_path))
            
            if statement is None:
                logger.warning(f"No data extracted from {pdf_path}")
                return []
            
            # Convert to legacy format
            return self._convert_to_legacy_format(statement)
            
        except Exception as e:
            logger.error(f"Failed to parse PDF: {e}")
            return []
    
    def _convert_to_legacy_format(self, statement: BankStatement) -> List[Dict]:
        """Convert BankStatement to legacy transaction format"""
        transactions = []
        
        for tx in statement.transactions:
            transaction = {
                'date': tx.date,
                'date_string': tx.date.strftime('%Y-%m-%d'),
                'description': tx.description,
                'amount': tx.amount,
                'amount_string': f"{tx.amount:.2f}"
            }
            
            # Add optional fields if present
            if tx.balance is not None:
                transaction['balance'] = tx.balance
            
            if tx.reference:
                transaction['reference'] = tx.reference
            
            if tx.transaction_type:
                transaction['type'] = tx.transaction_type
            
            transactions.append(transaction)
        
        return transactions
    
    def __del__(self):
        """Cleanup on deletion"""
        try:
            if self.parser:
                loop = self._get_event_loop()
                loop.run_until_complete(self.parser.close())
            if self._loop and not self._loop.is_closed():
                self._loop.close()
        except:
            pass

# Global instance for backward compatibility
_parser_instance = UniversalParserV2()

def parse_universal_pdf(pdf_path: str) -> List[Dict]:
    """
    Direct replacement for existing parse_universal_pdf function
    """
    return _parser_instance.parse_universal_pdf(pdf_path)

# Bank-specific parser functions for backward compatibility
def parse_bank_of_america(pdf_path: str) -> List[Dict]:
    return parse_universal_pdf(pdf_path)

def parse_wells_fargo(pdf_path: str) -> List[Dict]:
    return parse_universal_pdf(pdf_path)

def parse_chase(pdf_path: str) -> List[Dict]:
    return parse_universal_pdf(pdf_path)

def parse_citizens(pdf_path: str) -> List[Dict]:
    return parse_universal_pdf(pdf_path)

def parse_commonwealth_bank(pdf_path: str) -> List[Dict]:
    return parse_universal_pdf(pdf_path)

def parse_westpac(pdf_path: str) -> List[Dict]:
    return parse_universal_pdf(pdf_path)

def parse_rbc(pdf_path: str) -> List[Dict]:
    return parse_universal_pdf(pdf_path)

# Batch processing for multiple PDFs
async def process_multiple_pdfs(pdf_paths: List[str], num_workers: int = 20) -> Dict[str, any]:
    """
    Process multiple PDFs in parallel
    Returns detailed results with statistics
    """
    start_time = datetime.now()
    
    # Process PDFs
    results = await process_bank_statements(pdf_paths, num_workers=num_workers)
    
    # Calculate statistics
    successful = sum(1 for r in results if 'error' not in r)
    failed = len(results) - successful
    total_transactions = sum(
        len(r.get('transactions', [])) for r in results if 'error' not in r
    )
    
    # Group by bank
    by_bank = {}
    for result in results:
        if 'error' not in result:
            bank = result.get('bank', 'unknown')
            if bank not in by_bank:
                by_bank[bank] = []
            by_bank[bank].append(result)
    
    processing_time = (datetime.now() - start_time).total_seconds()
    
    return {
        'summary': {
            'total_pdfs': len(pdf_paths),
            'successful': successful,
            'failed': failed,
            'total_transactions': total_transactions,
            'processing_time': processing_time,
            'pdfs_per_second': len(pdf_paths) / processing_time if processing_time > 0 else 0
        },
        'by_bank': by_bank,
        'results': results
    }

# CLI for testing
if __name__ == "__main__":
    import sys
    import json
    
    if len(sys.argv) < 2:
        print("Usage: python integration_layer.py <pdf_path> [pdf_path2 ...]")
        sys.exit(1)
    
    pdf_paths = sys.argv[1:]
    
    if len(pdf_paths) == 1:
        # Single PDF - use sync method
        transactions = parse_universal_pdf(pdf_paths[0])
        print(f"Found {len(transactions)} transactions")
        for i, tx in enumerate(transactions[:5]):
            print(f"{i+1}. {tx['date_string']} - {tx['description'][:50]} - ${tx['amount']}")
    else:
        # Multiple PDFs - use async method
        results = asyncio.run(process_multiple_pdfs(pdf_paths))
        print(json.dumps(results['summary'], indent=2))