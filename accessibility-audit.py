#!/usr/bin/env python3
"""
Comprehensive Accessibility Audit for HTML Files
Checks for:
1. Proper heading hierarchy (H1->H2->H3)
2. Alt text on images
3. ARIA labels on interactive elements
4. Color contrast issues
5. Proper form labels
6. Descriptive link text
7. Skip navigation links
8. Language attributes
"""

import os
import re
from bs4 import BeautifulSoup
from collections import defaultdict
import sys

class AccessibilityAuditor:
    def __init__(self):
        self.violations = defaultdict(list)
        
    def audit_file(self, filepath):
        """Audit a single HTML file for accessibility issues"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            soup = BeautifulSoup(content, 'html.parser')
            
            # Check language attribute
            self.check_language_attribute(soup, filepath)
            
            # Check heading hierarchy
            self.check_heading_hierarchy(soup, filepath)
            
            # Check images for alt text
            self.check_image_alt_text(soup, filepath)
            
            # Check ARIA labels on interactive elements
            self.check_aria_labels(soup, filepath)
            
            # Check form labels
            self.check_form_labels(soup, filepath)
            
            # Check link text
            self.check_link_text(soup, filepath)
            
            # Check skip navigation
            self.check_skip_navigation(soup, filepath)
            
            # Check color contrast (basic check)
            self.check_color_contrast(soup, filepath)
            
        except Exception as e:
            self.violations[filepath].append(f"ERROR: Could not parse file - {str(e)}")
    
    def check_language_attribute(self, soup, filepath):
        """Check if html tag has lang attribute"""
        html_tag = soup.find('html')
        if not html_tag or not html_tag.get('lang'):
            self.violations[filepath].append("Missing lang attribute on <html> tag")
    
    def check_heading_hierarchy(self, soup, filepath):
        """Check for proper heading hierarchy"""
        headings = []
        for i in range(1, 7):
            h_tags = soup.find_all(f'h{i}')
            for tag in h_tags:
                headings.append((i, tag.get_text(strip=True), tag.sourceline))
        
        # Sort by line number
        headings.sort(key=lambda x: x[2] if x[2] else 0)
        
        # Check for missing H1
        h1_tags = [h for h in headings if h[0] == 1]
        if not h1_tags:
            self.violations[filepath].append("Missing H1 tag")
        elif len(h1_tags) > 1:
            self.violations[filepath].append(f"Multiple H1 tags found ({len(h1_tags)})")
        
        # Check hierarchy
        prev_level = 0
        for level, text, line in headings:
            if level > prev_level + 1 and prev_level != 0:
                self.violations[filepath].append(
                    f"Heading hierarchy skip: H{prev_level} to H{level} at line {line} ('{text[:50]}...')"
                )
            prev_level = level
    
    def check_image_alt_text(self, soup, filepath):
        """Check all images have alt text"""
        images = soup.find_all('img')
        for img in images:
            if not img.get('alt'):
                src = img.get('src', 'unknown')
                line = img.sourceline
                self.violations[filepath].append(
                    f"Image missing alt text: src='{src}' at line {line}"
                )
    
    def check_aria_labels(self, soup, filepath):
        """Check interactive elements for ARIA labels"""
        # Interactive elements that should have labels
        interactive_elements = ['button', 'a', 'input', 'select', 'textarea']
        
        for elem_type in interactive_elements:
            elements = soup.find_all(elem_type)
            for elem in elements:
                # Skip if element has text content
                if elem.get_text(strip=True):
                    continue
                
                # Check for aria-label or aria-labelledby
                if not elem.get('aria-label') and not elem.get('aria-labelledby'):
                    # For inputs, also check for associated label
                    if elem_type == 'input':
                        input_id = elem.get('id')
                        if input_id:
                            label = soup.find('label', {'for': input_id})
                            if label:
                                continue
                    
                    # Special case for buttons with only icons
                    if elem_type == 'button' and (elem.find('i') or elem.find('svg')):
                        line = elem.sourceline
                        self.violations[filepath].append(
                            f"Button with icon missing aria-label at line {line}"
                        )
                    elif elem_type == 'a' and not elem.get_text(strip=True):
                        line = elem.sourceline
                        href = elem.get('href', 'unknown')
                        self.violations[filepath].append(
                            f"Link without text missing aria-label: href='{href}' at line {line}"
                        )
    
    def check_form_labels(self, soup, filepath):
        """Check that form inputs have proper labels"""
        inputs = soup.find_all(['input', 'select', 'textarea'])
        
        for input_elem in inputs:
            input_type = input_elem.get('type', 'text')
            # Skip hidden and submit/button inputs
            if input_type in ['hidden', 'submit', 'button']:
                continue
            
            input_id = input_elem.get('id')
            has_label = False
            
            # Check for associated label
            if input_id:
                label = soup.find('label', {'for': input_id})
                if label:
                    has_label = True
            
            # Check for aria-label
            if input_elem.get('aria-label') or input_elem.get('aria-labelledby'):
                has_label = True
            
            # Check if input is wrapped in label
            parent = input_elem.parent
            if parent and parent.name == 'label':
                has_label = True
            
            if not has_label:
                line = input_elem.sourceline
                name = input_elem.get('name', 'unnamed')
                self.violations[filepath].append(
                    f"Form input without label: name='{name}' type='{input_type}' at line {line}"
                )
    
    def check_link_text(self, soup, filepath):
        """Check for non-descriptive link text"""
        non_descriptive_phrases = [
            'click here', 'here', 'read more', 'more', 'link', 
            'click', 'go', 'visit', 'this', 'page'
        ]
        
        links = soup.find_all('a')
        for link in links:
            link_text = link.get_text(strip=True).lower()
            if link_text in non_descriptive_phrases:
                href = link.get('href', 'unknown')
                line = link.sourceline
                self.violations[filepath].append(
                    f"Non-descriptive link text '{link_text}': href='{href}' at line {line}"
                )
    
    def check_skip_navigation(self, soup, filepath):
        """Check for skip navigation links"""
        # Look for common skip navigation patterns
        skip_found = False
        
        # Check first few links
        first_links = soup.find_all('a', limit=5)
        for link in first_links:
            href = link.get('href', '')
            text = link.get_text(strip=True).lower()
            if href.startswith('#') and any(word in text for word in ['skip', 'main', 'content']):
                skip_found = True
                break
        
        # Also check for hidden skip links
        if not skip_found:
            skip_links = soup.find_all('a', class_=re.compile(r'skip|sr-only|visually-hidden'))
            if skip_links:
                skip_found = True
        
        if not skip_found:
            self.violations[filepath].append("No skip navigation link found")
    
    def check_color_contrast(self, soup, filepath):
        """Basic check for potential color contrast issues"""
        # This is a simplified check - real contrast checking requires color values
        
        # Check for low contrast color combinations in inline styles
        elements_with_style = soup.find_all(style=True)
        
        low_contrast_patterns = [
            (r'color:\s*#[cdefCDEF]{3,6}', r'background-color:\s*#[cdefCDEF]{3,6}'),  # Light on light
            (r'color:\s*#[0-3]{3,6}', r'background-color:\s*#[0-3]{3,6}'),  # Dark on dark
            (r'color:\s*gray', r'background-color:\s*white'),  # Gray on white
            (r'color:\s*#999', r'background-color:\s*#fff'),  # Light gray on white
        ]
        
        for elem in elements_with_style:
            style = elem.get('style', '')
            for color_pattern, bg_pattern in low_contrast_patterns:
                if re.search(color_pattern, style) and re.search(bg_pattern, style):
                    line = elem.sourceline
                    self.violations[filepath].append(
                        f"Potential low color contrast in inline style at line {line}"
                    )
                    break
    
    def generate_report(self):
        """Generate accessibility audit report"""
        print("=" * 80)
        print("ACCESSIBILITY AUDIT REPORT")
        print("=" * 80)
        print()
        
        if not self.violations:
            print("No accessibility violations found!")
            return
        
        total_violations = sum(len(v) for v in self.violations.values())
        print(f"Total violations found: {total_violations}")
        print(f"Files with violations: {len(self.violations)}")
        print()
        
        # Group violations by type
        violation_types = defaultdict(list)
        for filepath, violations in self.violations.items():
            for violation in violations:
                # Extract violation type
                if "Missing lang attribute" in violation:
                    violation_types["Language Attributes"].append((filepath, violation))
                elif "heading" in violation.lower() or "h1" in violation.lower():
                    violation_types["Heading Hierarchy"].append((filepath, violation))
                elif "alt text" in violation:
                    violation_types["Missing Alt Text"].append((filepath, violation))
                elif "aria-label" in violation.lower():
                    violation_types["Missing ARIA Labels"].append((filepath, violation))
                elif "form input without label" in violation.lower():
                    violation_types["Form Label Issues"].append((filepath, violation))
                elif "link text" in violation:
                    violation_types["Non-descriptive Links"].append((filepath, violation))
                elif "skip navigation" in violation:
                    violation_types["Skip Navigation"].append((filepath, violation))
                elif "color contrast" in violation:
                    violation_types["Color Contrast"].append((filepath, violation))
                else:
                    violation_types["Other"].append((filepath, violation))
        
        # Print violations by type
        for vtype, items in sorted(violation_types.items()):
            print(f"\n{vtype} ({len(items)} issues)")
            print("-" * len(vtype))
            for filepath, violation in items[:10]:  # Show first 10 of each type
                short_path = filepath.replace('/Users/MAC/chrome/bank-statement-converter-unified/', '')
                print(f"  {short_path}: {violation}")
            if len(items) > 10:
                print(f"  ... and {len(items) - 10} more")
        
        print("\n" + "=" * 80)
        print("DETAILED VIOLATIONS BY FILE")
        print("=" * 80)
        
        # Print detailed violations for each file
        for filepath in sorted(self.violations.keys()):
            short_path = filepath.replace('/Users/MAC/chrome/bank-statement-converter-unified/', '')
            print(f"\n{short_path} ({len(self.violations[filepath])} issues):")
            for violation in self.violations[filepath]:
                print(f"  - {violation}")


def main():
    # Get all HTML files
    html_files = []
    base_dir = '/Users/MAC/chrome/bank-statement-converter-unified'
    
    for root, dirs, files in os.walk(base_dir):
        # Skip node_modules
        if 'node_modules' in root:
            continue
        
        for file in files:
            if file.endswith(('.html', '.htm')):
                html_files.append(os.path.join(root, file))
    
    print(f"Found {len(html_files)} HTML files to audit\n")
    
    # Run audit
    auditor = AccessibilityAuditor()
    
    for filepath in sorted(html_files):
        print(f"Auditing: {filepath.replace(base_dir + '/', '')}...")
        auditor.audit_file(filepath)
    
    print("\n")
    
    # Generate report
    auditor.generate_report()


if __name__ == "__main__":
    main()