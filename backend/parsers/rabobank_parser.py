"""Parser for Rabobank (Netherlands) bank statements."""

import re
from datetime import datetime
from typing import List, Dict, Optional
import logging
from pdfplumber import PDF
import PyPDF2
from io import BytesIO

try:
    import pdftotext
    PDFTOTEXT_AVAILABLE = True
except ImportError:
    PDFTOTEXT_AVAILABLE = False

logger = logging.getLogger(__name__)


def parse_rabobank_pdf(pdf_path: str) -> List[Dict]:
    """Parse a Rabobank PDF bank statement and extract transaction data."""
    transactions = []
    
    try:
        # Try pdfplumber first
        with PDF.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages):
                text = page.extract_text()
                if text:
                    # Look for the transaction table
                    lines = text.split('\n')
                    in_transaction_section = False
                    
                    for line in lines:
                        # Start of transactions (after header info)
                        if 'Rente' in line and 'datum' in line and 'Type' in line:
                            in_transaction_section = True
                            continue
                        
                        if in_transaction_section:
                            # Parse transaction lines
                            # Rabobank format: date, type, account, name/description, debit, credit
                            trans = parse_transaction_line(line)
                            if trans:
                                transactions.append(trans)
        
        # If no transactions found, try pdftotext
        if not transactions and PDFTOTEXT_AVAILABLE:
            with open(pdf_path, 'rb') as f:
                pdf = pdftotext.PDF(f)
                full_text = '\n'.join(pdf)
                transactions = extract_transactions_from_text(full_text)
        
        # If still no transactions, try PyPDF2
        if not transactions:
            with open(pdf_path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                for page in reader.pages:
                    text = page.extract_text()
                    page_transactions = extract_transactions_from_text(text)
                    transactions.extend(page_transactions)
        
        logger.info(f"Extracted {len(transactions)} transactions from Rabobank PDF")
        return transactions
        
    except Exception as e:
        logger.error(f"Error parsing Rabobank PDF: {str(e)}")
        return []


def parse_transaction_line(line: str) -> Optional[Dict]:
    """Parse a single transaction line from Rabobank format."""
    # Rabobank format has dates like "02-06" (day-month)
    # Pattern: date, possibly multi-line description, amount
    
    # Date pattern at start of line
    date_pattern = r'^(\d{2}-\d{2})'
    date_match = re.match(date_pattern, line)
    
    if not date_match:
        return None
    
    try:
        # Extract date
        date_str = date_match.group(1)
        
        # Look for amounts (Dutch format: 1.234,56)
        amount_pattern = r'(\d{1,3}(?:\.\d{3})*,\d{2})'
        amounts = re.findall(amount_pattern, line)
        
        if not amounts:
            return None
        
        # Get description - everything between date and first amount
        desc_end = line.find(amounts[0])
        if desc_end > 0:
            description = line[len(date_str):desc_end].strip()
        else:
            description = "Transaction"
        
        # Convert amount from Dutch format to float
        amount_str = amounts[-1]  # Use last amount found
        amount = float(amount_str.replace('.', '').replace(',', '.'))
        
        # Determine if it's debit or credit based on position or context
        # In Rabobank statements, debits are typically in one column, credits in another
        if 'CR' in line or (len(amounts) > 1 and amounts[-1] == amount_str):
            # Credit
            pass
        else:
            # Debit
            amount = -amount
        
        # For the date, we need to determine the year
        # This would be in the statement header
        current_year = datetime.now().year
        
        return {
            'date': f"{date_str}-{current_year}",
            'description': description.strip(),
            'amount': amount,
            'balance': None
        }
        
    except Exception as e:
        logger.debug(f"Could not parse line: {line}. Error: {e}")
        return None


def extract_transactions_from_text(text: str) -> List[Dict]:
    """Extract transactions from full text using pattern matching."""
    transactions = []
    lines = text.split('\n')
    
    # Find year from the statement
    year = None
    year_pattern = r'(\d{4})'
    for line in lines[:20]:  # Check first 20 lines
        if 'Datum vanaf' in line or 'Datum tot' in line:
            year_match = re.search(year_pattern, line)
            if year_match:
                year = year_match.group(1)
                break
    
    if not year:
        year = str(datetime.now().year)
    
    # Look for transaction patterns
    in_transaction_section = False
    
    for i, line in enumerate(lines):
        # Start of transaction section
        if 'Rente' in line and 'datum' in line:
            in_transaction_section = True
            continue
        
        if in_transaction_section and line.strip():
            # Match lines starting with date
            date_match = re.match(r'^(\d{2})-(\d{2})', line)
            if date_match:
                day = date_match.group(1)
                month = date_match.group(2)
                
                # Build the full transaction entry (might span multiple lines)
                full_entry = line
                j = i + 1
                while j < len(lines) and not re.match(r'^\d{2}-\d{2}', lines[j]):
                    if lines[j].strip():
                        full_entry += ' ' + lines[j].strip()
                    j += 1
                
                # Extract amount
                amount_pattern = r'(\d{1,3}(?:\.\d{3})*,\d{2})'
                amounts = re.findall(amount_pattern, full_entry)
                
                if amounts:
                    # Get description
                    desc_match = re.search(r'\d{2}-\d{2}\s+(.+?)(?:\d{1,3}(?:\.\d{3})*,\d{2})', full_entry)
                    description = desc_match.group(1).strip() if desc_match else "Transaction"
                    
                    # Clean description
                    description = re.sub(r'\s+', ' ', description)
                    description = description.replace('  ', ' ').strip()
                    
                    # Convert amount
                    amount_str = amounts[-1]
                    amount = float(amount_str.replace('.', '').replace(',', '.'))
                    
                    # Check if debit or credit
                    # Look for specific patterns or column positions
                    if 'af (debet)' in full_entry or full_entry.count(amount_str) == 1:
                        amount = -amount
                    
                    transactions.append({
                        'date': datetime.strptime(f"{day}-{month}-{year}", "%d-%m-%Y"),
                        'description': description,
                        'amount': amount,
                        'balance': None
                    })
    
    return transactions


def is_rabobank_statement(text: str) -> bool:
    """Check if the PDF is a Rabobank statement."""
    rabobank_indicators = [
        'rabobank',
        'rabo',
        'rabonl2u',
        'rekeningafschrift',
        'rabo basisrekening'
    ]
    
    text_lower = text.lower()
    return any(indicator in text_lower for indicator in rabobank_indicators)