#!/usr/bin/env python3
"""Fix relative imports in backend files."""

import os
import re

def fix_imports_in_file(filepath):
    """Fix relative imports in a single file."""
    with open(filepath, 'r') as f:
        content = f.read()
    
    # Replace relative imports with absolute imports
    replacements = [
        (r'from \.\.models\.database import', 'from models.database import'),
        (r'from \.\.utils\.auth import', 'from utils.auth import'),
        (r'from \.\.utils\.cleanup import', 'from utils.cleanup import'),
        (r'from \.\.middleware\.auth_middleware import', 'from middleware.auth_middleware import'),
        (r'from \.\.models import', 'from models import'),
        (r'from \.\.utils import', 'from utils import'),
        (r'from \.\.parsers import', 'from parsers import'),
        (r'from \.\.', 'from '),
        (r'from \.', 'from '),
    ]
    
    modified = False
    for pattern, replacement in replacements:
        new_content = re.sub(pattern, replacement, content)
        if new_content != content:
            modified = True
            content = new_content
    
    if modified:
        with open(filepath, 'w') as f:
            f.write(content)
        print(f"Fixed imports in: {filepath}")

# Fix imports in all Python files
for root, dirs, files in os.walk('/Users/MAC/chrome/bank-statement-converter-unified/backend'):
    # Skip venv directory
    if 'venv' in root:
        continue
    
    for file in files:
        if file.endswith('.py'):
            filepath = os.path.join(root, file)
            fix_imports_in_file(filepath)

print("Import fixing complete!")