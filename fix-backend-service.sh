#!/bin/bash

# Update systemd service to use uvicorn
sudo tee /etc/systemd/system/bank-converter-backend.service > /dev/null << 'EOF'
[Unit]
Description=Bank Statement Converter Backend API
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/bank-statement-converter-unified/backend
Environment="PATH=/home/ubuntu/.local/bin:/usr/bin:/usr/local/bin"
Environment="PYTHONPATH=/home/ubuntu/bank-statement-converter-unified/backend"
ExecStart=/home/ubuntu/.local/bin/uvicorn main:app --host 0.0.0.0 --port 5000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Reload and restart
sudo systemctl daemon-reload
sudo systemctl restart bank-converter-backend
sleep 3
sudo systemctl status bank-converter-backend --no-pager