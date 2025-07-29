# AWS Lightsail Server Stability Fixes

## Most Common Causes of Inaccessibility

### 1. **Memory Exhaustion (Most Likely)**
Small Lightsail instances often run out of memory, causing the system to become unresponsive.

**Quick Fix - Add Swap Space:**
```bash
# SSH into your server when accessible
ssh -i /Users/MAC/Downloads/bank-statement-converter.pem ubuntu@3.235.19.83

# Create 2GB swap file
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# Make permanent
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab

# Configure swappiness
echo 'vm.swappiness=10' | sudo tee -a /etc/sysctl.conf
```

### 2. **Service Memory Limits**
Backend services consuming too much memory.

**Fix - Add systemd memory limits:**
```bash
# Edit backend service
sudo systemctl edit bank-converter-backend

# Add these lines:
[Service]
MemoryMax=512M
MemoryHigh=400M
Restart=always
RestartSec=10
```

### 3. **Log Files Filling Disk**
Logs can quickly fill small disks.

**Fix - Setup log rotation:**
```bash
# Create logrotate config
sudo tee /etc/logrotate.d/bank-converter << EOF
/home/ubuntu/bank-statement-converter-unified/backend/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    create 0640 ubuntu ubuntu
}
EOF

# Clean old logs
sudo find /var/log -name "*.log" -mtime +7 -delete
```

### 4. **CPU Burst Credits Depleted**
Lightsail uses burstable CPU performance.

**Check CPU credits:**
```bash
# Install CloudWatch tools
sudo apt-get install -y amazon-cloudwatch-utils

# Or check in AWS Console:
# Lightsail > Instance > Metrics > CPU burst capacity
```

### 5. **Automatic Security Updates**
Ubuntu's unattended-upgrades can cause unexpected reboots.

**Fix - Configure update schedule:**
```bash
# Edit auto-update config
sudo nano /etc/apt/apt.conf.d/50unattended-upgrades

# Set specific reboot time
Unattended-Upgrade::Automatic-Reboot "true";
Unattended-Upgrade::Automatic-Reboot-Time "03:00";
```

## Monitoring Script

Create a monitoring script that runs via cron:

```bash
#!/bin/bash
# /home/ubuntu/monitor_health.sh

# Check memory usage
MEMORY_USAGE=$(free | grep Mem | awk '{print int($3/$2 * 100)}')
if [ $MEMORY_USAGE -gt 90 ]; then
    # Restart backend if memory is high
    sudo systemctl restart bank-converter-backend
    echo "$(date): Restarted backend due to high memory usage: $MEMORY_USAGE%" >> /var/log/health-monitor.log
fi

# Check disk usage
DISK_USAGE=$(df -h / | tail -1 | awk '{print int($5)}')
if [ $DISK_USAGE -gt 85 ]; then
    # Clean up old files
    find /home/ubuntu/bank-statement-converter-unified/uploads -name "*.pdf" -mtime +1 -delete
    find /home/ubuntu/bank-statement-converter-unified/backend/failed_pdfs -name "*.pdf" -mtime +30 -delete
    echo "$(date): Cleaned up old files due to high disk usage: $DISK_USAGE%" >> /var/log/health-monitor.log
fi
```

**Setup cron job:**
```bash
# Add to crontab
crontab -e

# Add this line to run every 5 minutes
*/5 * * * * /home/ubuntu/monitor_health.sh
```

## Instance Upgrade Recommendations

If problems persist, consider upgrading your Lightsail instance:

| Current Issue | Recommended Instance |
|--------------|---------------------|
| < 1GB RAM | 2GB instance ($10/month) |
| CPU credits depleting | 2 vCPU instance |
| High traffic | Load balancer + 2 instances |

## Quick Recovery Script

When server becomes accessible, run this to prevent future issues:

```bash
#!/bin/bash
# save as: emergency_fix.sh

# 1. Add swap if not exists
if ! swapon -s | grep -q swapfile; then
    sudo fallocate -l 2G /swapfile
    sudo chmod 600 /swapfile
    sudo mkswap /swapfile
    sudo swapon /swapfile
fi

# 2. Clean up space
sudo apt-get clean
sudo journalctl --vacuum-time=3d
find /home/ubuntu/bank-statement-converter-unified/uploads -name "*.pdf" -mtime +1 -delete

# 3. Restart services
sudo systemctl restart nginx
sudo systemctl restart bank-converter-backend

# 4. Set up monitoring
free -h
df -h
systemctl status bank-converter-backend
```

## Permanent Solution

The most reliable solution is to:
1. **Upgrade to 2GB RAM instance** ($10/month)
2. **Enable automatic snapshots** (backup)
3. **Set up CloudWatch alarms** for high CPU/memory
4. **Use Lightsail load balancer** for high availability

This will prevent most accessibility issues you're experiencing.