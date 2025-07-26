"""Dedicated parser for Rabobank PDF statements"""

import re
from datetime import datetime
import PyPDF2

def parse_rabobank_date(date_str):
    """Parse Rabobank date format (DD-MM)"""
    # Rabobank uses DD-MM format, we need to add the year
    current_year = datetime.now().year
    
    # Try different date formats
    formats = [
        '%d-%m',  # DD-MM (Rabobank short format)
        '%d-%m-%Y',  # DD-MM-YYYY
        '%d/%m/%Y',  # DD/MM/YYYY
    ]
    
    for fmt in formats:
        try:
            if fmt == '%d-%m':
                # Add current year for short format
                parsed = datetime.strptime(f"{date_str}-{current_year}", '%d-%m-%Y')
            else:
                parsed = datetime.strptime(date_str, fmt)
            return parsed
        except:
            continue
    return None

def extract_rabobank_amount(amount_str):
    """Extract amount from Rabobank format (European number format)"""
    try:
        # Clean the string
        cleaned = amount_str.strip()
        
        # Rabobank uses dots for thousands and comma for decimal
        # Example: 1.234,56
        cleaned = cleaned.replace('.', '').replace(',', '.')
        
        # Convert to float
        return float(cleaned)
    except:
        return None

def parse_rabobank_pdf(pdf_path):
    """Parse Rabobank PDF statement"""
    transactions = []
    
    try:
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            
            for page_num in range(len(pdf_reader.pages)):
                page = pdf_reader.pages[page_num]
                text = page.extract_text()
                lines = text.split('\n')
                
                i = 0
                while i < len(lines):
                    line = lines[i].strip()
                    
                    # Look for transaction start pattern: date followed by type code
                    # Format: DD-MM[type] where type is 'ei', 'bc', 'db', 'id', etc.
                    match = re.match(r'^(\d{2}-\d{2})(ei|bc|db|id|sb|cb|bg|tb|ga|gb|ck|ba)', line)
                    if match:
                        date_str = match.group(1)
                        trans_type = match.group(2)
                        
                        # Parse the rest of the line
                        rest_of_line = line[len(match.group(0)):].strip()
                        
                        # Initialize transaction
                        trans = {
                            'date_string': date_str,
                            'date': parse_rabobank_date(date_str),
                            'type': trans_type,
                            'description': '',
                            'amount': None
                        }
                        
                        # Look for IBAN pattern to identify counterparty
                        iban_match = re.search(r'[A-Z]{2}\d{2}\s*[A-Z0-9\s]+', rest_of_line)
                        if iban_match:
                            trans['counterparty'] = rest_of_line
                            # Amount is usually at the end of the line
                            amount_match = re.search(r'([\d.]+,\d{2})$', rest_of_line)
                            if amount_match:
                                trans['amount_string'] = amount_match.group(1)
                                trans['amount'] = extract_rabobank_amount(amount_match.group(1))
                                # Extract counterparty name (between IBAN and amount)
                                iban_end = iban_match.end()
                                amount_start = amount_match.start()
                                if amount_start > iban_end:
                                    trans['description'] = rest_of_line[iban_end:amount_start].strip()
                        else:
                            # No IBAN, probably a card transaction
                            # Amount is the last number on the line
                            amount_match = re.search(r'([\d.]+,\d{2})$', rest_of_line)
                            if amount_match:
                                trans['amount_string'] = amount_match.group(1)
                                trans['amount'] = extract_rabobank_amount(amount_match.group(1))
                                trans['description'] = rest_of_line[:amount_match.start()].strip()
                            else:
                                trans['description'] = rest_of_line
                        
                        # Look for additional details in next lines
                        j = i + 1
                        details = []
                        while j < len(lines):
                            next_line = lines[j].strip()
                            
                            # Stop if we hit another transaction or certain keywords
                            if (re.match(r'^\d{2}-\d{2}(ei|bc|db|id|sb|cb|bg|tb|ga|gb|ck|ba)', next_line) or
                                next_line.startswith('Verwerkingsdatum:') or
                                next_line.startswith('Transactiereferentie:') or
                                not next_line):
                                break
                            
                            # Skip certain lines
                            if not any(skip in next_line for skip in ['Verwerkingsdatum:', 'Transactiereferentie:', 'Appr Cd:', '. Pas:']):
                                details.append(next_line)
                            
                            j += 1
                        
                        # Combine description with details
                        if details:
                            if trans['description']:
                                trans['description'] += ' ' + ' '.join(details)
                            else:
                                trans['description'] = ' '.join(details)
                        
                        # Make debit amounts negative
                        if trans['amount'] is not None and trans_type in ['bc', 'ei', 'db', 'ba']:
                            trans['amount'] = -abs(trans['amount'])
                        
                        # Only add if we have valid data
                        if trans['date'] and trans['amount'] is not None:
                            transactions.append(trans)
                        
                        i = j - 1  # Continue from where we left off
                    
                    i += 1
                    
    except Exception as e:
        print(f"Error parsing Rabobank PDF: {e}")
        import traceback
        traceback.print_exc()
    
    return transactions