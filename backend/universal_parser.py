"""
Universal PDF Parser - V2 with Robust Architecture
=================================================

This is a wrapper that uses the new robust parser architecture
while maintaining backward compatibility with existing code.
"""

# Import the new parser
from parsers.integration_layer import (
    parse_universal_pdf,
    parse_bank_of_america,
    parse_wells_fargo,
    parse_chase,
    parse_citizens,
    parse_commonwealth_bank,
    parse_westpac,
    parse_rbc,
    process_multiple_pdfs
)

# Re-export all functions for backward compatibility
__all__ = [
    'parse_universal_pdf',
    'parse_bank_of_america', 
    'parse_wells_fargo',
    'parse_chase',
    'parse_citizens',
    'parse_commonwealth_bank',
    'parse_westpac',
    'parse_rbc',
    'process_multiple_pdfs'
]

# Add any legacy functions that might be used
def parse_rabobank_pdf(pdf_path):
    return parse_universal_pdf(pdf_path)

def parse_monzo(pdf_path):
    return parse_universal_pdf(pdf_path)

def parse_santander(pdf_path):
    return parse_universal_pdf(pdf_path)

def parse_boa(pdf_path):
    return parse_bank_of_america(pdf_path)

def parse_becu(pdf_path):
    return parse_universal_pdf(pdf_path)

def parse_discover(pdf_path):
    return parse_universal_pdf(pdf_path)

def parse_greendot(pdf_path):
    return parse_universal_pdf(pdf_path)

def parse_netspend(pdf_path):
    return parse_universal_pdf(pdf_path)

def parse_paypal(pdf_path):
    return parse_universal_pdf(pdf_path)

def parse_suntrust(pdf_path):
    return parse_universal_pdf(pdf_path)

def parse_woodforest(pdf_path):
    return parse_universal_pdf(pdf_path)

def parse_walmart(pdf_path):
    return parse_universal_pdf(pdf_path)

def parse_huntington(pdf_path):
    return parse_universal_pdf(pdf_path)

def parse_bendigo(pdf_path):
    return parse_universal_pdf(pdf_path)

def parse_monese(pdf_path):
    return parse_universal_pdf(pdf_path)

# For testing
if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        pdf_path = sys.argv[1]
        transactions = parse_universal_pdf(pdf_path)
        print(f"Extracted {len(transactions)} transactions using robust parser")
    else:
        print("Usage: python universal_parser.py <pdf_path>")
