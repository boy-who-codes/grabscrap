#!/bin/bash
# Production deployment script for Kabaadwala Django project

# Update system
sudo apt update && sudo apt upgrade -y

# Install dependencies
sudo apt install -y nginx python3-pip python3-venv libpq-dev

# Create system user
sudo useradd --system --no-create-home kabaadwala

# Configure firewall
sudo ufw allow 'Nginx Full'
sudo ufw enable

# Setup project dir
sudo mkdir -p /opt/kabaadwala
sudo chown -R kabaadwala:kabaadwala /opt/kabaadwala
sudo chmod -R 775 /opt/kabaadwala

# Python environment
python3 -m venv /opt/kabaadwala/venv
source /opt/kabaadwala/venv/bin/activate
pip install -r requirements.txt gunicorn daphne

# Database setup (PostgreSQL example)
sudo -u postgres psql -c "CREATE DATABASE kabaadwala_prod;"
sudo -u postgres psql -c "CREATE USER kabaadwala WITH PASSWORD '${DB_PASS}';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE kabaadwala_prod TO kabaadwala;"

# Migrations and static files
python manage.py migrate
python manage.py collectstatic --noinput

# Configure Gunicorn+Daphne
cat << EOF | sudo tee /etc/systemd/system/kabaadwala.service
[Unit]
Description=Kabaadwala Production Server
After=network.target

[Service]
User=kabaadwala
Group=kabaadwala
WorkingDirectory=/opt/kabaadwala
EnvironmentFile=/opt/kabaadwala/.env
ExecStart=/opt/kabaadwala/venv/bin/daphne -b 0.0.0.0 -p 8000 core.asgi:application
ExecStartPost=/opt/kabaadwala/venv/bin/gunicorn --access-logfile - --workers 3 --bind unix:/opt/kabaadwala/kabaadwala.sock core.wsgi:application

[Install]
WantedBy=multi-user.target
EOF

# Configure Nginx
cat << EOF | sudo tee /etc/nginx/sites-available/kabaadwala
server {
    listen 80;
    server_name _;

    location / {
        proxy_pass http://unix:/opt/kabaadwala/kabaadwala.sock;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    location /ws/ {
        proxy_pass http://0.0.0.0:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    location /static/ {
        alias /opt/kabaadwala/staticfiles/;
    }

    location /media/ {
        alias /opt/kabaadwala/media/;
    }
}
EOF

# Enable and restart services
sudo ln -s /etc/nginx/sites-available/kabaadwala /etc/nginx/sites-enabled/
sudo systemctl daemon-reload
sudo systemctl restart nginx kabaadwala