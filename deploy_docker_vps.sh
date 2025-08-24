#!/bin/bash
# Comprehensive Docker deployment script for Django project with Celery and Channels

# Exit on error
set -e

# Variables - customize these
PROJECT_NAME="kabaadwala"
DOMAIN_NAME="kabaadwala.com" # Replace with your actual domain
EMAIL="noreply@kabaadwala.com" # For Let's Encrypt

# Colors for output
GREEN="\033[0;32m"
YELLOW="\033[1;33m"
RED="\033[0;31m"
NC="\033[0m" # No Color

echo -e "${GREEN}Starting deployment of $PROJECT_NAME...${NC}"

# Update system
echo -e "${YELLOW}Updating system packages...${NC}"
sudo apt update && sudo apt upgrade -y

# Install Docker and Docker Compose if not installed
if ! command -v docker &> /dev/null; then
    echo -e "${YELLOW}Installing Docker...${NC}"
    sudo apt install -y apt-transport-https ca-certificates curl software-properties-common
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
    sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"
    sudo apt update
    sudo apt install -y docker-ce
    sudo systemctl enable docker
    sudo systemctl start docker
    sudo usermod -aG docker $USER
    echo -e "${GREEN}Docker installed successfully!${NC}"
fi

if ! command -v docker-compose &> /dev/null; then
    echo -e "${YELLOW}Installing Docker Compose...${NC}"
    sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.3/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
    echo -e "${GREEN}Docker Compose installed successfully!${NC}"
fi

# Install Nginx and Certbot for SSL
echo -e "${YELLOW}Installing Nginx and Certbot...${NC}"
sudo apt install -y nginx certbot python3-certbot-nginx

# Configure firewall
echo -e "${YELLOW}Configuring firewall...${NC}"
sudo ufw allow 'Nginx Full'
sudo ufw allow ssh
sudo ufw --force enable

# Create project directory
echo -e "${YELLOW}Setting up project directory...${NC}"
sudo mkdir -p /opt/$PROJECT_NAME
sudo chown -R $USER:$USER /opt/$PROJECT_NAME

# Clone or copy project files
echo -e "${YELLOW}Copying project files...${NC}"
# If using git:
# git clone https://github.com/yourusername/yourrepo.git /opt/$PROJECT_NAME
# Or copy local files:
rsync -av --exclude 'env' --exclude 'venv' --exclude '__pycache__' --exclude '*.pyc' ./ /opt/$PROJECT_NAME/

# Create .env file for production
echo -e "${YELLOW}Creating production .env file...${NC}"
cat > /opt/$PROJECT_NAME/.env << EOF
# Django settings
DEBUG=False
SECRET_KEY=$(openssl rand -hex 32)
ALLOWED_HOSTS=$DOMAIN_NAME,www.$DOMAIN_NAME

# Database settings
DATABASE_URL=postgres://postgres:postgres@db:5432/postgres

# Redis settings
REDIS_URL=redis://redis:6379/0
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0

# Email settings
EMAIL_HOST=$EMAIL_HOST
EMAIL_PORT=$EMAIL_PORT
EMAIL_HOST_USER=$EMAIL_HOST_USER
EMAIL_HOST_PASSWORD=$EMAIL_HOST_PASSWORD
EMAIL_USE_TLS=$EMAIL_USE_TLS
EMAIL_USE_SSL=$EMAIL_USE_SSL
DEFAULT_FROM_EMAIL=$DEFAULT_FROM_EMAIL
EMAIL_FROM_ADDRESS=$EMAIL_FROM_ADDRESS

# OTP Settings
OTP_LENGTH=6
OTP_EXPIRY_SECONDS=300

# Google Maps API Key
GOOGLE_MAPS_API_KEY=$GOOGLE_MAPS_API_KEY
EOF

# Update docker-compose.yml for production
echo -e "${YELLOW}Creating production docker-compose.yml...${NC}"
cat > /opt/$PROJECT_NAME/docker-compose.yml << EOF
version: '3.8'

services:
  web:
    build: .
    restart: always
    command: gunicorn --bind 0.0.0.0:8000 --workers 4 core.wsgi:application
    volumes:
      - .:/app
      - static_volume:/app/staticfiles
      - media_volume:/app/media
    expose:
      - 8000
    env_file:
      - .env
    depends_on:
      - db
      - redis

  db:
    image: postgres:13
    restart: always
    volumes:
      - postgres_data:/var/lib/postgresql/data/
    environment:
      - POSTGRES_PASSWORD=postgres
      - POSTGRES_USER=postgres
      - POSTGRES_DB=postgres

  redis:
    image: redis:6
    restart: always

  celery:
    build: .
    restart: always
    command: celery -A core worker -l info
    volumes:
      - .:/app
    env_file:
      - .env
    depends_on:
      - web
      - redis

  celery-beat:
    build: .
    restart: always
    command: celery -A core beat -l info
    volumes:
      - .:/app
    env_file:
      - .env
    depends_on:
      - web
      - redis

  daphne:
    build: .
    restart: always
    command: daphne -b 0.0.0.0 -p 8001 core.asgi:application
    volumes:
      - .:/app
      - static_volume:/app/staticfiles
      - media_volume:/app/media
    expose:
      - 8001
    env_file:
      - .env
    depends_on:
      - web
      - redis

  nginx:
    image: nginx:latest
    restart: always
    volumes:
      - ./nginx/conf.d:/etc/nginx/conf.d
      - static_volume:/app/staticfiles
      - media_volume:/app/media
      - ./nginx/certbot/conf:/etc/letsencrypt
      - ./nginx/certbot/www:/var/www/certbot
    ports:
      - 80:80
      - 443:443
    depends_on:
      - web
      - daphne

  certbot:
    image: certbot/certbot
    restart: unless-stopped
    volumes:
      - ./nginx/certbot/conf:/etc/letsencrypt
      - ./nginx/certbot/www:/var/www/certbot
    entrypoint: "/bin/sh -c 'trap exit TERM; while :; do certbot renew; sleep 12h & wait \$\${!}; done;'"

