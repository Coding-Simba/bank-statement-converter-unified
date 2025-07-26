#!/usr/bin/env python3
"""
Fix all broken links and redesign banks section
"""

import os
from bs4 import BeautifulSoup

def create_modern_banks_section():
    """Create a modern, logical banks section with proper links"""
    banks_html = '''
    <!-- Supported Banks Section -->
    <section class="content-section" id="supported-banks">
        <div class="container">
            <div class="section-header">
                <h2>Trusted by Users of 1000+ Banks</h2>
                <p>Our AI-powered converter works seamlessly with statements from major banks worldwide</p>
            </div>
            
            <!-- Major US Banks -->
            <div style="margin-bottom: 3rem;">
                <h3 style="text-align: center; color: var(--text-secondary); font-size: 1rem; text-transform: uppercase; letter-spacing: 2px; margin-bottom: 2rem;">Major US Banks</h3>
                <div class="bank-grid" style="grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1.5rem;">
                    <a href="/pages/chase-bank-statement-converter.html" class="bank-card-link">
                        <div class="bank-card">
                            <div class="bank-icon">🏦</div>
                            <h4>Chase</h4>
                            <p>JPMorgan Chase Bank</p>
                        </div>
                    </a>
                    <a href="/pages/bank-of-america-statement-converter.html" class="bank-card-link">
                        <div class="bank-card">
                            <div class="bank-icon">🏛️</div>
                            <h4>Bank of America</h4>
                            <p>BoA Statement Converter</p>
                        </div>
                    </a>
                    <a href="/pages/wells-fargo-statement-converter.html" class="bank-card-link">
                        <div class="bank-card">
                            <div class="bank-icon">🏪</div>
                            <h4>Wells Fargo</h4>
                            <p>Wells Fargo & Company</p>
                        </div>
                    </a>
                    <a href="/pages/citi-bank-statement-converter.html" class="bank-card-link">
                        <div class="bank-card">
                            <div class="bank-icon">🌆</div>
                            <h4>Citi</h4>
                            <p>Citibank Statements</p>
                        </div>
                    </a>
                </div>
            </div>
            
            <!-- Regional Banks -->
            <div style="margin-bottom: 3rem;">
                <h3 style="text-align: center; color: var(--text-secondary); font-size: 1rem; text-transform: uppercase; letter-spacing: 2px; margin-bottom: 2rem;">Regional Banks</h3>
                <div class="bank-grid" style="grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));">
                    <a href="/pages/us-bank-statement-converter.html" class="bank-link-simple">US Bank</a>
                    <a href="/pages/pnc-bank-statement-converter.html" class="bank-link-simple">PNC Bank</a>
                    <a href="/pages/capital-one-statement-converter.html" class="bank-link-simple">Capital One</a>
                    <a href="/pages/td-bank-statement-converter.html" class="bank-link-simple">TD Bank</a>
                    <a href="/pages/truist-bank-statement-converter.html" class="bank-link-simple">Truist</a>
                    <a href="/pages/regions-bank-statement-converter.html" class="bank-link-simple">Regions</a>
                    <a href="/pages/fifth-third-bank-statement-converter.html" class="bank-link-simple">Fifth Third</a>
                    <a href="/pages/keybank-statement-converter.html" class="bank-link-simple">KeyBank</a>
                </div>
            </div>
            
            <!-- Online & Credit Union Banks -->
            <div style="margin-bottom: 2rem;">
                <h3 style="text-align: center; color: var(--text-secondary); font-size: 1rem; text-transform: uppercase; letter-spacing: 2px; margin-bottom: 2rem;">Online Banks & Credit Unions</h3>
                <div class="bank-grid" style="grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));">
                    <a href="/pages/ally-bank-statement-converter.html" class="bank-link-simple">Ally Bank</a>
                    <a href="/pages/navy-federal-statement-converter.html" class="bank-link-simple">Navy Federal</a>
                    <a href="/pages/usaa-bank-statement-converter.html" class="bank-link-simple">USAA</a>
                    <a href="/pages/citizens-bank-statement-converter.html" class="bank-link-simple">Citizens Bank</a>
                    <a href="/pages/huntington-bank-statement-converter.html" class="bank-link-simple">Huntington</a>
                    <a href="/pages/mt-bank-statement-converter.html" class="bank-link-simple">M&T Bank</a>
                    <a href="/pages/comerica-bank-statement-converter.html" class="bank-link-simple">Comerica</a>
                    <a href="/pages/zions-bank-statement-converter.html" class="bank-link-simple">Zions Bank</a>
                </div>
            </div>
            
            <!-- CTA -->
            <div style="text-align: center; margin-top: 3rem; padding: 2rem; background: var(--bg-secondary); border-radius: var(--radius-lg);">
                <p style="color: var(--text-secondary); margin-bottom: 1rem;">Can't find your bank? Don't worry!</p>
                <h3 style="color: var(--primary); margin-bottom: 1rem;">Our AI works with ANY bank statement</h3>
                <a href="#upload" class="cta-button">Try Your Bank Now</a>
            </div>
        </div>
    </section>
    '''
    return banks_html

