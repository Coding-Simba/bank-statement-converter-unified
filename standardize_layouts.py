#!/usr/bin/env python3
"""
Standardize layouts across all HTML pages in the Bank Statement Converter project.
This script ensures consistent layout, navigation, and styling across all pages.
"""

import os
import re
from bs4 import BeautifulSoup
from pathlib import Path
import shutil
from datetime import datetime

class LayoutStandardizer:
    def __init__(self, base_dir):
        self.base_dir = Path(base_dir)
        self.backup_dir = self.base_dir / f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.processed_files = []
        self.errors = []
        
    def create_backup(self):
        """Create backup of all HTML files before processing."""
        print(f"Creating backup in {self.backup_dir}")
        if not self.backup_dir.exists():
            self.backup_dir.mkdir(parents=True)
            
    def get_html_files(self):
        """Get all HTML files to process."""
        html_files = []
        
        # Root directory HTML files
        for file in self.base_dir.glob("*.html"):
            if file.name not in ['index.html']:  # Skip index.html for now
                html_files.append(file)
                
        # Pages directory
        pages_dir = self.base_dir / "pages"
        if pages_dir.exists():
            html_files.extend(pages_dir.glob("*.html"))
            
        # Blog directory
        blog_dir = self.base_dir / "blog"
        if blog_dir.exists():
            html_files.extend(blog_dir.glob("*.html"))
            
        return html_files
        
    def get_standard_header(self):
        """Return standardized header HTML."""
        return '''<!-- Standardized Header -->
<header>
    <nav>
        <a class="nav-logo" href="/">
            <svg fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                <rect height="18" rx="2" ry="2" width="18" x="3" y="3"></rect>
                <line x1="3" x2="21" y1="9" y2="9"></line>
                <line x1="9" x2="9" y1="21" y2="9"></line>
            </svg>
            BankCSVConverter
        </a>
        <ul class="nav-menu">
            <li><a href="/features.html">Features</a></li>
            <li><a href="/how-it-works.html">How It Works</a></li>
            <li><a href="/pricing.html">Pricing</a></li>
            <li><a href="/api.html">API</a></li>
            <li><a href="/blog.html">Blog</a></li>
        </ul>
        <button class="menu-toggle" id="menuToggle">
            <span></span>
            <span></span>
            <span></span>
        </button>
    </nav>
</header>'''
        
    def get_standard_footer(self):
        """Return standardized footer HTML."""
        return '''<!-- Standardized Footer -->
<footer>
    <div class="container">
        <div class="footer-content">
            <div class="footer-section">
                <h4>Product</h4>
                <ul>
                    <li><a href="/features.html">Features</a></li>
                    <li><a href="/how-it-works.html">How It Works</a></li>
                    <li><a href="/pricing.html">Pricing</a></li>
                    <li><a href="/api.html">API</a></li>
                </ul>
            </div>
            <div class="footer-section">
                <h4>Company</h4>
                <ul>
                    <li><a href="/about.html">About</a></li>
                    <li><a href="/blog.html">Blog</a></li>
                    <li><a href="/contact.html">Contact</a></li>
                    <li><a href="/careers.html">Careers</a></li>
                </ul>
            </div>
            <div class="footer-section">
                <h4>Support</h4>
                <ul>
                    <li><a href="/help.html">Help Center</a></li>
                    <li><a href="/faq.html">FAQ</a></li>
                    <li><a href="/security.html">Security</a></li>
                    <li><a href="/status.html">Status</a></li>
                </ul>
            </div>
            <div class="footer-section">
                <h4>Legal</h4>
                <ul>
                    <li><a href="/privacy.html">Privacy Policy</a></li>
                    <li><a href="/terms.html">Terms of Service</a></li>
                    <li><a href="/gdpr.html">GDPR</a></li>
                    <li><a href="/ccpa.html">CCPA</a></li>
                </ul>
            </div>
        </div>
        <div class="footer-bottom">
            <p>&copy; 2025 BankCSVConverter. All rights reserved.</p>
        </div>
    </div>
</footer>'''

    def get_standard_scripts(self):
        """Return standardized JavaScript."""
        return '''<!-- Standardized Scripts -->
<script>
document.addEventListener('DOMContentLoaded', function() {
    // Mobile menu functionality
    const menuToggle = document.getElementById('menuToggle');
    const navMenu = document.querySelector('.nav-menu');
    
    if (menuToggle && navMenu) {
        menuToggle.addEventListener('click', function() {
            navMenu.classList.toggle('active');
            menuToggle.classList.toggle('active');
            document.body.style.overflow = navMenu.classList.contains('active') ? 'hidden' : '';
        });
        
        // Close menu when clicking on a link
        document.querySelectorAll('.nav-menu a').forEach(link => {
            link.addEventListener('click', function() {
                navMenu.classList.remove('active');
                menuToggle.classList.remove('active');
                document.body.style.overflow = '';
            });
        });
        
        // Close menu when clicking outside
        document.addEventListener('click', function(event) {
            if (!event.target.closest('nav') && navMenu.classList.contains('active')) {
                navMenu.classList.remove('active');
                menuToggle.classList.remove('active');
                document.body.style.overflow = '';
            }
        });
    }
});
</script>'''

    def fix_relative_paths(self, html_content, file_path):
        """Fix relative paths based on file location."""
        soup = BeautifulSoup(html_content, 'html.parser')
        relative_path = os.path.relpath(self.base_dir, file_path.parent)
        
        # Fix CSS paths
        for link in soup.find_all('link', {'rel': 'stylesheet'}):
            href = link.get('href')
            if href and not href.startswith(('http', '//')):
                if 'css/' in href and not href.startswith('../'):
                    if file_path.parent != self.base_dir:
                        link['href'] = f"{relative_path}/{href}"
                        
        # Fix navigation links
        for a in soup.find_all('a'):
            href = a.get('href')
            if href and not href.startswith(('http', '#', 'mailto:', 'tel:')):
                if href.startswith('/'):
                    if file_path.parent != self.base_dir:
                        a['href'] = relative_path + href
                        
        return str(soup)

    def standardize_file(self, file_path):
        """Standardize a single HTML file."""
        print(f"Processing: {file_path}")
        
        try:
            # Create backup
            backup_path = self.backup_dir / file_path.relative_to(self.base_dir)
            backup_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(file_path, backup_path)
            
            # Read file
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            soup = BeautifulSoup(content, 'html.parser')
            
            # Skip if already standardized
            if soup.find('header') and 'Standardized Header' in str(soup.find('header')):
                print(f"  Already standardized, skipping...")
                return
                
            # Get page title and meta description
            title = soup.find('title')
            title_text = title.text if title else "BankCSVConverter"
            
            meta_desc = soup.find('meta', {'name': 'description'})
            desc_text = meta_desc.get('content', '') if meta_desc else ''
            
            # Extract main content
            main_content = ""
            
            # Try different content selectors
            main = soup.find('main')
            if main:
                main_content = str(main.decode_contents() if hasattr(main, 'decode_contents') else main)
            else:
                # Look for content after header
                header = soup.find('header')
                if header:
                    content_after_header = []
                    for sibling in header.find_next_siblings():
                        if sibling.name == 'footer':
                            break
                        content_after_header.append(str(sibling))
                    main_content = '\n'.join(content_after_header)
                else:
                    # Extract body content excluding scripts
                    body = soup.find('body')
                    if body:
                        for script in body.find_all('script'):
                            script.decompose()
                        main_content = str(body.decode_contents() if hasattr(body, 'decode_contents') else body)
                        
            # Clean up main content
            main_content = re.sub(r'<header[^>]*>.*?</header>', '', main_content, flags=re.DOTALL)
            main_content = re.sub(r'<footer[^>]*>.*?</footer>', '', main_content, flags=re.DOTALL)
            
            # Build standardized page
            standardized_html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="description" content="{desc_text}">
    <title>{title_text}</title>
    <link rel="canonical" href="https://BankCSVConverter.com{file_path.relative_to(self.base_dir).as_posix().replace('.html', '')}">
    
    <!-- Unified Design System -->
    <link rel="stylesheet" href="{'../' if file_path.parent != self.base_dir else ''}css/main.css">
    
    <!-- Skip Link for Accessibility -->
    <style>
        .skip-link {{
            position: absolute;
            left: -9999px;
        }}
        .skip-link:focus {{
            position: absolute;
            left: 6px;
            top: 7px;
            z-index: 999999;
            padding: 8px 16px;
            background: #000;
            color: white;
            text-decoration: none;
        }}
    </style>
