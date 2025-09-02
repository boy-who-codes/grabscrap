#!/bin/bash

# KABAADWALA™ Production Deployment Script
echo "🚀 Starting KABAADWALA™ production deployment..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    print_error "Please run as root (use sudo)"
    exit 1
fi

# Update system
print_status "Updating system packages..."
apt-get update && apt-get upgrade -y

# Install Docker if not present
if ! command -v docker &> /dev/null; then
    print_status "Installing Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    systemctl enable docker
    systemctl start docker
    rm get-docker.sh
fi

# Install Docker Compose if not present
if ! command -v docker-compose &> /dev/null; then
    print_status "Installing Docker Compose..."
    curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
fi

# Install Nginx
if ! command -v nginx &> /dev/null; then
    print_status "Installing Nginx..."
    apt-get install -y nginx
    systemctl enable nginx
fi

# Use existing .env file or create from .env.dev
print_status "Setting up environment file..."
if [ -f .env ]; then
    print_status "Using existing .env file..."
    # Add Docker-specific overrides
    cat >> .env << EOF

# Docker overrides
DB_HOST=db
DB_PORT=5432
DB_NAME=kabaadwala_db
DB_USER=kabaadwala_user
DB_PASSWORD=$(openssl rand -base64 16)
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_URL=redis://redis:6379/2
DEBUG=False
EOF
elif [ -f .env.dev ]; then
    print_status "Using .env.dev as base..."
    cp .env.dev .env
    # Add Docker-specific overrides
    cat >> .env << EOF

# Docker overrides
DB_HOST=db
DB_PORT=5432
DB_NAME=kabaadwala_db
DB_USER=kabaadwala_user
DB_PASSWORD=$(openssl rand -base64 16)
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_URL=redis://redis:6379/2
DEBUG=False
EOF
else
    print_error ".env or .env.dev file not found. Please create one first."
    exit 1
fi

# Create production docker-compose
cat > docker-compose.prod.yml << EOF
version: '3.8'

services:
  db:
    image: postgres:15
    environment:
      POSTGRES_DB: kabaadwala_db
      POSTGRES_USER: kabaadwala_user
      POSTGRES_PASSWORD: \${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U kabaadwala_user -d kabaadwala_db"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  web:
    build: .
    command: gunicorn kabaadwala.wsgi:application --bind 0.0.0.0:8000 --workers 3
    volumes:
      - media_files:/app/media
      - static_files:/app/static
    ports:
      - "8000:8000"
    env_file:
      - .env
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
    restart: unless-stopped

  celery:
    build: .
    command: python manage_celery.py worker --loglevel=info
    volumes:
      - media_files:/app/media
    env_file:
      - .env
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
    restart: unless-stopped

  celery-beat:
    build: .
    command: python manage_celery.py beat --loglevel=info
    env_file:
      - .env
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
    restart: unless-stopped

  flower:
    build: .
    command: python manage_celery.py flower --port=5555
    ports:
      - "5555:5555"
    env_file:
      - .env
    depends_on:
      - redis
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:
  media_files:
  static_files:
EOF

# Create Nginx configuration
print_status "Creating Nginx configuration..."
cat > /etc/nginx/sites-available/kabaadwala << EOF
server {
    listen 80;
    server_name your-domain.com www.your-domain.com;

    client_max_body_size 100M;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    location /static/ {
        alias /var/www/kabaadwala/static/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    location /media/ {
        alias /var/www/kabaadwala/media/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    location /flower/ {
        proxy_pass http://localhost:5555/;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF

# Enable Nginx site
ln -sf /etc/nginx/sites-available/kabaadwala /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# Test Nginx configuration
nginx -t

# Create directories for static and media files
mkdir -p /var/www/kabaadwala/static
mkdir -p /var/www/kabaadwala/media

# Install gunicorn
pip3 install gunicorn

# Add gunicorn to requirements
echo "gunicorn==21.2.0" >> requirements.txt

# Build and start services
print_status "Building and starting services..."
docker-compose -f docker-compose.prod.yml build
docker-compose -f docker-compose.prod.yml up -d

# Wait for services
sleep 30

# Copy static files
print_status "Copying static files..."
docker-compose -f docker-compose.prod.yml exec web python manage.py collectstatic --noinput
docker cp $(docker-compose -f docker-compose.prod.yml ps -q web):/app/static/. /var/www/kabaadwala/static/

# Set permissions
chown -R www-data:www-data /var/www/kabaadwala/
chmod -R 755 /var/www/kabaadwala/

# Restart Nginx
systemctl restart nginx

# Setup firewall
print_status "Configuring firewall..."
ufw allow 22
ufw allow 80
ufw allow 443
ufw --force enable

# Create systemd service for auto-start
cat > /etc/systemd/system/kabaadwala.service << EOF
[Unit]
Description=KABAADWALA Docker Compose Application
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=$(pwd)
ExecStart=/usr/local/bin/docker-compose -f docker-compose.prod.yml up -d
ExecStop=/usr/local/bin/docker-compose -f docker-compose.prod.yml down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
EOF

systemctl enable kabaadwala.service

print_status "🎉 Production deployment completed!"
echo ""
echo -e "${BLUE}Your KABAADWALA™ application is now running!${NC}"
echo ""
echo -e "${BLUE}Next Steps:${NC}"
echo "1. Update your domain in /etc/nginx/sites-available/kabaadwala"
echo "2. Update .env file with your production settings"
echo "3. Setup SSL certificate (recommended: certbot)"
echo "4. Configure your email SMTP settings"
echo "5. Update Razorpay keys for live payments"
echo ""
echo -e "${BLUE}Access URLs:${NC}"
echo "🌐 Web: http://your-server-ip"
echo "👨‍💼 Admin: http://your-server-ip/admin"
echo "🌸 Flower: http://your-server-ip/flower"
echo ""
print_warning "Remember to update your domain and production settings!"
