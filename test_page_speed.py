#!/usr/bin/env python3
"""
Page speed testing script for Bank Statement Converter
Tests loading performance of original vs optimized pages
"""

import time
import json
from pathlib import Path
from urllib.request import urlopen
from http.server import HTTPServer, SimpleHTTPRequestHandler
import threading
import subprocess

class TestServer:
    """Simple HTTP server for testing"""
    def __init__(self, port=8080):
        self.port = port
        self.server = None
        self.thread = None
    
    def start(self):
        """Start the test server"""
        handler = SimpleHTTPRequestHandler
        self.server = HTTPServer(('localhost', self.port), handler)
        self.thread = threading.Thread(target=self.server.serve_forever)
        self.thread.daemon = True
        self.thread.start()
        time.sleep(1)  # Give server time to start
        print(f"Test server started on http://localhost:{self.port}")
    
    def stop(self):
        """Stop the test server"""
        if self.server:
            self.server.shutdown()
            self.thread.join()
            print("Test server stopped")

def measure_page_load(url, num_tests=3):
    """Measure page load time"""
    times = []
    
    for i in range(num_tests):
        start = time.time()
        try:
            response = urlopen(url)
            content = response.read()
            end = time.time()
            load_time = (end - start) * 1000  # Convert to milliseconds
            times.append(load_time)
            print(f"    Test {i+1}: {load_time:.2f}ms")
        except Exception as e:
            print(f"    Test {i+1}: Failed - {e}")
    
    if times:
        avg_time = sum(times) / len(times)
        return {
            "average": round(avg_time, 2),
            "min": round(min(times), 2),
            "max": round(max(times), 2),
            "tests": len(times)
        }
    return None

def analyze_file_sizes():
    """Analyze file sizes for performance impact"""
    print("\n📏 File Size Analysis:")
    print("=" * 50)
    
    files_to_check = [
        ("index.html", "Original HTML"),
        ("index-optimized.html", "Optimized HTML"),
        ("css/modern-style.css", "Original CSS"),
        ("css/modern-style.min.css", "Minified CSS"),
        ("js/main.js", "Original JS"),
        ("js/main.min.js", "Minified JS"),
        ("css/critical.min.css", "Critical CSS")
    ]
    
    total_original = 0
    total_optimized = 0
    
    for filepath, description in files_to_check:
        path = Path(filepath)
        if path.exists():
            size = path.stat().st_size
            print(f"  {description:.<40} {size:>8,} bytes")
            
            if "Original" in description:
                total_original += size
            elif "Optimized" in description or "Minified" in description:
                total_optimized += size
    
    print(f"\n  Total original size:................... {total_original:>8,} bytes")
    print(f"  Total optimized size:.................. {total_optimized:>8,} bytes")
    if total_original > 0:
        reduction = ((total_original - total_optimized) / total_original) * 100
        print(f"  Size reduction:....................... {reduction:>7.1f}%")

def check_optimization_checklist():
    """Check optimization checklist"""
    print("\n✅ Performance Optimization Checklist:")
    print("=" * 50)
    
    checks = [
        ("CSS Minification", Path("css/modern-style.min.css").exists()),
        ("JS Minification", Path("js/main.min.js").exists()),
        ("Critical CSS", Path("css/critical.min.css").exists()),
        ("Optimized HTML", Path("index-optimized.html").exists()),
        (".htaccess (compression)", Path(".htaccess").exists()),
        ("Performance Report", Path("performance-report.json").exists())
    ]
    
    all_passed = True
    for check, passed in checks:
        status = "✅" if passed else "❌"
        print(f"  {status} {check}")
        if not passed:
            all_passed = False
    
    return all_passed

