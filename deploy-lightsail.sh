#!/bin/bash
# Deploy to AWS Lightsail - Ultra cheap hosting

# Install on Lightsail instance (Ubuntu)
sudo apt update
sudo apt install -y python3-pip python3-venv nginx

# Clone your repo
git clone https://github.com/yourusername/bank-statement-converter.git
cd bank-statement-converter

# Setup Python environment
python3 -m venv venv
source venv/bin/activate
pip install -r backend/requirements-fastapi.txt
pip install gunicorn

# Setup Nginx
sudo tee /etc/nginx/sites-available/app << EOF
server {
    listen 80;
    server_name your-domain.com;

    # Frontend
    location / {
        root /home/ubuntu/bank-statement-converter;
        try_files \$uri \$uri/ /index.html;
    }

    # Backend API
    location /api {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
    }
}
EOF

sudo ln -s /etc/nginx/sites-available/app /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl restart nginx

# Create systemd service
sudo tee /etc/systemd/system/app.service << EOF
[Unit]
Description=Bank Statement Converter
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/bank-statement-converter
Environment="PATH=/home/ubuntu/bank-statement-converter/venv/bin"
ExecStart=/home/ubuntu/bank-statement-converter/venv/bin/gunicorn -w 2 -k uvicorn.workers.UvicornWorker backend.main:app --bind 127.0.0.1:8000

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl enable app
sudo systemctl start app

echo "Deployment complete! Access at http://your-lightsail-ip"