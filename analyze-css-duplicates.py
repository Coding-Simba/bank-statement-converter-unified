#!/usr/bin/env python3
"""
CSS Duplicate Analyzer for Bank Statement Converter
Identifies duplicate selectors and conflicting styles across CSS files
"""

import re
import os
from collections import defaultdict

def extract_css_rules(file_path):
    """Extract CSS rules from a file"""
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Remove comments
    content = re.sub(r'/\*.*?\*/', '', content, flags=re.DOTALL)
    
    # Find CSS rules (selector { properties })
    rules = {}
    pattern = r'([^{]+)\s*{\s*([^}]+)\s*}'
    
    for match in re.finditer(pattern, content):
        selector = match.group(1).strip()
        properties = match.group(2).strip()
        
        # Skip @media, @keyframes, etc
        if selector.startswith('@'):
            continue
            
        # Clean up selector
        selector = ' '.join(selector.split())
        
        if selector not in rules:
            rules[selector] = []
        rules[selector].append({
            'file': os.path.basename(file_path),
            'properties': properties
        })
    
    return rules

def analyze_duplicates(css_dir):
    """Analyze all CSS files for duplicates"""
    all_rules = defaultdict(list)
    
    # Process non-minified CSS files
    css_files = [
        'unified-styles.css',
        'modern-style.css',
        'style.css',
        'style-seo.css'
    ]
    
    for css_file in css_files:
        file_path = os.path.join(css_dir, css_file)
        if os.path.exists(file_path):
            rules = extract_css_rules(file_path)
            for selector, definitions in rules.items():
                all_rules[selector].extend(definitions)
    
    # Find duplicates
    duplicates = {k: v for k, v in all_rules.items() if len(v) > 1}
    
    return duplicates

def generate_report(duplicates):
    """Generate a report of duplicate selectors"""
    print("# CSS Duplicate Selectors Report\n")
    print(f"Found {len(duplicates)} duplicate selectors across CSS files\n")
    
    # Sort by number of occurrences
    sorted_duplicates = sorted(duplicates.items(), key=lambda x: len(x[1]), reverse=True)
    
    for selector, definitions in sorted_duplicates[:30]:  # Top 30 duplicates
        print(f"\n## Selector: `{selector}`")
        print(f"Found in {len(definitions)} files:")
        
        for defn in definitions:
            print(f"\n### {defn['file']}")
            # Show first 200 chars of properties
            props = defn['properties'][:200]
            if len(defn['properties']) > 200:
                props += '...'
            print(f"```css\n{props}\n```")

def main():
    css_dir = '/Users/MAC/chrome/bank-statement-converter-unified/css'
    duplicates = analyze_duplicates(css_dir)
    generate_report(duplicates)

if __name__ == '__main__':
    main()