volumes:
  postgres_data:
  static_volume:
  media_volume:
EOF

# Create Nginx configuration
echo -e "${YELLOW}Creating Nginx configuration...${NC}"
sudo mkdir -p /opt/$PROJECT_NAME/nginx/conf.d
sudo mkdir -p /opt/$PROJECT_NAME/nginx/certbot/conf
sudo mkdir -p /opt/$PROJECT_NAME/nginx/certbot/www

cat > /opt/$PROJECT_NAME/nginx/conf.d/app.conf << EOF
server {
    listen 80;
    server_name $DOMAIN_NAME www.$DOMAIN_NAME;
    server_tokens off;

    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }

    location / {
        return 301 https://\$host\$request_uri;
    }
}

server {
    listen 443 ssl;
    server_name $DOMAIN_NAME www.$DOMAIN_NAME;
    server_tokens off;

    ssl_certificate /etc/letsencrypt/live/$DOMAIN_NAME/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/$DOMAIN_NAME/privkey.pem;
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;

    client_max_body_size 20M;

    location / {
        proxy_pass http://web:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    location /ws/ {
        proxy_pass http://daphne:8001;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    location /static/ {
        alias /app/staticfiles/;
    }

    location /media/ {
        alias /app/media/;
    }
}
EOF

# Start the containers
echo -e "${YELLOW}Starting Docker containers...${NC}"
cd /opt/$PROJECT_NAME
docker-compose up -d

# Initialize SSL certificates
echo -e "${YELLOW}Initializing SSL certificates...${NC}"
sudo certbot --nginx -d $DOMAIN_NAME -d www.$DOMAIN_NAME --email $EMAIL --agree-tos --no-eff-email

# Run migrations and collect static files
echo -e "${YELLOW}Running database migrations...${NC}"
docker-compose exec web python manage.py migrate

echo -e "${YELLOW}Collecting static files...${NC}"
docker-compose exec web python manage.py collectstatic --noinput

# Create superuser (optional)
echo -e "${YELLOW}Do you want to create a superuser? (y/n)${NC}"
read create_superuser
if [ "$create_superuser" = "y" ]; then
    docker-compose exec web python manage.py createsuperuser
fi

# Setup automatic renewal of SSL certificates
echo -e "${YELLOW}Setting up automatic SSL renewal...${NC}"
echo "0 12 * * * root /usr/bin/certbot renew --quiet" | sudo tee -a /etc/crontab > /dev/null

# Setup automatic backups (optional)
echo -e "${YELLOW}Setting up daily database backups...${NC}"
cat > /opt/$PROJECT_NAME/backup.sh << EOF
#!/bin/bash
BACKUP_DIR="/opt/$PROJECT_NAME/backups"
DATETIME=\$(date +%Y%m%d_%H%M%S)
mkdir -p \$BACKUP_DIR

# Backup database
docker-compose exec -T db pg_dump -U postgres postgres > \$BACKUP_DIR/db_\$DATETIME.sql

# Backup media files (optional)
tar -czf \$BACKUP_DIR/media_\$DATETIME.tar.gz -C /opt/$PROJECT_NAME/media .

# Remove backups older than 7 days
find \$BACKUP_DIR -type f -name "*.sql" -mtime +7 -delete
find \$BACKUP_DIR -type f -name "*.tar.gz" -mtime +7 -delete
EOF

chmod +x /opt/$PROJECT_NAME/backup.sh
echo "0 2 * * * root /opt/$PROJECT_NAME/backup.sh" | sudo tee -a /etc/crontab > /dev/null

echo -e "${GREEN}Deployment completed successfully!${NC}"
echo -e "${GREEN}Your application is now running at https://$DOMAIN_NAME${NC}"

# Print useful commands
echo -e "${YELLOW}Useful commands:${NC}"
echo -e "  - View logs: ${GREEN}cd /opt/$PROJECT_NAME && docker-compose logs -f${NC}"
echo -e "  - Restart services: ${GREEN}cd /opt/$PROJECT_NAME && docker-compose restart${NC}"
echo -e "  - Update deployment: ${GREEN}cd /opt/$PROJECT_NAME && docker-compose down && git pull && docker-compose up -d --build${NC}"