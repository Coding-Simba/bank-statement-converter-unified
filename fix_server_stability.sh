#!/bin/bash

# AWS Lightsail Server Stability Fix Script
# Run this when your server is accessible to prevent future outages

SERVER_IP="3.235.19.83"
KEY_PATH="/Users/MAC/Downloads/bank-statement-converter.pem"
SERVER_USER="ubuntu"

echo "AWS Lightsail Server Stability Fix"
echo "=================================="
echo "This script will implement fixes to prevent server inaccessibility"
echo ""

# Check if we can connect
if ! ssh -o ConnectTimeout=5 -i "$KEY_PATH" "$SERVER_USER@$SERVER_IP" "echo 'Connected'" 2>/dev/null; then
    echo "❌ Cannot connect to server. Please try again when server is accessible."
    exit 1
fi

echo "✅ Connected to server"
echo ""

# 1. Add swap space
echo "1. ADDING SWAP SPACE (if not exists)..."
ssh -i "$KEY_PATH" "$SERVER_USER@$SERVER_IP" << 'EOF'
if ! swapon -s | grep -q swapfile; then
    echo "Creating 2GB swap file..."
    sudo fallocate -l 2G /swapfile
    sudo chmod 600 /swapfile
    sudo mkswap /swapfile
    sudo swapon /swapfile
    echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
    echo 'vm.swappiness=10' | sudo tee -a /etc/sysctl.conf
    echo "✅ Swap space added"
else
    echo "✅ Swap space already exists"
fi
swapon -s
EOF

# 2. Set up automatic cleanup
echo -e "\n2. SETTING UP AUTOMATIC CLEANUP..."
ssh -i "$KEY_PATH" "$SERVER_USER@$SERVER_IP" << 'EOF'
# Create cleanup script
cat > /home/ubuntu/cleanup_old_files.sh << 'SCRIPT'
#!/bin/bash
# Delete PDFs older than 1 day from uploads
find /home/ubuntu/bank-statement-converter-unified/uploads -name "*.pdf" -mtime +1 -delete 2>/dev/null
find /home/ubuntu/bank-statement-converter-unified/uploads -name "*.csv" -mtime +1 -delete 2>/dev/null

# Delete failed PDFs older than 30 days
find /home/ubuntu/bank-statement-converter-unified/backend/failed_pdfs -name "*.pdf" -mtime +30 -delete 2>/dev/null

# Clean package cache
sudo apt-get clean

# Rotate logs
sudo journalctl --vacuum-time=3d

echo "$(date): Cleanup completed" >> /home/ubuntu/cleanup.log
SCRIPT

chmod +x /home/ubuntu/cleanup_old_files.sh

# Add to crontab (runs daily at 3 AM)
(crontab -l 2>/dev/null | grep -v cleanup_old_files; echo "0 3 * * * /home/ubuntu/cleanup_old_files.sh") | crontab -

echo "✅ Automatic cleanup configured"
EOF

# 3. Configure service limits
echo -e "\n3. CONFIGURING SERVICE MEMORY LIMITS..."
ssh -i "$KEY_PATH" "$SERVER_USER@$SERVER_IP" << 'EOF'
# Create systemd override for backend service
sudo mkdir -p /etc/systemd/system/bank-converter-backend.service.d/
sudo tee /etc/systemd/system/bank-converter-backend.service.d/override.conf << OVERRIDE
[Service]
# Restart service if it fails
Restart=always
RestartSec=10

# Memory limits (adjust based on your instance size)
MemoryMax=600M
MemoryHigh=500M

# CPU limits (prevent 100% CPU usage)
CPUQuota=80%
OVERRIDE

sudo systemctl daemon-reload
echo "✅ Service limits configured"
EOF

