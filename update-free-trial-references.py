#!/usr/bin/env python3
"""
Update all references from 'free trial' to 'create free account' across the website
"""

import os
import re

# Dictionary of replacements
replacements = {
    # Button text variations
    r'Start Free Trial': 'Create Free Account',
    r'start free trial': 'create free account',
    r'Start free trial': 'Create free account',
    r'FREE TRIAL': 'SIGN UP FREE',
    r'Free Trial': 'Sign Up Free',
    r'free trial': 'free account',
    
    # Sentence variations
    r'Sign up for a free trial': 'Create a free account',
    r'sign up for a free trial': 'create a free account',
    r'Try it free': 'Sign up free',
    r'try it free': 'sign up free',
    r'14-day free trial': 'free account with 5 daily conversions',
    r'7-day free trial': 'free account with 5 daily conversions',
    r'30-day free trial': 'free account with 5 daily conversions',
    
    # Trial period references
    r'trial period': 'free account',
    r'Trial period': 'Free account',
    r'trial expires': 'daily limit reached',
    r'Trial expires': 'Daily limit reached',
}

# Files and directories to exclude
exclude_dirs = {'.git', 'node_modules', 'backup_20250726_004344', '__pycache__', '.next'}
exclude_files = {'update-free-trial-references.py', 'pricing.html', 'conversion-limit-modal.js'}

def update_file(filepath):
    """Update a single file with all replacements"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        changes_made = []
        
        # Apply all replacements
        for pattern, replacement in replacements.items():
            if re.search(pattern, content):
                content = re.sub(pattern, replacement, content)
                changes_made.append(f"{pattern} -> {replacement}")
        
        # Only write if changes were made
        if content != original_content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"Updated: {filepath}")
            for change in changes_made:
                print(f"  - {change}")
            return True
    except Exception as e:
        print(f"Error processing {filepath}: {e}")
    return False

def process_directory(directory):
    """Process all HTML, JS, and CSS files in directory"""
    updated_files = 0
    
    for root, dirs, files in os.walk(directory):
        # Remove excluded directories from dirs to prevent walking into them
        dirs[:] = [d for d in dirs if d not in exclude_dirs]
        
        for file in files:
            # Check if file should be processed
            if file in exclude_files:
                continue
                
            if file.endswith(('.html', '.js', '.css', '.jsx', '.tsx')):
                filepath = os.path.join(root, file)
                if update_file(filepath):
                    updated_files += 1
    
    return updated_files

# Run the script
if __name__ == "__main__":
    print("Updating free trial references to free account...")
    print("-" * 50)
    
    # Process the current directory
    updated_count = process_directory('.')
    
    print("-" * 50)
    print(f"Total files updated: {updated_count}")
    print("\nDone! All 'free trial' references have been updated to 'free account'.")
    print("\nNote: The pricing.html and conversion-limit-modal.js files were excluded as they were already updated.")