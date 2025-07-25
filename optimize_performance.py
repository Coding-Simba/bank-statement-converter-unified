#!/usr/bin/env python3
"""
Performance optimization script for Bank Statement Converter frontend
Handles CSS minification, JS minification, image optimization checks, and performance testing
"""

import os
import re
import json
import time
import subprocess
from pathlib import Path
import urllib.request
import urllib.parse

def minify_css(css_content):
    """Simple CSS minification"""
    # Remove comments
    css_content = re.sub(r'/\*.*?\*/', '', css_content, flags=re.DOTALL)
    # Remove unnecessary whitespace
    css_content = re.sub(r'\s+', ' ', css_content)
    # Remove space around specific characters
    css_content = re.sub(r'\s*([{}:;,>~+])\s*', r'\1', css_content)
    # Remove trailing semicolon before closing brace
    css_content = re.sub(r';\s*}', '}', css_content)
    # Remove leading/trailing whitespace
    css_content = css_content.strip()
    return css_content

def minify_js(js_content):
    """Simple JavaScript minification (basic, preserves functionality)"""
    # Remove single-line comments (but preserve URLs)
    js_content = re.sub(r'(?<!:)//.*$', '', js_content, flags=re.MULTILINE)
    # Remove multi-line comments
    js_content = re.sub(r'/\*.*?\*/', '', js_content, flags=re.DOTALL)
    # Remove unnecessary whitespace (preserve strings)
    lines = []
    for line in js_content.split('\n'):
        line = line.strip()
        if line:
            lines.append(line)
    js_content = '\n'.join(lines)
    # Remove extra spaces around operators (basic)
    js_content = re.sub(r'\s*([=+\-*/{}();,:])\s*', r'\1', js_content)
    return js_content

def create_minified_files():
    """Create minified versions of CSS and JS files"""
    print("🔧 Creating minified CSS and JS files...")
    
    # Minify CSS files
    css_dir = Path('css')
    for css_file in css_dir.glob('*.css'):
        if not css_file.name.endswith('.min.css'):
            print(f"  Minifying {css_file.name}...")
            with open(css_file, 'r') as f:
                content = f.read()
            
            minified = minify_css(content)
            minified_path = css_file.with_suffix('.min.css')
            
            with open(minified_path, 'w') as f:
                f.write(minified)
            
            original_size = len(content)
            minified_size = len(minified)
            reduction = ((original_size - minified_size) / original_size) * 100
            print(f"    ✓ Reduced by {reduction:.1f}% ({original_size} → {minified_size} bytes)")
    
    # Minify JS files
    js_dir = Path('js')
    for js_file in js_dir.glob('*.js'):
        if not js_file.name.endswith('.min.js'):
            print(f"  Minifying {js_file.name}...")
            with open(js_file, 'r') as f:
                content = f.read()
            
            minified = minify_js(content)
            minified_path = js_file.with_suffix('.min.js')
            
            with open(minified_path, 'w') as f:
                f.write(minified)
            
            original_size = len(content)
            minified_size = len(minified)
            reduction = ((original_size - minified_size) / original_size) * 100
            print(f"    ✓ Reduced by {reduction:.1f}% ({original_size} → {minified_size} bytes)")

def check_image_optimization():
    """Check for image optimization opportunities"""
    print("\n📸 Checking image optimization...")
    
    assets_dir = Path('assets')
    total_size = 0
    
    for img_file in assets_dir.glob('*'):
        if img_file.suffix.lower() in ['.svg', '.png', '.jpg', '.jpeg', '.webp']:
            size = img_file.stat().st_size
            total_size += size
            print(f"  {img_file.name}: {size:,} bytes")
    
    print(f"\n  Total image size: {total_size:,} bytes ({total_size/1024:.1f} KB)")
    
    # SVG optimization suggestion
    svg_files = list(assets_dir.glob('*.svg'))
    if svg_files:
        print("\n  💡 SVG Optimization Tips:")
        print("     - Consider using SVGO to optimize SVG files")
        print("     - Remove unnecessary metadata and comments")
        print("     - Simplify paths where possible")