# 4. Set up monitoring script
echo -e "\n4. SETTING UP HEALTH MONITORING..."
ssh -i "$KEY_PATH" "$SERVER_USER@$SERVER_IP" << 'EOF'
cat > /home/ubuntu/monitor_health.sh << 'MONITOR'
#!/bin/bash
# Health monitoring script

LOG_FILE="/home/ubuntu/health-monitor.log"

# Check memory usage
MEMORY_USAGE=$(free | grep Mem | awk '{print int($3/$2 * 100)}')
SWAP_USAGE=$(free | grep Swap | awk '{print ($3/$2 * 100)}')

echo "$(date): Memory: ${MEMORY_USAGE}%, Swap: ${SWAP_USAGE}%" >> $LOG_FILE

# If memory usage is critical (>90%), restart backend
if [ $MEMORY_USAGE -gt 90 ]; then
    echo "$(date): High memory usage detected: $MEMORY_USAGE%" >> $LOG_FILE
    sudo systemctl restart bank-converter-backend
    echo "$(date): Restarted backend service" >> $LOG_FILE
fi

# Check disk usage
DISK_USAGE=$(df -h / | tail -1 | awk '{print int($5)}')
if [ $DISK_USAGE -gt 85 ]; then
    echo "$(date): High disk usage detected: $DISK_USAGE%" >> $LOG_FILE
    /home/ubuntu/cleanup_old_files.sh
fi

# Check if services are running
for service in nginx bank-converter-backend; do
    if ! systemctl is-active --quiet $service; then
        echo "$(date): Service $service is not running, attempting restart" >> $LOG_FILE
        sudo systemctl start $service
    fi
done
MONITOR

chmod +x /home/ubuntu/monitor_health.sh

# Add to crontab (runs every 5 minutes)
(crontab -l 2>/dev/null | grep -v monitor_health; echo "*/5 * * * * /home/ubuntu/monitor_health.sh") | crontab -

echo "✅ Health monitoring configured"
EOF

# 5. Configure log rotation
echo -e "\n5. CONFIGURING LOG ROTATION..."
ssh -i "$KEY_PATH" "$SERVER_USER@$SERVER_IP" << 'EOF'
sudo tee /etc/logrotate.d/bank-converter << LOGROTATE
/home/ubuntu/bank-statement-converter-unified/backend/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    create 0640 ubuntu ubuntu
    postrotate
        systemctl reload bank-converter-backend > /dev/null 2>&1 || true
    endscript
}

/home/ubuntu/*.log {
    weekly
    rotate 4
    compress
    delaycompress
    missingok
    notifempty
}
LOGROTATE

echo "✅ Log rotation configured"
EOF

# 6. Check and display system status
echo -e "\n6. CURRENT SYSTEM STATUS:"
ssh -i "$KEY_PATH" "$SERVER_USER@$SERVER_IP" << 'EOF'
echo "Memory Usage:"
free -h
echo -e "\nDisk Usage:"
df -h /
echo -e "\nSystem Load:"
uptime
echo -e "\nService Status:"
systemctl status nginx --no-pager | head -3
systemctl status bank-converter-backend --no-pager | head -3
EOF

# 7. Restart services to apply changes
echo -e "\n7. RESTARTING SERVICES..."
ssh -i "$KEY_PATH" "$SERVER_USER@$SERVER_IP" << 'EOF'
sudo systemctl daemon-reload
sudo systemctl restart bank-converter-backend
sudo systemctl restart nginx
echo "✅ Services restarted"
EOF

echo -e "\n✅ ALL FIXES APPLIED!"
echo ""
echo "Your server should now be more stable. The following has been configured:"
echo "- 2GB swap space for memory overflow"
echo "- Automatic daily cleanup of old files"
echo "- Memory limits for backend service"
echo "- Health monitoring every 5 minutes"
echo "- Log rotation to prevent disk fill"
echo ""
echo "Monitor your server with: ssh -i $KEY_PATH $SERVER_USER@$SERVER_IP 'tail -f /home/ubuntu/health-monitor.log'"