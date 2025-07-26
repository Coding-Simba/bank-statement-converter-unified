#!/usr/bin/env python3
"""
Update all HTML files to include mobile navigation
"""

import os
import re
from bs4 import BeautifulSoup

def update_html_file(filepath):
    """Update a single HTML file with mobile navigation"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        soup = BeautifulSoup(content, 'html.parser')
        
        # Check if already has mobile navigation
        if soup.find('link', href=re.compile('mobile-navigation.css')):
            print(f"✓ {filepath} - Already has mobile navigation")
            return False
        
        # Find the head tag
        head = soup.find('head')
        if not head:
            print(f"✗ {filepath} - No head tag found")
            return False
        
        # Add mobile navigation CSS after main CSS
        main_css = soup.find('link', href=re.compile('main.css|style.css'))
        if main_css:
            # Create new link tag for mobile navigation CSS
            mobile_css = soup.new_tag('link', rel='stylesheet', href='css/mobile-navigation.css')
            main_css.insert_after(mobile_css)
        else:
            # Add at the end of head if no main CSS found
            mobile_css = soup.new_tag('link', rel='stylesheet', href='css/mobile-navigation.css')
            head.append(mobile_css)
        
        # Find body tag or closing body tag
        body = soup.find('body')
        if body:
            # Add mobile navigation script before closing body tag
            scripts = body.find_all('script')
            if scripts:
                last_script = scripts[-1]
                mobile_script = soup.new_tag('script', src='js/mobile-navigation.js')
                last_script.insert_after(mobile_script)
            else:
                # Add at the end of body
                mobile_script = soup.new_tag('script', src='js/mobile-navigation.js')
                body.append(mobile_script)
        
        # Adjust paths for files in subdirectories
        if '/' in filepath:
            depth = filepath.count('/') - 1
            prefix = '../' * depth
            
            # Update CSS path
            mobile_css['href'] = prefix + mobile_css['href']
            
            # Update JS path
            if 'mobile_script' in locals():
                mobile_script['src'] = prefix + mobile_script['src']
        
        # Write updated content
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(str(soup.prettify()))
        
        print(f"✓ {filepath} - Updated with mobile navigation")
        return True
        
    except Exception as e:
        print(f"✗ {filepath} - Error: {str(e)}")
        return False

def process_directory(directory):
    """Process all HTML files in directory and subdirectories"""
    updated_count = 0
    skipped_count = 0
    error_count = 0
    
    # Define directories to skip
    skip_dirs = {'backup_20250726_004344', '.git', 'node_modules', 'vendor'}
    
    for root, dirs, files in os.walk(directory):
        # Remove skip directories from dirs to prevent walking into them
        dirs[:] = [d for d in dirs if d not in skip_dirs]
        
        for file in files:
            if file.endswith('.html'):
                filepath = os.path.join(root, file)
                result = update_html_file(filepath)
                
                if result is True:
                    updated_count += 1
                elif result is False:
                    skipped_count += 1
                else:
                    error_count += 1
    
    return updated_count, skipped_count, error_count

def update_css_main():
    """Add mobile-specific styles to main.css if needed"""
    main_css_path = 'css/main.css'
    
    try:
        with open(main_css_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check if mobile-specific adjustments are already there
        if 'mobile-menu-open' in content:
            print("✓ main.css already has mobile adjustments")
            return
        
        # Add mobile-specific adjustments
        mobile_adjustments = """
/* Mobile Navigation Adjustments */
@media (max-width: 768px) {
    /* Adjust main content when mobile menu is open */
    body.mobile-menu-open {
        overflow: hidden;
        position: fixed;
        width: 100%;
    }
    
    /* Ensure navbar doesn't overlap with mobile menu button */
    .navbar,
    nav,
    header nav {
        padding-right: 60px;
    }
    
    /* Hide desktop navigation items on mobile */
    .nav-menu,
    .navbar .nav-menu,
    nav ul.nav-menu,
    header nav ul {
        display: none !important;
    }
    
    /* Adjust hero sections for mobile */
    .hero-section,
    .hero-content {
        padding-top: 80px; /* Account for fixed navbar */
    }
    
    /* Make sure content is not covered by fixed navbar */
    main {
        padding-top: 70px;
    }
}

/* Smooth transitions */
* {
    -webkit-tap-highlight-color: transparent; /* Remove tap highlight on mobile */
}

