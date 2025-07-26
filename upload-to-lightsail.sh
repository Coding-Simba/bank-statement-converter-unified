#!/bin/bash
# Script to upload your code to Lightsail instance

# Replace with your Lightsail instance IP
INSTANCE_IP="YOUR_LIGHTSAIL_IP"

echo "Uploading Bank Statement Converter to Lightsail..."

# Create directories on remote
ssh ubuntu@$INSTANCE_IP "mkdir -p /home/ubuntu/bank-statement-converter/{backend,frontend/js}"

# Upload backend files
echo "Uploading backend..."
scp -r backend/* ubuntu@$INSTANCE_IP:/home/ubuntu/bank-statement-converter/backend/

# Upload frontend files
echo "Uploading frontend..."
scp index.html modern-homepage-fixed.html ubuntu@$INSTANCE_IP:/home/ubuntu/bank-statement-converter/frontend/
scp -r css ubuntu@$INSTANCE_IP:/home/ubuntu/bank-statement-converter/frontend/
scp -r js/* ubuntu@$INSTANCE_IP:/home/ubuntu/bank-statement-converter/frontend/js/

# Upload configuration files
scp lightsail-setup.sh ubuntu@$INSTANCE_IP:/home/ubuntu/

# Restart service
echo "Restarting service..."
ssh ubuntu@$INSTANCE_IP "sudo systemctl restart bankconverter"

echo "Upload complete!"
echo "Check status: ssh ubuntu@$INSTANCE_IP 'sudo systemctl status bankconverter'"