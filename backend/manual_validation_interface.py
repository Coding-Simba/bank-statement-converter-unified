#!/usr/bin/env python3
"""
Manual validation interface for bank statement extraction
Allows users to review and correct extracted transactions
"""
import json
import os
from typing import List, Dict, Optional, Tuple
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class TransactionValidator:
    """Interface for manual validation of extracted transactions"""
    
    def __init__(self, pdf_path: str, extracted_transactions: List[Dict]):
        self.pdf_path = pdf_path
        self.original_transactions = extracted_transactions
        self.validated_transactions = []
        self.validation_metadata = {
            'pdf_path': pdf_path,
            'extraction_timestamp': datetime.now().isoformat(),
            'original_count': len(extracted_transactions),
            'validation_status': 'pending'
        }
    
    def generate_validation_report(self) -> Dict:
        """Generate a report for manual validation"""
        report = {
            'metadata': self.validation_metadata,
            'transactions': [],
            'summary': {
                'total_transactions': len(self.original_transactions),
                'total_credits': 0,
                'total_debits': 0,
                'suspicious_amounts': [],
                'missing_dates': [],
                'missing_descriptions': []
            }
        }
        
        for i, trans in enumerate(self.original_transactions):
            date = trans.get('date_string', '')
            desc = trans.get('description', '')
            amount = trans.get('amount', 0)
            
            # Flag issues
            issues = []
            if not date:
                issues.append('missing_date')
                report['summary']['missing_dates'].append(i)
            if not desc:
                issues.append('missing_description')
                report['summary']['missing_descriptions'].append(i)
            if abs(amount) > 10000:
                issues.append('large_amount')
                report['summary']['suspicious_amounts'].append({
                    'index': i,
                    'amount': amount
                })
            
            # Add to report
            trans_info = {
                'index': i,
                'date': date,
                'description': desc,
                'amount': amount,
                'issues': issues,
                'confidence': self._calculate_confidence(trans),
                'needs_review': len(issues) > 0
            }
            
            report['transactions'].append(trans_info)
            
            # Update summary
            if amount > 0:
                report['summary']['total_credits'] += amount
            else:
                report['summary']['total_debits'] += amount
        
        return report
    
    def _calculate_confidence(self, transaction: Dict) -> float:
        """Calculate confidence score for a transaction"""
        confidence = 1.0
        
        # Reduce confidence for missing fields
        if not transaction.get('date_string'):
            confidence -= 0.3
        if not transaction.get('description'):
            confidence -= 0.2
        if transaction.get('amount', 0) == 0:
            confidence -= 0.3
        
        # Reduce confidence for suspicious amounts
        amount = abs(transaction.get('amount', 0))
        if amount > 100000:
            confidence -= 0.5
        elif amount > 10000:
            confidence -= 0.2
        
        return max(0, confidence)
    
    def save_validation_template(self, output_path: str):
        """Save validation template to JSON for manual review"""
        report = self.generate_validation_report()
        
        # Add instructions
        report['instructions'] = {
            'review_process': [
                '1. Review each transaction marked with needs_review=true',
                '2. Verify dates are in correct format (MM/DD/YYYY)',
                '3. Check amounts are reasonable for the transaction type',
                '4. Ensure descriptions match the transaction',
                '5. Mark validated=true when correct or after correction',
                '6. Add correction notes if changes were made'
            ],
            'fields_to_update': {
                'date': 'Correct date in MM/DD/YYYY format',
                'description': 'Clear description of the transaction',
                'amount': 'Positive for credits, negative for debits',
                'validated': 'Set to true after review',
                'correction_notes': 'Explain any changes made'
            }
        }
        
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Validation template saved to {output_path}")
        return output_path
    
    def load_validated_data(self, validated_path: str) -> List[Dict]:
        """Load manually validated data"""
        with open(validated_path, 'r') as f:
            data = json.load(f)
        
        validated_transactions = []
        
        for trans in data['transactions']:
            if trans.get('validated', False):
                validated_transactions.append({
                    'date_string': trans['date'],
                    'description': trans['description'],
                    'amount': trans['amount'],
                    'validated': True,
                    'correction_notes': trans.get('correction_notes', '')
                })
        
        self.validated_transactions = validated_transactions
        self.validation_metadata['validation_completed'] = datetime.now().isoformat()
        self.validation_metadata['validated_count'] = len(validated_transactions)
        self.validation_metadata['validation_status'] = 'completed'
        
        return validated_transactions
    
    def generate_final_csv(self, transactions: List[Dict]) -> str:
        """Generate final CSV from validated transactions"""
        csv_lines = ['Date,Description,Amount,Type']
        
        for trans in transactions:
            date = trans.get('date_string', '')
            desc = trans.get('description', '').replace(',', ';')  # Escape commas
            amount = trans.get('amount', 0)
            trans_type = 'Credit' if amount > 0 else 'Debit'
            
            csv_lines.append(f'{date},{desc},{abs(amount):.2f},{trans_type}')
        
        return '\n'.join(csv_lines)

def create_validation_interface(pdf_path: str, transactions: List[Dict]) -> str:
    """Create validation interface for extracted transactions"""
    validator = TransactionValidator(pdf_path, transactions)
    
    # Generate output filename
    base_name = os.path.splitext(os.path.basename(pdf_path))[0]
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_path = f'validation_{base_name}_{timestamp}.json'
    
    # Save validation template
    validator.save_validation_template(output_path)
    
    return output_path

def process_validated_file(validated_json_path: str, original_pdf_path: str, 
                         original_transactions: List[Dict]) -> Tuple[List[Dict], str]:
    """Process manually validated JSON file"""
    validator = TransactionValidator(original_pdf_path, original_transactions)
    
    # Load validated data
    validated_trans = validator.load_validated_data(validated_json_path)
    
    # Generate final CSV
    csv_content = validator.generate_final_csv(validated_trans)
    
    # Save CSV
    csv_path = validated_json_path.replace('.json', '.csv')
    with open(csv_path, 'w') as f:
        f.write(csv_content)
    
    return validated_trans, csv_path