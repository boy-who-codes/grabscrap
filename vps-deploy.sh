#!/bin/bash

echo "🚀 KABAADWALA™ VPS Deployment Script"
echo "===================================="

# Update system
echo "📦 Updating system packages..."
sudo apt-get update -y

# Install Docker if not present
if ! command -v docker &> /dev/null; then
    echo "🐳 Installing Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
    rm get-docker.sh
fi

# Install Docker Compose if not present
if ! command -v docker-compose &> /dev/null; then
    echo "🔧 Installing Docker Compose..."
    sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
fi

# Create app directory
APP_DIR="/opt/kabaadwala"
echo "📁 Creating application directory: $APP_DIR"
sudo mkdir -p $APP_DIR
sudo chown $USER:$USER $APP_DIR

# Copy files to VPS directory
echo "📋 Copying application files..."
cp -r . $APP_DIR/
cd $APP_DIR

# Set permissions
chmod +x deploy.sh

# Run deployment
echo "🚀 Starting deployment..."
./deploy.sh

echo ""
echo "✅ VPS Deployment Complete!"
echo "🌐 Your app should be running at: http://$(curl -s ifconfig.me):8000"
echo "👤 Admin login: admin@admin.com / admin123"
