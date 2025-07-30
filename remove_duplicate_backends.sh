#!/bin/bash

# Remove Duplicate Backend Directories

SERVER_IP="3.235.19.83"
KEY_PATH="/Users/MAC/Downloads/bank-statement-converter.pem"
SERVER_USER="ubuntu"

echo "Removing Duplicate Backend Directories"
echo "====================================="
echo ""

# First, clean up locally
echo "LOCAL CLEANUP:"
echo "--------------"

# Check current directory structure
echo "Current local directory: $(pwd)"
echo ""

# Check if we're in the unified directory
if [[ $(pwd) == *"bank-statement-converter-unified"* ]]; then
    echo "✅ You're in the unified directory. This is the one we'll keep locally."
else
    echo "⚠️  Please run this from the bank-statement-converter-unified directory"
fi

echo ""
echo "SERVER CLEANUP:"
echo "---------------"

ssh -i "$KEY_PATH" "$SERVER_USER@$SERVER_IP" << 'EOF'

echo "1. Identifying directories on server:"
echo "Production (KEEP): /home/ubuntu/bank-statement-converter"
ls -la /home/ubuntu/bank-statement-converter 2>/dev/null | head -3
echo ""
echo "Unified (REMOVE): /home/ubuntu/bank-statement-converter-unified"
ls -la /home/ubuntu/bank-statement-converter-unified 2>/dev/null | head -3

echo -e "\n2. Checking which services are using which directories:"
echo "bankconverter service uses:"
grep WorkingDirectory /etc/systemd/system/bankconverter.service 2>/dev/null || echo "Not found"

echo -e "\n3. Backing up any unique files from unified before removal:"
# Create backup directory
mkdir -p /home/ubuntu/backup_unified_$(date +%Y%m%d)

# Backup any unique or newer files
echo "Backing up CLAUDE.md and other documentation..."
cp /home/ubuntu/bank-statement-converter-unified/*.md /home/ubuntu/backup_unified_$(date +%Y%m%d)/ 2>/dev/null || echo "No .md files to backup"

echo -e "\n4. Disabling and removing the duplicate service:"
sudo systemctl stop bank-converter-backend 2>/dev/null || echo "Service not running"
sudo systemctl disable bank-converter-backend 2>/dev/null || echo "Service not found"
sudo rm -f /etc/systemd/system/bank-converter-backend.service
sudo rm -rf /etc/systemd/system/bank-converter-backend.service.d/
sudo systemctl daemon-reload

echo -e "\n5. Removing the duplicate unified directory:"
echo "This will remove: /home/ubuntu/bank-statement-converter-unified"
echo "Removing in 3 seconds... (Ctrl+C to cancel)"
sleep 3
sudo rm -rf /home/ubuntu/bank-statement-converter-unified

echo -e "\n6. Cleaning up any remaining references:"
# Remove any systemd services referencing the unified directory
sudo grep -r "bank-statement-converter-unified" /etc/systemd/system/ 2>/dev/null | cut -d: -f1 | xargs -r sudo rm -f

echo -e "\n7. Final directory check:"
echo "Remaining directories:"
ls -la /home/ubuntu/ | grep bank

echo -e "\n8. Verifying production service is still running:"
sudo systemctl status bankconverter --no-pager | head -5

echo -e "\n✅ Server cleanup complete!"
echo "Production backend: /home/ubuntu/bank-statement-converter"
echo "Service: bankconverter.service"
echo "Port: 8000"

EOF

echo ""
echo "LOCAL DIRECTORY RECOMMENDATION:"
echo "==============================="
echo "Keep using: $(pwd)"
echo "This is your development directory with all the fixes."
echo ""
echo "The server now has only ONE backend directory:"
echo "- /home/ubuntu/bank-statement-converter (production)"
echo ""
echo "No more confusion! 🎉"