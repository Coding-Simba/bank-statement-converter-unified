#!/bin/bash
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
lighthouse http://localhost:8080/index.html \
    --output=html \
    --output-path=./lighthouse-report-original.html \
    --only-categories=performance \
    --quiet

echo "Running audit on optimized page..."
lighthouse http://localhost:8080/index-optimized.html \
    --output=html \
    --output-path=./lighthouse-report-optimized.html \
    --only-categories=performance \
    --quiet

# Stop server
kill $SERVER_PID

echo ""
echo "✅ Audits complete!"
echo "   Original: lighthouse-report-original.html"
echo "   Optimized: lighthouse-report-optimized.html"
