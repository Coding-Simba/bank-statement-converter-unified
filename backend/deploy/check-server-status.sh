#!/bin/bash
# Script to check the status of BankCSV backend deployment

echo "=== BankCSV Backend Status Check ==="
echo ""

# Check if backend service exists and is running
echo "1. Backend Service Status:"
if systemctl is-active --quiet bankcsv-backend; then
    echo "   ✓ Backend service is running"
    systemctl status bankcsv-backend --no-pager | grep -E "Active:|Main PID:"
else
    if systemctl list-unit-files | grep -q bankcsv-backend; then
        echo "   ✗ Backend service exists but is not running"
        echo "   Run: sudo systemctl start bankcsv-backend"
    else
        echo "   ✗ Backend service not installed"
        echo "   Run the setup-server.sh script first"
    fi
fi
echo ""

# Check if backend is responding
echo "2. Backend API Check:"
if curl -s http://localhost:5000/health > /dev/null 2>&1; then
    echo "   ✓ Backend API is responding on port 5000"
    echo "   Response: $(curl -s http://localhost:5000/health)"
else
    echo "   ✗ Backend API not responding on port 5000"
    echo "   Check logs: sudo journalctl -u bankcsv-backend -n 50"
fi
echo ""

# Check nginx configuration
echo "3. Nginx Configuration:"
if nginx -t 2>/dev/null; then
    echo "   ✓ Nginx configuration is valid"
else
    echo "   ✗ Nginx configuration has errors"
    sudo nginx -t
fi

# Check if nginx is proxying correctly
if grep -q "proxy_pass.*5000" /etc/nginx/sites-enabled/* 2>/dev/null; then
    echo "   ✓ Nginx proxy configuration found"
else
    echo "   ✗ Nginx proxy to backend not configured"
    echo "   Add proxy configuration for /api/ location"
fi
echo ""

# Check Python dependencies
echo "4. Python Environment:"
if [ -d "/home/bankcsv/backend/venv" ]; then
    echo "   ✓ Virtual environment exists"
    source /home/bankcsv/backend/venv/bin/activate 2>/dev/null
    
    # Check key packages
    packages=("fastapi" "uvicorn" "pandas" "PyPDF2" "tabula-py")
    missing=()
    for pkg in "${packages[@]}"; do
        if ! pip show $pkg >/dev/null 2>&1; then
            missing+=($pkg)
        fi
    done
    
    if [ ${#missing[@]} -eq 0 ]; then
        echo "   ✓ All key Python packages installed"
    else
        echo "   ✗ Missing Python packages: ${missing[*]}"
        echo "   Run: pip install ${missing[*]}"
    fi
else
    echo "   ✗ Virtual environment not found"
fi
echo ""

# Check file permissions
echo "5. File Permissions:"
if [ -f "/home/bankcsv/backend/.env" ]; then
    echo "   ✓ .env file exists"
    perms=$(stat -c %a /home/bankcsv/backend/.env)
    if [ "$perms" = "600" ]; then
        echo "   ✓ .env has correct permissions (600)"
    else
        echo "   ⚠ .env has permissions $perms (should be 600)"
    fi
else
    echo "   ✗ .env file not found"
fi
echo ""

# Check logs for recent errors
echo "6. Recent Errors (last 10 lines):"
if [ -f "/home/bankcsv/logs/backend.error.log" ]; then
    tail -10 /home/bankcsv/logs/backend.error.log 2>/dev/null || echo "   No recent errors"
else
    echo "   Error log file not found"
fi
echo ""

# Test API endpoint
echo "7. API Endpoint Test:"
response=$(curl -s -w "\n%{http_code}" https://bankcsvconverter.com/api/health 2>/dev/null)
http_code=$(echo "$response" | tail -n1)
body=$(echo "$response" | head -n-1)

if [ "$http_code" = "200" ]; then
    echo "   ✓ API is accessible via HTTPS"
    echo "   Response: $body"
elif [ "$http_code" = "502" ]; then
    echo "   ✗ 502 Bad Gateway - Backend not running or not accessible"
elif [ "$http_code" = "404" ]; then
    echo "   ✗ 404 Not Found - Nginx not configured to proxy /api/"
else
    echo "   ✗ HTTP $http_code - Check nginx and backend configuration"
fi
echo ""

echo "=== Summary ==="
echo "Run this script with sudo for more detailed information"
echo "To view full logs: sudo journalctl -u bankcsv-backend -f"