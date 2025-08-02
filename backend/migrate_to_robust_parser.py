#!/usr/bin/env python3
"""
Migration Script to Robust Parser
=================================

Safely migrates the existing parser to the new robust architecture.
"""

import os
import shutil
import sys
from datetime import datetime

def backup_existing_parser():
    """Backup the existing universal_parser.py"""
    source = 'universal_parser.py'
    if os.path.exists(source):
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup = f'universal_parser_backup_{timestamp}.py'
        shutil.copy2(source, backup)
        print(f"✅ Backed up existing parser to: {backup}")
        return True
    return False

def update_universal_parser():
    """Update universal_parser.py to use the new robust parser"""
    
    new_parser_content = '''"""
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
'''
    
    with open('universal_parser.py', 'w') as f:
        f.write(new_parser_content)
    
    print("✅ Updated universal_parser.py to use robust parser")

def install_dependencies():
    """Install required dependencies"""
    print("\n📦 Installing required dependencies...")
    
    requirements = [
        'pdfplumber>=0.9.0',
        'camelot-py[cv]>=0.11.0',
        'tabula-py>=2.8.0',
        'PyMuPDF>=1.23.0',
        'pdf2image>=1.16.0',
        'pytesseract>=0.3.10',
        'pandas>=2.0.0',
        'numpy>=1.24.0',
        'scikit-learn>=1.3.0',
        'joblib>=1.3.0',
        'python-dateutil>=2.8.0',
        'prometheus-client>=0.19.0'
    ]
    
    import subprocess
    
    for req in requirements:
        try:
            subprocess.run([sys.executable, '-m', 'pip', 'install', req], 
                         check=True, capture_output=True)
            print(f"  ✅ {req}")
        except subprocess.CalledProcessError:
            print(f"  ❌ Failed to install {req}")

def create_directories():
    """Create required directories"""
    dirs = ['models', 'training_data', 'logs']
    
    for dir_name in dirs:
        os.makedirs(dir_name, exist_ok=True)
        print(f"✅ Created directory: {dir_name}")

def test_new_parser():
    """Test the new parser with a sample PDF"""
    print("\n🧪 Testing new parser...")
    
    test_pdfs = [
        '/Users/MAC/chrome/bank-statement-converter-unified/test_files/standard.pdf',
        '/Users/MAC/Desktop/pdfs/1/USA Bank of America.pdf'
    ]
    
    for pdf_path in test_pdfs:
        if os.path.exists(pdf_path):
            print(f"\nTesting with: {pdf_path}")
            try:
                from parsers.integration_layer import parse_universal_pdf
                transactions = parse_universal_pdf(pdf_path)
                print(f"  ✅ Successfully extracted {len(transactions)} transactions")
                if transactions:
                    tx = transactions[0]
                    print(f"  Sample: {tx['date_string']} - {tx['description'][:30]}... - ${tx['amount']}")
            except Exception as e:
                print(f"  ❌ Test failed: {e}")
            break

def main():
    """Run the migration"""
    print("🚀 Migrating to Robust PDF Parser Architecture")
    print("=" * 50)
    
    # Check current directory
    if not os.path.exists('universal_parser.py'):
        print("❌ Error: universal_parser.py not found in current directory")
        print("   Please run this script from the backend directory")
        return 1
    
    # Step 1: Backup existing parser
    if not backup_existing_parser():
        print("⚠️  No existing parser to backup")
    
    # Step 2: Create required directories
    create_directories()
    
    # Step 3: Install dependencies
    print("\n📦 Skipping dependency installation (run manually if needed)")
    
    # Step 4: Update the parser
    update_universal_parser()
    
    # Step 5: Test the new parser
    test_new_parser()
    
    print("\n✅ Migration complete!")
    print("\nNext steps:")
    print("1. Test with your training PDFs")
    print("2. Monitor logs for any issues")
    print("3. The old parser is backed up if you need to rollback")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())