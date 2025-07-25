#!/usr/bin/env python3
"""
Update navigation headers across all bank pages to match index.html
"""

import os
import re

# Navigation header HTML to insert
NAV_HEADER_HTML = '''    <!-- Header Navigation -->
    <header>
        <nav>
            <a href="../" class="nav-logo">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M12 2L2 7v10c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V7l-10-5z"/>
                    <path d="M9 12l2 2 4-4"/>
                </svg>
                BankCSVConverter
            </a>
            
            <ul class="nav-menu">
                <li><a href="../all-pages.html">All Banks</a></li>
                <li><a href="../pages/bank-statement-converter-comparison.html">Why Us</a></li>
                <li><a href="../blog/financial-data-privacy-guide.html">Security</a></li>
            </ul>
            
            <button class="menu-toggle">
                <span></span>
                <span></span>
                <span></span>
            </button>
        </nav>
    </header>'''

# CSS for navigation header
NAV_CSS = '''        /* Header Navigation - matching index.html */
        header {
            background: white;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            z-index: 1000;
        }
        
        nav {
            max-width: 1200px;
            margin: 0 auto;
            padding: 0 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            height: 60px;
        }
        
        .nav-logo {
            display: flex;
            align-items: center;
            gap: 10px;
            text-decoration: none;
            color: #667eea;
            font-weight: 700;
            font-size: 1.2rem;
        }
        
        .nav-logo svg {
            width: 32px;
            height: 32px;
        }
        
        .nav-menu {
            display: flex;
            gap: 30px;
            list-style: none;
        }
        
        .nav-menu a {
            color: #666;
            text-decoration: none;
            font-weight: 500;
            font-size: 0.95rem;
            transition: color 0.3s ease;
        }
        
        .nav-menu a:hover {
            color: #667eea;
        }
        
        /* Mobile Menu Button */
        .menu-toggle {
            display: none;
            background: none;
            border: none;
            cursor: pointer;
            padding: 5px;
        }
        
        .menu-toggle span {
            display: block;
            width: 25px;
            height: 3px;
            background: #667eea;
            margin: 5px 0;
            transition: 0.3s;
        }
        
        /* Mobile Menu Styles */
        .nav-menu.active {
            display: flex;
            flex-direction: column;
            position: absolute;
            top: 60px;
            left: 0;
            right: 0;
            background: white;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            padding: 20px;
        }
        
        .menu-toggle.active span:nth-child(1) {
            transform: rotate(-45deg) translate(-5px, 6px);
        }
        
        .menu-toggle.active span:nth-child(2) {
            opacity: 0;
        }
        
        .menu-toggle.active span:nth-child(3) {
            transform: rotate(45deg) translate(-5px, -6px);
        }
        
        /* Adjust body for fixed header */
        body {
            padding-top: 60px;
        }
        
        /* Mobile Responsive */
        @media (max-width: 768px) {
            .nav-menu {
                display: none;
            }
            
            .menu-toggle {
                display: block;
            }
        }'''

# JavaScript for mobile menu
MOBILE_MENU_JS = '''    <!-- Mobile menu JavaScript -->
    <script>
        const menuToggle = document.querySelector('.menu-toggle');
        const navMenu = document.querySelector('.nav-menu');
        
        menuToggle.addEventListener('click', () => {
            navMenu.classList.toggle('active');
            menuToggle.classList.toggle('active');
        });
        
        // Close menu when clicking on a link
        document.querySelectorAll('.nav-menu a').forEach(link => {
            link.addEventListener('click', () => {
                navMenu.classList.remove('active');
                menuToggle.classList.remove('active');
            });
        });
    </script>'''

def update_bank_page(filepath):
    """Update a single bank page with new navigation"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check if page uses modern-style.css
    uses_modern_css = 'modern-style.css' in content
    
    if uses_modern_css:
        # For pages using modern-style.css, we need to add inline navigation CSS
        # First, check if navigation CSS already exists
        if 'Header Navigation - matching index.html' not in content:
            # Add navigation CSS before closing </style> tag
            style_close_pattern = r'(</style>)'
            content = re.sub(style_close_pattern, f'\n{NAV_CSS}\n\\1', content, count=1)
    
    # Replace old header with new header
    # Pattern to match existing header
    old_header_pattern = r'<header>.*?</header>'
    
    # Find if there's an existing header
    if re.search(old_header_pattern, content, re.DOTALL):
        # Replace existing header
        content = re.sub(old_header_pattern, NAV_HEADER_HTML, content, flags=re.DOTALL)
    else:
        # Add header after <body> tag
        body_pattern = r'(<body[^>]*>)'
        content = re.sub(body_pattern, f'\\1\n{NAV_HEADER_HTML}', content, count=1)
    
    # Add mobile menu JavaScript before closing </body> tag if not already present
    if 'menuToggle.addEventListener' not in content:
        body_close_pattern = r'(</body>)'
        content = re.sub(body_close_pattern, f'{MOBILE_MENU_JS}\n\\1', content, count=1)
    
    # Write updated content
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"Updated: {filepath}")

def main():
    # Update all bank pages in the pages directory
    pages_dir = '/Users/MAC/chrome/bank-statement-converter/frontend/pages'
    
    for filename in os.listdir(pages_dir):
        if filename.endswith('.html') and 'converter' in filename:
            filepath = os.path.join(pages_dir, filename)
            update_bank_page(filepath)
    
    print("Navigation update complete!")

if __name__ == '__main__':
    main()