/* Prevent horizontal scroll when menu is animating */
html {
    overflow-x: hidden;
}
"""
        
        # Append to the file
        with open(main_css_path, 'a', encoding='utf-8') as f:
            f.write(mobile_adjustments)
        
        print("✓ Added mobile adjustments to main.css")
        
    except Exception as e:
        print(f"✗ Error updating main.css: {str(e)}")

def main():
    """Main function"""
    print("Starting mobile navigation update...")
    print("-" * 50)
    
    # Update CSS first
    update_css_main()
    print("-" * 50)
    
    # Process all HTML files
    updated, skipped, errors = process_directory('.')
    
    print("-" * 50)
    print(f"Summary:")
    print(f"  Updated: {updated} files")
    print(f"  Skipped: {skipped} files")
    print(f"  Errors: {errors} files")
    print("-" * 50)
    
    # Create a test page
    create_test_page()

def create_test_page():
    """Create a test page for mobile navigation"""
    test_content = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Mobile Navigation Test - BankCSVConverter</title>
    <link rel="stylesheet" href="css/main.css">
    <link rel="stylesheet" href="css/mobile-navigation.css">
    <style>
        .test-container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }
        .test-section {
            margin: 40px 0;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 8px;
        }
        .device-info {
            background: #e9ecef;
            padding: 15px;
            border-radius: 8px;
            margin: 20px 0;
            font-family: monospace;
        }
        .test-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }
        .test-card {
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
    </style>
</head>
<body>
    <!-- Standard Navigation -->
    <nav class="navbar">
        <div class="nav-container">
            <a href="/" class="nav-logo">BankCSVConverter</a>
            <ul class="nav-menu">
                <li><a href="/features.html" class="nav-link">Features</a></li>
                <li><a href="/how-it-works.html" class="nav-link">How It Works</a></li>
                <li><a href="/pricing.html" class="nav-link">Pricing</a></li>
                <li><a href="/api.html" class="nav-link">API</a></li>
                <li><a href="/blog.html" class="nav-link">Blog</a></li>
            </ul>
        </div>
    </nav>

    <main>
        <div class="test-container">
            <h1>Mobile Navigation Test</h1>
            
            <div class="device-info" id="deviceInfo"></div>
            
            <div class="test-section">
                <h2>1. Resize Your Browser</h2>
                <p>Make your browser window narrower (less than 768px wide) to see the mobile navigation.</p>
                <p>Current width: <span id="currentWidth"></span>px</p>
            </div>
            
            <div class="test-section">
                <h2>2. Mobile Menu Features</h2>
                <ul>
                    <li>✓ Hamburger menu button (top right)</li>
                    <li>✓ Slide-from-right animation</li>
                    <li>✓ Dark overlay when open</li>
                    <li>✓ Smooth animations</li>
                    <li>✓ Touch/swipe support</li>
                    <li>✓ Click outside to close</li>
                    <li>✓ Escape key to close</li>
                    <li>✓ Current page highlighting</li>
                </ul>
            </div>
            
            <div class="test-section">
                <h2>3. Test Scenarios</h2>
                <div class="test-grid">
                    <div class="test-card">
                        <h3>Open/Close</h3>
                        <p>Click hamburger menu to open, click again or overlay to close</p>
                    </div>
                    <div class="test-card">
                        <h3>Swipe Gestures</h3>
                        <p>On mobile: swipe right on menu to close, swipe from right edge to open</p>
                    </div>
                    <div class="test-card">
                        <h3>Keyboard Navigation</h3>
                        <p>Tab through menu items, press Escape to close</p>
                    </div>
                    <div class="test-card">
                        <h3>Screen Rotation</h3>
                        <p>Menu adapts to landscape/portrait orientation</p>
                    </div>
                </div>
            </div>
        </div>
    </main>

    <script>
        // Display device info
        function updateDeviceInfo() {
            const info = document.getElementById('deviceInfo');
            const width = document.getElementById('currentWidth');
            
            const deviceInfo = {
                'Screen Width': window.innerWidth + 'px',
                'Screen Height': window.innerHeight + 'px',
                'Device Pixel Ratio': window.devicePixelRatio,
                'User Agent': navigator.userAgent.substring(0, 50) + '...',
                'Touch Support': 'ontouchstart' in window ? 'Yes' : 'No'
            };
            
            info.innerHTML = Object.entries(deviceInfo)
                .map(([key, value]) => `<strong>${key}:</strong> ${value}`)
                .join('<br>');
            
            if (width) {
                width.textContent = window.innerWidth;
            }
        }
        
        updateDeviceInfo();
        window.addEventListener('resize', updateDeviceInfo);
    </script>
    
    <script src="js/mobile-navigation.js"></script>
</body>
</html>"""
    
    try:
        with open('test-mobile-nav-new.html', 'w', encoding='utf-8') as f:
            f.write(test_content)
        print("✓ Created test page: test-mobile-nav-new.html")
    except Exception as e:
        print(f"✗ Error creating test page: {str(e)}")

if __name__ == '__main__':
    main()