</head>
<body>
    <a href="#main" class="skip-link">Skip to main content</a>
    
    {self.get_standard_header()}
    
    <main id="main">
        <div class="content-wrapper">
            <div class="container">
                {main_content}
            </div>
        </div>
    </main>
    
    {self.get_standard_footer()}
    {self.get_standard_scripts()}
</body>
</html>'''
            
            # Fix relative paths
            standardized_html = self.fix_relative_paths(standardized_html, file_path)
            
            # Write standardized file
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(standardized_html)
                
            self.processed_files.append(file_path)
            print(f"  ✓ Standardized successfully")
            
        except Exception as e:
            self.errors.append(f"{file_path}: {str(e)}")
            print(f"  ✗ Error: {str(e)}")
            
    def run(self):
        """Run the standardization process."""
        print("Starting layout standardization...")
        
        # Create backup
        self.create_backup()
        
        # Get files to process
        html_files = self.get_html_files()
        print(f"Found {len(html_files)} HTML files to process")
        
        # Process each file
        for file_path in html_files:
            self.standardize_file(file_path)
            
        # Report results
        print("\n" + "="*50)
        print(f"Standardization complete!")
        print(f"Files processed: {len(self.processed_files)}")
        print(f"Errors: {len(self.errors)}")
        
        if self.errors:
            print("\nErrors encountered:")
            for error in self.errors:
                print(f"  - {error}")
                
        print(f"\nBackup created at: {self.backup_dir}")
        

if __name__ == "__main__":
    standardizer = LayoutStandardizer("/Users/MAC/chrome/bank-statement-converter-unified")
    standardizer.run()