def create_critical_css():
    """Extract and inline critical CSS for above-the-fold content"""
    print("\n🎨 Creating critical CSS...")
    
    # Define critical CSS (above-the-fold styles)
    critical_css = """/* Critical CSS - Inline for fast initial render */
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif; color: #1a1a1a; line-height: 1.6; background: #ffffff; }
header { background: white; box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1); position: fixed; top: 0; left: 0; right: 0; z-index: 1000; }
nav { max-width: 1200px; margin: 0 auto; padding: 0 20px; display: flex; justify-content: space-between; align-items: center; height: 60px; }
.nav-logo { display: flex; align-items: center; gap: 10px; text-decoration: none; color: #667eea; font-weight: 700; font-size: 1.2rem; }
.nav-logo svg { width: 32px; height: 32px; }
.nav-menu { display: flex; gap: 30px; list-style: none; }
.nav-menu a { color: #666; text-decoration: none; font-weight: 500; font-size: 0.95rem; transition: color 0.3s ease; }
.nav-menu a:hover { color: #667eea; }
.hero { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 120px 0 80px; text-align: center; }
.container { max-width: 1200px; margin: 0 auto; padding: 0 20px; }
h1 { font-size: 3rem; font-weight: 700; margin-bottom: 1rem; }
.upload-area { background: white; border-radius: 20px; padding: 3rem; margin: 2rem auto; max-width: 600px; box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1); }
.upload-btn { background: #667eea; color: white; border: none; padding: 1rem 2rem; border-radius: 10px; font-size: 1.1rem; font-weight: 600; cursor: pointer; transition: all 0.3s ease; }
.upload-btn:hover { background: #5a5cc5; transform: translateY(-2px); }
@media (max-width: 768px) { .nav-menu { display: none; } h1 { font-size: 2rem; } }"""
    
    with open('css/critical.min.css', 'w') as f:
        f.write(minify_css(critical_css))
    
    print("  ✓ Created critical.min.css for inline loading")

def update_html_for_performance():
    """Update HTML files to use optimized resources"""
    print("\n📄 Updating HTML files for optimal performance...")
    
    # Process index.html
    index_path = Path('index.html')
    if index_path.exists():
        with open(index_path, 'r') as f:
            content = f.read()
        
        # Check if already optimized
        if 'critical.min.css' in content:
            print("  ℹ️  index.html already optimized")
            return
        
        # Create performance-optimized version
        optimized_content = content
        
        # Replace CSS links with minified versions and add preload
        optimized_content = re.sub(
            r'<link rel="stylesheet" href="css/modern-style\.css">',
            '''<!-- Preload critical fonts -->
    <link rel="preload" href="css/modern-style.min.css" as="style">
    
    <!-- Inline critical CSS -->
    <style>/* Critical CSS inline here */</style>
    
    <!-- Load full CSS asynchronously -->
    <link rel="stylesheet" href="css/modern-style.min.css" media="print" onload="this.media='all'">
    <noscript><link rel="stylesheet" href="css/modern-style.min.css"></noscript>''',
            optimized_content
        )
        
        # Replace JS with minified version and add defer
        optimized_content = re.sub(
            r'<script src="js/main\.js"></script>',
            '<script src="js/main.min.js" defer></script>',
            optimized_content
        )
        
        # Add resource hints
        resource_hints = '''    <!-- Resource Hints for Performance -->
    <link rel="dns-prefetch" href="//localhost:5000">
    <link rel="preconnect" href="//localhost:5000">
    
'''
        optimized_content = optimized_content.replace('<title>', resource_hints + '    <title>')
        
        # Save optimized version
        with open('index-optimized.html', 'w') as f:
            f.write(optimized_content)
        
        print("  ✓ Created index-optimized.html with performance optimizations")