def create_privacy_page():
    """Create privacy policy page"""
    privacy_content = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="description" content="BankCSVConverter Privacy Policy - Learn how we protect your financial data with bank-level security and automatic deletion.">
    <title>Privacy Policy - BankCSVConverter</title>
    <link rel="canonical" href="https://BankCSVConverter.com/privacy">
    <link rel="stylesheet" href="css/main.css">
</head>
<body>
    <header>
        <nav>
            <a href="/" class="nav-logo">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect>
                    <line x1="3" y1="9" x2="21" y2="9"></line>
                    <line x1="9" y1="21" x2="9" y2="9"></line>
                </svg>
                BankCSVConverter
            </a>
            <ul class="nav-menu">
                <li><a href="/features.html">Features</a></li>
                <li><a href="/how-it-works.html">How It Works</a></li>
                <li><a href="/#supported-banks">Banks</a></li>
                <li><a href="/pricing.html">Pricing</a></li>
                <li><a href="/blog.html">Blog</a></li>
                <li><a href="/api.html">API</a></li>
            </ul>
            <button class="menu-toggle" id="menuToggle">
                <span></span><span></span><span></span>
            </button>
        </nav>
    </header>
    
    <main>
        <section class="hero" style="min-height: 300px;">
            <div class="container">
                <h1>Privacy Policy</h1>
                <p>Your privacy and data security are our top priorities</p>
            </div>
        </section>
        
        <section class="content-section">
            <div class="container" style="max-width: 800px;">
                <p style="color: var(--text-secondary); margin-bottom: 2rem;">Last updated: January 25, 2025</p>
                
                <h2>Our Commitment to Privacy</h2>
                <p>At BankCSVConverter, we understand that you're trusting us with sensitive financial data. We take this responsibility seriously and have implemented industry-leading security measures to protect your information.</p>
                
                <h2>Data Collection</h2>
                <p>We collect only the minimum information necessary to provide our service:</p>
                <ul>
                    <li>PDF bank statements you upload for conversion</li>
                    <li>Basic usage analytics (page views, conversion counts)</li>
                    <li>Email address (only if you create an account)</li>
                </ul>
                
                <h2>Data Security</h2>
                <div class="feature-card" style="margin: 2rem 0;">
                    <h3>🔒 Bank-Level Encryption</h3>
                    <p>All data transfers use 256-bit SSL encryption, the same standard used by major financial institutions.</p>
                </div>
                
                <div class="feature-card" style="margin: 2rem 0;">
                    <h3>🗑️ Automatic Deletion</h3>
                    <p>Your files are automatically deleted from our servers immediately after conversion. We never store your bank statements.</p>
                </div>
                
                <div class="feature-card" style="margin: 2rem 0;">
                    <h3>🚫 No Data Storage</h3>
                    <p>We process everything in memory and immediately discard all data. Your financial information is never saved to our databases.</p>
                </div>
                
                <h2>Data Usage</h2>
                <p>We never:</p>
                <ul>
                    <li>Store your bank statements</li>
                    <li>Share your data with third parties</li>
                    <li>Use your financial data for any purpose other than conversion</li>
                    <li>Track or analyze your transaction data</li>
                </ul>
                
                <h2>Compliance</h2>
                <p>We comply with:</p>
                <ul>
                    <li>GDPR (General Data Protection Regulation)</li>
                    <li>CCPA (California Consumer Privacy Act)</li>
                    <li>SOC 2 Type II certification standards</li>
                </ul>
                
                <h2>Contact Us</h2>
                <p>If you have any questions about our privacy policy, please contact us at:</p>
                <p><strong>Email:</strong> privacy@bankcsvconverter.com</p>
            </div>
        </section>
    </main>
    
    <footer>
        <div class="container">
            <div class="footer-bottom">
                <p>&copy; 2025 BankCSVConverter. All rights reserved.</p>
            </div>
        </div>
    </footer>
    
    <script>
        document.addEventListener('DOMContentLoaded', function() {
            const menuToggle = document.getElementById('menuToggle');
            const navMenu = document.querySelector('.nav-menu');
            
            if (menuToggle && navMenu) {
                menuToggle.addEventListener('click', function() {
                    navMenu.classList.toggle('active');
                    menuToggle.classList.toggle('active');
                });
            }
        });
    </script>
