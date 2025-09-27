#!/bin/bash

# YouTube AI Assistant Deployment Script
# For Ubuntu/Debian servers

echo "🚀 Deploying YouTube AI Assistant..."

# Update system
sudo apt update && sudo apt upgrade -y

# Install Python 3.11 and dependencies
sudo apt install -y python3.11 python3.11-pip python3.11-venv nginx git curl

# Clone repository (if not already done)
# git clone https://github.com/P-Saroha/Agent-For-YT-Video.git
# cd Agent-For-YT-Video

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
cd server
pip install -r requirements.txt

# Create systemd service
sudo tee /etc/systemd/system/youtube-ai.service > /dev/null <<EOF
[Unit]
Description=YouTube AI Assistant
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$(pwd)
Environment=PATH=$(pwd)/../venv/bin
ExecStart=$(pwd)/../venv/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable youtube-ai
sudo systemctl start youtube-ai

# Configure Nginx
sudo tee /etc/nginx/sites-available/youtube-ai > /dev/null <<EOF
server {
    listen 80;
    server_name your-domain.com;  # Replace with your domain

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF

# Enable Nginx site
sudo ln -s /etc/nginx/sites-available/youtube-ai /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx

echo "✅ Deployment complete!"
echo "🌐 Your API is running at: http://your-server-ip:8000"
echo "📊 Check status: sudo systemctl status youtube-ai"
echo "📋 View logs: sudo journalctl -u youtube-ai -f"