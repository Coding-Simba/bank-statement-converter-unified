"""Parser for bank statements that only show summary information without transaction details"""

import re
from datetime import datetime

def parse_summary_statement(pdf_path):
    """Parse summary-only bank statements (like ANZ home loan statements)"""
    transactions = []
    
    try:
        import subprocess
        # Extract text from PDF
        result = subprocess.run(['pdftotext', '-layout', pdf_path, '-'], 
                                capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"pdftotext failed: {result.stderr}")
            return transactions
            
        text = result.stdout
        
        # Look for summary section
        if 'statement overview' in text.lower():
            # Extract summary items as pseudo-transactions
            
            # Pattern for summary lines like "Total payments +$102,136.02"
            summary_pattern = r'(Opening balance|Total payments|Total withdrawals|Total interests?|Total [\w/]+ charges?|Closing balance)\s*([+-]?\$?\s*[\d,]+\.?\d*)'
            
            matches = re.finditer(summary_pattern, text, re.IGNORECASE)
            
            # Try to extract statement period for date
            period_match = re.search(r'Statement Period\s+(\d+\.\d+\.\d+)-(\d+\.\d+\.\d+)', text)
            start_date = None
            end_date = None
            
            if period_match:
                try:
                    # Parse dates in DD.MM.YYYY format
                    start_date = datetime.strptime(period_match.group(1), '%d.%m.%Y')
                    end_date = datetime.strptime(period_match.group(2), '%d.%m.%Y')
                except:
                    pass
            
            # Use end date for transactions or current date
            trans_date = end_date if end_date else datetime.now()
            trans_date_str = trans_date.strftime('%d/%m/%Y') if trans_date else 'N/A'
            
            for match in matches:
                description = match.group(1).strip()
                amount_str = match.group(2).strip()
                
                # Skip opening/closing balance as they're not transactions
                if 'balance' in description.lower() and ('opening' in description.lower() or 'closing' in description.lower()):
                    continue
                
                # Clean amount string
                amount_str = amount_str.replace('$', '').replace(' ', '').replace(',', '')
                
                # Determine sign
                if amount_str.startswith('+'):
                    amount = float(amount_str[1:])
                elif amount_str.startswith('-'):
                    amount = -float(amount_str[1:])
                else:
                    # Determine by description
                    if 'payment' in description.lower():
                        amount = float(amount_str)  # Payments are positive (money in)
                    else:
                        amount = -float(amount_str)  # Everything else is negative (money out)
                
                transaction = {
                    'date': trans_date,
                    'date_string': trans_date_str,
                    'description': description,
                    'amount': amount,
                    'amount_string': amount_str
                }
                
                transactions.append(transaction)
        
        return transactions
        
    except Exception as e:
        print(f"Error parsing summary statement: {e}")
        import traceback
        traceback.print_exc()
        return transactions