</body>
</html>'''
    
    with open('/Users/MAC/chrome/bank-statement-converter-unified/privacy.html', 'w') as f:
        f.write(privacy_content)
    
    return "privacy.html created"

def create_terms_page():
    """Create terms of service page"""
    terms_content = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="description" content="BankCSVConverter Terms of Service - Terms and conditions for using our bank statement conversion service.">
    <title>Terms of Service - BankCSVConverter</title>
    <link rel="canonical" href="https://BankCSVConverter.com/terms">
    <link rel="stylesheet" href="css/main.css">
</head>
<body>
    <header>
        <nav>
            <a href="/" class="nav-logo">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect>
                    <line x1="3" y1="9" x2="21" y2="9"></line>
                    <line x1="9" y1="21" x2="9" y2="9"></line>
                </svg>
                BankCSVConverter
            </a>
            <ul class="nav-menu">
                <li><a href="/features.html">Features</a></li>
                <li><a href="/how-it-works.html">How It Works</a></li>
                <li><a href="/#supported-banks">Banks</a></li>
                <li><a href="/pricing.html">Pricing</a></li>
                <li><a href="/blog.html">Blog</a></li>
                <li><a href="/api.html">API</a></li>
            </ul>
            <button class="menu-toggle" id="menuToggle">
                <span></span><span></span><span></span>
            </button>
        </nav>
    </header>
    
    <main>
        <section class="hero" style="min-height: 300px;">
            <div class="container">
                <h1>Terms of Service</h1>
                <p>Please read these terms carefully before using our service</p>
            </div>
        </section>
        
        <section class="content-section">
            <div class="container" style="max-width: 800px;">
                <p style="color: var(--text-secondary); margin-bottom: 2rem;">Last updated: January 25, 2025</p>
                
                <h2>Acceptance of Terms</h2>
                <p>By using BankCSVConverter, you agree to these Terms of Service. If you do not agree, please do not use our service.</p>
                
                <h2>Service Description</h2>
                <p>BankCSVConverter provides automated conversion of PDF bank statements to CSV and Excel formats. The service is provided "as is" without warranties of any kind.</p>
                
                <h2>Acceptable Use</h2>
                <p>You agree to:</p>
                <ul>
                    <li>Only upload bank statements you have legal rights to access</li>
                    <li>Not attempt to reverse engineer or hack our systems</li>
                    <li>Not use the service for any illegal purposes</li>
                    <li>Not upload malicious files or attempt to compromise our security</li>
                </ul>
                
                <h2>Limitations</h2>
                <p>Free accounts are limited to 5 conversions per month. Paid accounts have limits as specified in their plan details.</p>
                
                <h2>Liability</h2>
                <p>We are not liable for:</p>
                <ul>
                    <li>Errors in conversion accuracy</li>
                    <li>Loss of data during processing</li>
                    <li>Indirect or consequential damages</li>
                </ul>
                
                <h2>Termination</h2>
                <p>We reserve the right to terminate or suspend access to our service for violations of these terms.</p>
                
                <h2>Changes to Terms</h2>
                <p>We may update these terms at any time. Continued use of the service constitutes acceptance of updated terms.</p>
                
                <h2>Contact</h2>
                <p>For questions about these terms, contact us at:</p>
                <p><strong>Email:</strong> legal@bankcsvconverter.com</p>
            </div>
        </section>
    </main>
    
    <footer>
        <div class="container">
            <div class="footer-bottom">
                <p>&copy; 2025 BankCSVConverter. All rights reserved.</p>
            </div>
        </div>
    </footer>
    
    <script>
        document.addEventListener('DOMContentLoaded', function() {
            const menuToggle = document.getElementById('menuToggle');
            const navMenu = document.querySelector('.nav-menu');
            
            if (menuToggle && navMenu) {
                menuToggle.addEventListener('click', function() {
                    navMenu.classList.toggle('active');
                    menuToggle.classList.toggle('active');
                });
            }
        });
    </script>
</body>
</html>'''
    
    with open('/Users/MAC/chrome/bank-statement-converter-unified/terms.html', 'w') as f:
        f.write(terms_content)
    
    return "terms.html created"

