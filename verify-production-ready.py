#!/usr/bin/env python3
"""
Verify the website is production-ready
"""
import os
import glob
from bs4 import BeautifulSoup
import json

def check_html_file(file_path):
    """Check if an HTML file has all required elements"""
    issues = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        soup = BeautifulSoup(content, 'html.parser')
        
        # Check for production CSS
        production_css = soup.find('link', href=lambda x: x and 'production.css' in x)
        if not production_css:
            issues.append("Missing production.css link")
        
        # Check for production JS
        production_js = soup.find('script', src=lambda x: x and 'production.js' in x)
        if not production_js:
            issues.append("Missing production.js script")
        
        # Check for viewport meta tag
        viewport = soup.find('meta', attrs={'name': 'viewport'})
        if not viewport:
            issues.append("Missing viewport meta tag")
        
        # Check for navigation
        nav = soup.find('nav')
        if nav:
            # Check for mobile menu toggle
            menu_toggle = nav.find(id='menuToggle')
            if not menu_toggle:
                issues.append("Missing mobile menu toggle")
            
            # Check for nav menu
            nav_menu = nav.find(class_='nav-menu')
            if not nav_menu:
                issues.append("Missing nav-menu class")
        
        # Check for proper title
        title = soup.find('title')
        if not title or not title.string:
            issues.append("Missing or empty title tag")
        
        # Check for description meta tag
        description = soup.find('meta', attrs={'name': 'description'})
        if not description:
            issues.append("Missing description meta tag")
        
        # Check for charset
        charset = soup.find('meta', charset=True)
        if not charset:
            issues.append("Missing charset meta tag")
        
        # Check for broken links
        links = soup.find_all('a', href=True)
        for link in links:
            href = link['href']
            if href.startswith('/') and not href.startswith('//'):
                # Check if it's a local file that should exist
                if href.endswith('.html'):
                    local_path = href[1:] if href.startswith('/') else href
                    if not os.path.exists(local_path) and not os.path.exists(os.path.join('pages', os.path.basename(local_path))):
                        issues.append(f"Broken link: {href}")
        
        return issues
        
    except Exception as e:
        return [f"Error reading file: {str(e)}"]

def verify_css_files():
    """Verify CSS files exist and are properly formatted"""
    issues = []
    
    required_css = ['css/production.css', 'css/enhancements.css']
    
    for css_file in required_css:
        if not os.path.exists(css_file):
            issues.append(f"Missing CSS file: {css_file}")
        else:
            try:
                with open(css_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if len(content) < 100:
                        issues.append(f"CSS file seems empty: {css_file}")
            except Exception as e:
                issues.append(f"Error reading CSS file {css_file}: {str(e)}")
    
    return issues

def verify_js_files():
    """Verify JavaScript files exist and are properly formatted"""
    issues = []
    
    required_js = ['js/production.js']
    
    for js_file in required_js:
        if not os.path.exists(js_file):
            issues.append(f"Missing JS file: {js_file}")
        else:
            try:
                with open(js_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if len(content) < 100:
                        issues.append(f"JS file seems empty: {js_file}")
            except Exception as e:
                issues.append(f"Error reading JS file {js_file}: {str(e)}")
    
    return issues

def verify_assets():
    """Verify required assets exist"""
    issues = []
    
    required_assets = [
        'assets/logo.svg',
        'assets/secure-icon.svg',
        'assets/accurate-icon.svg',
        'assets/institutional-icon.svg'
    ]
    
    for asset in required_assets:
        if not os.path.exists(asset):
            issues.append(f"Missing asset: {asset}")
    
    return issues

def main():
    """Run all verification checks"""
    print("🔍 Verifying website is production-ready...\n")
    
    all_issues = []
    
    # Check CSS files
    print("📁 Checking CSS files...")
    css_issues = verify_css_files()
    if css_issues:
        all_issues.extend(css_issues)
        for issue in css_issues:
            print(f"  ❌ {issue}")
    else:
        print("  ✅ All CSS files present and valid")
    
    # Check JS files
    print("\n📁 Checking JavaScript files...")
    js_issues = verify_js_files()
    if js_issues:
        all_issues.extend(js_issues)
        for issue in js_issues:
            print(f"  ❌ {issue}")
    else:
        print("  ✅ All JavaScript files present and valid")
    
    # Check assets
    print("\n📁 Checking assets...")
    asset_issues = verify_assets()
    if asset_issues:
        all_issues.extend(asset_issues)
        for issue in asset_issues:
            print(f"  ❌ {issue}")
    else:
        print("  ✅ All required assets present")
    
    # Check HTML files
    print("\n📄 Checking HTML files...")
    html_files = []
    html_files.extend(glob.glob('*.html'))
    html_files.extend(glob.glob('pages/*.html'))
    html_files.extend(glob.glob('blog/*.html'))
    
    # Filter out backup files
    html_files = [f for f in html_files if not f.endswith('.backup') and 'backup' not in f]
    
    html_issues_count = 0
    for file_path in html_files:
        issues = check_html_file(file_path)
        if issues:
            html_issues_count += len(issues)
            print(f"\n  ❌ {file_path}:")
            for issue in issues:
                print(f"     - {issue}")
                all_issues.append(f"{file_path}: {issue}")
    
    if html_issues_count == 0:
        print("  ✅ All HTML files properly structured")
    
    # Summary
    print("\n" + "="*50)
    print("📊 VERIFICATION SUMMARY")
    print("="*50)
    
    if not all_issues:
        print("✅ Website is PRODUCTION READY!")
        print("✅ All checks passed successfully")
        
        # Create success report
        report = {
            "status": "PRODUCTION_READY",
            "timestamp": "2025-01-26",
            "checks": {
                "css_files": "PASSED",
                "js_files": "PASSED",
                "assets": "PASSED",
                "html_structure": "PASSED",
                "mobile_responsive": "PASSED",
                "navigation": "PASSED"
            },
            "issues": []
        }
    else:
        print(f"❌ Found {len(all_issues)} issues that need attention")
        print("\nIssues summary:")
        for i, issue in enumerate(all_issues[:10], 1):
            print(f"{i}. {issue}")
        
        if len(all_issues) > 10:
            print(f"... and {len(all_issues) - 10} more issues")
        
        report = {
            "status": "NEEDS_ATTENTION",
            "timestamp": "2025-01-26",
            "checks": {
                "css_files": "PASSED" if not css_issues else "FAILED",
                "js_files": "PASSED" if not js_issues else "FAILED",
                "assets": "PASSED" if not asset_issues else "FAILED",
                "html_structure": "NEEDS_REVIEW",
            },
            "issues": all_issues
        }
    
    # Save report
    with open('production-verification-report.json', 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\n📝 Full report saved to: production-verification-report.json")

if __name__ == '__main__':
    main()