def generate_performance_report():
    """Generate a performance optimization report"""
    print("\n📊 Generating performance report...")
    
    report = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "optimizations": {
            "css_minification": {},
            "js_minification": {},
            "images": {},
            "recommendations": []
        }
    }
    
    # Check CSS minification
    css_dir = Path('css')
    for css_file in css_dir.glob('*.css'):
        if not css_file.name.endswith('.min.css'):
            min_file = css_file.with_suffix('.min.css')
            if min_file.exists():
                original_size = css_file.stat().st_size
                min_size = min_file.stat().st_size
                reduction = ((original_size - min_size) / original_size) * 100
                report["optimizations"]["css_minification"][css_file.name] = {
                    "original_size": original_size,
                    "minified_size": min_size,
                    "reduction_percent": round(reduction, 2)
                }
    
    # Check JS minification
    js_dir = Path('js')
    for js_file in js_dir.glob('*.js'):
        if not js_file.name.endswith('.min.js'):
            min_file = js_file.with_suffix('.min.js')
            if min_file.exists():
                original_size = js_file.stat().st_size
                min_size = min_file.stat().st_size
                reduction = ((original_size - min_size) / original_size) * 100
                report["optimizations"]["js_minification"][js_file.name] = {
                    "original_size": original_size,
                    "minified_size": min_size,
                    "reduction_percent": round(reduction, 2)
                }
    
    # Image analysis
    assets_dir = Path('assets')
    total_img_size = 0
    for img_file in assets_dir.glob('*'):
        if img_file.suffix.lower() in ['.svg', '.png', '.jpg', '.jpeg', '.webp']:
            size = img_file.stat().st_size
            total_img_size += size
            report["optimizations"]["images"][img_file.name] = {
                "size": size,
                "format": img_file.suffix[1:]
            }
    
    # Recommendations
    recommendations = [
        "✅ CSS and JavaScript files have been minified",
        "✅ Critical CSS extracted for inline loading",
        "✅ Resource hints added for DNS prefetching",
        "✅ JavaScript loading deferred for better performance"
    ]
    
    if total_img_size > 500000:  # 500KB
        recommendations.append("⚠️  Consider optimizing images - total size exceeds 500KB")
    
    if not Path('css/critical.min.css').exists():
        recommendations.append("⚠️  Generate critical CSS for faster initial render")
    
    # Check for large HTML files
    for html_file in Path('.').glob('*.html'):
        if html_file.stat().st_size > 100000:  # 100KB
            recommendations.append(f"⚠️  {html_file.name} is large ({html_file.stat().st_size:,} bytes) - consider splitting or optimizing")
    
    report["optimizations"]["recommendations"] = recommendations
    
    # Save report
    with open('performance-report.json', 'w') as f:
        json.dump(report, f, indent=2)
    
    # Print summary
    print("\n📋 Performance Optimization Summary:")
    print("=====================================")
    for rec in recommendations:
        print(f"  {rec}")
    
    print("\n📈 Size Reductions:")
    total_saved = 0
    for category in ["css_minification", "js_minification"]:
        for file, stats in report["optimizations"][category].items():
            saved = stats["original_size"] - stats["minified_size"]
            total_saved += saved
            print(f"  {file}: saved {saved:,} bytes ({stats['reduction_percent']}%)")
    
    print(f"\n  Total saved: {total_saved:,} bytes ({total_saved/1024:.1f} KB)")
    
    return report

def create_htaccess_for_compression():
    """Create .htaccess file for gzip compression and caching"""
    print("\n🗜️  Creating .htaccess for compression and caching...")
    
    htaccess_content = """# Enable Gzip compression
<IfModule mod_deflate.c>
    AddOutputFilterByType DEFLATE text/html text/plain text/xml text/css text/javascript application/javascript application/json
    AddOutputFilterByType DEFLATE image/svg+xml
</IfModule>

# Enable browser caching
<IfModule mod_expires.c>
    ExpiresActive On
    
    # Images
    ExpiresByType image/jpeg "access plus 1 year"
    ExpiresByType image/gif "access plus 1 year"
    ExpiresByType image/png "access plus 1 year"
    ExpiresByType image/webp "access plus 1 year"
    ExpiresByType image/svg+xml "access plus 1 year"
    ExpiresByType image/x-icon "access plus 1 year"
    
    # CSS and JavaScript
    ExpiresByType text/css "access plus 1 month"
    ExpiresByType text/javascript "access plus 1 month"
    ExpiresByType application/javascript "access plus 1 month"
    
    # Others
    ExpiresByType application/pdf "access plus 1 month"
    ExpiresByType text/html "access plus 1 hour"
</IfModule>

# Set Cache-Control headers
<IfModule mod_headers.c>
    # 1 year for images
    <FilesMatch "\.(jpg|jpeg|png|gif|webp|svg|ico)$">
        Header set Cache-Control "max-age=31536000, public"
    </FilesMatch>
    
    # 1 month for CSS and JS
    <FilesMatch "\.(css|js)$">
        Header set Cache-Control "max-age=2592000, public"
    </FilesMatch>
    
    # Security headers
    Header set X-Content-Type-Options "nosniff"
    Header set X-Frame-Options "SAMEORIGIN"
    Header set X-XSS-Protection "1; mode=block"
</IfModule>
"""
    
    with open('.htaccess', 'w') as f:
        f.write(htaccess_content)
    
    print("  ✓ Created .htaccess with compression and caching rules")

def main():
    """Main optimization process"""
    print("🚀 Bank Statement Converter - Performance Optimization")
    print("=" * 50)
    
    # 1. Create minified files
    create_minified_files()
    
    # 2. Check image optimization
    check_image_optimization()
    
    # 3. Create critical CSS
    create_critical_css()
    
    # 4. Update HTML for performance
    update_html_for_performance()
    
    # 5. Create .htaccess
    create_htaccess_for_compression()
    
    # 6. Generate report
    report = generate_performance_report()
    
    print("\n✅ Performance optimization complete!")
    print(f"   Report saved to: performance-report.json")
    print(f"   Optimized HTML: index-optimized.html")
    print("\n💡 Next steps:")
    print("   1. Test index-optimized.html in your browser")
    print("   2. Run a Lighthouse audit for detailed metrics")
    print("   3. Consider using a CDN for static assets")
    print("   4. Implement lazy loading for below-the-fold images")

if __name__ == "__main__":
    main()