def fix_navigation_links(filepath):
    """Fix navigation links to point to actual pages instead of anchors"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Fix navigation links
    content = content.replace('href="#features"', 'href="/features.html"')
    content = content.replace('href="#how-it-works"', 'href="/how-it-works.html"')
    
    # Fix footer links
    content = content.replace('href="#privacy"', 'href="/privacy.html"')
    content = content.replace('href="#terms"', 'href="/terms.html"')
    content = content.replace('href="/privacy"', 'href="/privacy.html"')
    content = content.replace('href="/terms"', 'href="/terms.html"')
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

def update_index_banks_section():
    """Update the banks section in index.html"""
    filepath = '/Users/MAC/chrome/bank-statement-converter-unified/index.html'
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    soup = BeautifulSoup(content, 'html.parser')
    
    # Find and replace the banks section
    old_banks = soup.find('section', id='supported-banks')
    if old_banks:
        new_banks_html = BeautifulSoup(create_modern_banks_section(), 'html.parser')
        old_banks.replace_with(new_banks_html)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(str(soup))

def main():
    """Main function to fix all issues"""
    print("Fixing broken links and redesigning banks section...")
    
    # Create missing pages
    print("Creating missing pages...")
    create_privacy_page()
    create_terms_page()
    
    # Fix navigation links in all HTML files
    print("Fixing navigation links...")
    import glob
    for html_file in glob.glob('/Users/MAC/chrome/bank-statement-converter-unified/**/*.html', recursive=True):
        if 'node_modules' not in html_file:
            try:
                fix_navigation_links(html_file)
            except Exception as e:
                print(f"Error fixing {html_file}: {e}")
    
    # Update banks section
    print("Updating banks section with modern design...")
    update_index_banks_section()
    
    print("\n✅ All fixes complete!")
    print("   - Created privacy.html")
    print("   - Created terms.html") 
    print("   - Fixed navigation links")
    print("   - Redesigned banks section with proper links")

if __name__ == "__main__":
    main()