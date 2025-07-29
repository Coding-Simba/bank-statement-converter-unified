#!/bin/bash

# AWS Lightsail Server Diagnostic Script
# This script helps diagnose why your server becomes inaccessible

SERVER_IP="3.235.19.83"
KEY_PATH="/Users/MAC/Downloads/bank-statement-converter.pem"
SERVER_USER="ubuntu"

echo "AWS Lightsail Server Diagnostic Report"
echo "======================================"
echo "Date: $(date)"
echo "Server IP: $SERVER_IP"
echo ""

# 1. Test basic connectivity
echo "1. TESTING BASIC CONNECTIVITY"
echo "-----------------------------"
echo -n "Ping test (5 packets)... "
if ping -c 5 -W 2 $SERVER_IP > /dev/null 2>&1; then
    echo "✓ Server is reachable"
    ping -c 5 $SERVER_IP | grep "round-trip"
else
    echo "✗ Server is not responding to ping"
    echo "  Note: Security group might block ICMP"
fi

# 2. Test SSH connectivity
echo -e "\n2. TESTING SSH CONNECTIVITY"
echo "-----------------------------"
echo -n "SSH port 22 test... "
if nc -z -w5 $SERVER_IP 22 2>/dev/null; then
    echo "✓ SSH port is open"
else
    echo "✗ SSH port is not accessible"
    echo "  Possible causes:"
    echo "  - Security group blocking port 22"
    echo "  - SSH service is down"
    echo "  - Server is overloaded"
fi

# 3. Try SSH connection with timeout
echo -e "\n3. ATTEMPTING SSH CONNECTION"
echo "-----------------------------"
if ssh -o ConnectTimeout=10 -o StrictHostKeyChecking=no -i "$KEY_PATH" "$SERVER_USER@$SERVER_IP" "echo 'SSH connection successful'" 2>/dev/null; then
    echo "✓ SSH connection successful"
    
    # If connected, run diagnostics
    echo -e "\n4. SERVER DIAGNOSTICS"
    echo "-----------------------------"
    
    # Check system load
    echo "System Load:"
    ssh -i "$KEY_PATH" "$SERVER_USER@$SERVER_IP" "uptime" 2>/dev/null
    
    # Check memory usage
    echo -e "\nMemory Usage:"
    ssh -i "$KEY_PATH" "$SERVER_USER@$SERVER_IP" "free -h" 2>/dev/null
    
    # Check disk usage
    echo -e "\nDisk Usage:"
    ssh -i "$KEY_PATH" "$SERVER_USER@$SERVER_IP" "df -h /" 2>/dev/null
    
    # Check running services
    echo -e "\nKey Services Status:"
    ssh -i "$KEY_PATH" "$SERVER_USER@$SERVER_IP" "sudo systemctl status nginx --no-pager | head -5" 2>/dev/null
    ssh -i "$KEY_PATH" "$SERVER_USER@$SERVER_IP" "sudo systemctl status bank-converter-backend --no-pager | head -5" 2>/dev/null
    
    # Check for OOM killer activity
    echo -e "\nChecking for Out-of-Memory kills (last 10):"
    ssh -i "$KEY_PATH" "$SERVER_USER@$SERVER_IP" "sudo dmesg | grep -i 'killed process' | tail -10" 2>/dev/null
    
    # Check system logs for errors
    echo -e "\nRecent system errors:"
    ssh -i "$KEY_PATH" "$SERVER_USER@$SERVER_IP" "sudo journalctl -p err -n 20 --no-pager" 2>/dev/null
    
else
    echo "✗ SSH connection failed"
    echo "  Error details:"
    ssh -v -o ConnectTimeout=10 -i "$KEY_PATH" "$SERVER_USER@$SERVER_IP" "exit" 2>&1 | grep -E "debug1:|Connection|refused|timeout" | head -10
fi

# 4. Test web services
echo -e "\n5. TESTING WEB SERVICES"
echo "-----------------------------"
echo -n "HTTP port 80 test... "
if nc -z -w5 $SERVER_IP 80 2>/dev/null; then
    echo "✓ HTTP port is open"
    # Test actual HTTP response
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" -m 5 "http://$SERVER_IP/" 2>/dev/null)
    echo "  HTTP response code: $HTTP_CODE"
else
    echo "✗ HTTP port is not accessible"
fi

echo -n "Backend API port 5000 test... "
if nc -z -w5 $SERVER_IP 5000 2>/dev/null; then
    echo "✓ API port is open"
else
    echo "✗ API port is not accessible (might be behind reverse proxy)"
fi

# 5. DNS resolution test
echo -e "\n6. DNS RESOLUTION TEST"
echo "-----------------------------"
echo -n "Resolving bankcsvconverter.com... "
RESOLVED_IP=$(dig +short bankcsvconverter.com @8.8.8.8 | head -1)
if [ -n "$RESOLVED_IP" ]; then
    echo "✓ Resolves to: $RESOLVED_IP"
    if [ "$RESOLVED_IP" != "$SERVER_IP" ]; then
        echo "  ⚠ Warning: DNS points to different IP than expected!"
    fi
else
    echo "✗ DNS resolution failed"
fi

# 6. Common issues and solutions
echo -e "\n7. COMMON ISSUES & SOLUTIONS"
echo "-----------------------------"
echo "Based on the diagnostics, here are possible issues:"
echo ""
echo "1. MEMORY ISSUES (Most Common for Lightsail)"
echo "   - Small instances (512MB-1GB) can run out of memory"
echo "   - Python/Node processes can consume significant memory"
echo "   - Solution: Upgrade instance or add swap space"
echo ""
echo "2. CPU THROTTLING"
echo "   - Lightsail has CPU burst credits"
echo "   - Sustained high CPU usage depletes credits"
echo "   - Solution: Optimize code or upgrade instance"
echo ""
echo "3. DISK SPACE"
echo "   - Logs and temp files can fill disk"
echo "   - Solution: Clean up logs, add log rotation"
echo ""
echo "4. SECURITY GROUP SETTINGS"
echo "   - Ensure ports 22, 80, 443 are open"
echo "   - Check source IP restrictions"
echo ""
echo "5. AUTOMATIC UPDATES"
echo "   - Ubuntu unattended-upgrades can cause reboots"
echo "   - Solution: Configure update schedule"

echo -e "\nDiagnostic complete!"