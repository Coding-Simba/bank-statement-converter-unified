#!/bin/bash

# Setup SSL on AWS EC2 with Cloudflare Origin Certificate
# This creates a secure connection between Cloudflare and your origin server

echo "=== Cloudflare Origin SSL Setup ==="
echo "This script will help you set up SSL on your AWS server"
echo ""

# Instructions for getting Cloudflare Origin Certificate
cat << 'EOF'
STEP 1: Get Cloudflare Origin Certificate
=========================================
1. Log in to Cloudflare Dashboard
2. Go to SSL/TLS → Origin Server
3. Click "Create Certificate"
4. Choose:
   - Private key type: RSA
   - Certificate Validity: 15 years
   - Hostnames: *.bankcsvconverter.com, bankcsvconverter.com
5. Copy the Origin Certificate and Private Key

STEP 2: On your AWS server, run these commands:
===============================================

# Connect to your server
ssh -i your-key.pem ubuntu@3.235.19.83

# Create SSL directory
sudo mkdir -p /etc/nginx/ssl

# Create certificate file
sudo nano /etc/nginx/ssl/cloudflare-origin.crt
# Paste the Origin Certificate here and save

# Create private key file  
sudo nano /etc/nginx/ssl/cloudflare-origin.key
# Paste the Private Key here and save

# Set proper permissions
sudo chmod 600 /etc/nginx/ssl/cloudflare-origin.key
sudo chmod 644 /etc/nginx/ssl/cloudflare-origin.crt

# Create Nginx HTTPS configuration
sudo nano /etc/nginx/sites-available/bankcsvconverter-ssl

# Paste this configuration:
server {
    listen 443 ssl http2;
    server_name bankcsvconverter.com www.bankcsvconverter.com;

    ssl_certificate /etc/nginx/ssl/cloudflare-origin.crt;
    ssl_certificate_key /etc/nginx/ssl/cloudflare-origin.key;

    # SSL configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    root /var/www/html;
    index index.html index.htm;

    location / {
        try_files $uri $uri/ =404;
    }

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
}

# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name bankcsvconverter.com www.bankcsvconverter.com;
    return 301 https://$server_name$request_uri;
}

# Enable the new configuration
sudo ln -s /etc/nginx/sites-available/bankcsvconverter-ssl /etc/nginx/sites-enabled/
sudo rm /etc/nginx/sites-enabled/default  # Remove default if exists

# Test configuration
sudo nginx -t

# Reload Nginx
sudo systemctl reload nginx

# Update AWS Security Group to allow HTTPS (port 443) from Cloudflare IPs

STEP 3: Update Cloudflare Settings
==================================
1. Go to SSL/TLS → Overview
2. Change from "Flexible" to "Full" mode
3. This enables end-to-end encryption

STEP 4: Update AWS Security Group
=================================
Add inbound rule for HTTPS (port 443) from Cloudflare IPs:
- 173.245.48.0/20
- 103.21.244.0/22
- 103.22.200.0/22
- 103.31.4.0/22
- 141.101.64.0/18
- 108.162.192.0/18
- 190.93.240.0/20
- 188.114.96.0/20
- 197.234.240.0/22
- 198.41.128.0/17
- 162.158.0.0/15
- 104.16.0.0/13
- 104.24.0.0/14
- 172.64.0.0/13
- 131.0.72.0/22

EOF

echo ""
echo "Follow the steps above to enable HTTPS on your origin server!"