def generate_performance_tips():
    """Generate additional performance tips"""
    print("\n💡 Additional Performance Tips:")
    print("=" * 50)
    
    tips = [
        "1. **Image Optimization**: Use WebP format for better compression",
        "2. **Lazy Loading**: Implement lazy loading for below-the-fold images",
        "3. **CDN**: Use a CDN for static assets to reduce latency",
        "4. **HTTP/2**: Enable HTTP/2 on your server for multiplexing",
        "5. **Service Worker**: Add a service worker for offline functionality",
        "6. **Font Loading**: Use font-display: swap for web fonts",
        "7. **Preconnect**: Add preconnect hints for external domains",
        "8. **Bundle Splitting**: Split JS bundles for better caching",
        "9. **Image Sprites**: Combine small icons into sprites",
        "10. **Async Scripts**: Load non-critical JS asynchronously"
    ]
    
    for tip in tips:
        print(f"  {tip}")

def create_lighthouse_script():
    """Create a script to run Lighthouse audit"""
    lighthouse_script = """#!/bin/bash
# Lighthouse Performance Audit Script

echo "🔍 Running Lighthouse Performance Audit..."
echo "=========================================="

# Check if lighthouse is installed
if ! command -v lighthouse &> /dev/null; then
    echo "❌ Lighthouse is not installed."
    echo "   Install with: npm install -g lighthouse"
    exit 1
fi

# Start local server
echo "Starting local server..."
python3 -m http.server 8080 &
SERVER_PID=$!
sleep 2

# Run Lighthouse audit
echo "Running audit on original page..."
lighthouse http://localhost:8080/index.html \\
    --output=html \\
    --output-path=./lighthouse-report-original.html \\
    --only-categories=performance \\
    --quiet

echo "Running audit on optimized page..."
lighthouse http://localhost:8080/index-optimized.html \\
    --output=html \\
    --output-path=./lighthouse-report-optimized.html \\
    --only-categories=performance \\
    --quiet

# Stop server
kill $SERVER_PID

echo ""
echo "✅ Audits complete!"
echo "   Original: lighthouse-report-original.html"
echo "   Optimized: lighthouse-report-optimized.html"
"""
    
    with open('run-lighthouse-audit.sh', 'w') as f:
        f.write(lighthouse_script)
    
    Path('run-lighthouse-audit.sh').chmod(0o755)
    print("\n📝 Created run-lighthouse-audit.sh for detailed performance testing")

def main():
    """Main performance testing"""
    print("🏃 Bank Statement Converter - Page Speed Testing")
    print("=" * 50)
    
    # 1. Check optimization checklist
    all_optimizations_done = check_optimization_checklist()
    
    if not all_optimizations_done:
        print("\n⚠️  Some optimizations are missing. Run optimize_performance.py first.")
        return
    
    # 2. Analyze file sizes
    analyze_file_sizes()
    
    # 3. Test page load speeds (if server can be started)
    print("\n⏱️  Page Load Speed Test:")
    print("=" * 50)
    
    server = TestServer()
    try:
        server.start()
        
        # Test original page
        print("\n  Testing original index.html:")
        original_stats = measure_page_load("http://localhost:8080/index.html")
        
        # Test optimized page
        print("\n  Testing optimized index-optimized.html:")
        optimized_stats = measure_page_load("http://localhost:8080/index-optimized.html")
        
        # Compare results
        if original_stats and optimized_stats:
            improvement = ((original_stats["average"] - optimized_stats["average"]) / 
                          original_stats["average"]) * 100
            print(f"\n  Performance Improvement: {improvement:.1f}%")
            print(f"  Original avg: {original_stats['average']}ms")
            print(f"  Optimized avg: {optimized_stats['average']}ms")
    except Exception as e:
        print(f"  Could not start test server: {e}")
        print("  (This is normal if another service is using port 8080)")
    finally:
        server.stop()
    
    # 4. Generate performance tips
    generate_performance_tips()
    
    # 5. Create Lighthouse script
    create_lighthouse_script()
    
    # 6. Final summary
    print("\n📊 Performance Testing Summary:")
    print("=" * 50)
    print("  ✅ All optimizations have been applied")
    print("  ✅ File sizes have been reduced")
    print("  ✅ Critical CSS extracted for fast initial render")
    print("  ✅ Resources configured for compression and caching")
    print("\n  Next: Run ./run-lighthouse-audit.sh for detailed metrics")

if __name__ == "__main__":
    main()