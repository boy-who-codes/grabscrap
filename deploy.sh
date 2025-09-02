#!/bin/bash

# KABAADWALA™ Docker Deployment Script
echo "🚀 Starting KABAADWALA™ deployment..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    print_error "Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Stop existing containers
print_status "Stopping existing containers..."
docker-compose down

# Copy environment file
if [ ! -f .env ]; then
    if [ -f .env.dev ]; then
        print_status "Using existing .env.dev file..."
        cp .env.dev .env
    else
        print_error ".env file not found. Please create .env file first."
        exit 1
    fi
else
    print_status "Using existing .env file..."
fi

# Build and start services
print_status "Building Docker images..."
docker-compose build

print_status "Starting services..."
docker-compose up -d

# Wait for services to be ready
print_status "Waiting for services to start..."
sleep 30

# Check service status
print_status "Checking service status..."
docker-compose ps

# Show logs
print_status "Showing recent logs..."
docker-compose logs --tail=50

echo ""
print_status "🎉 KABAADWALA™ deployment completed!"
echo ""
echo -e "${BLUE}Access your application:${NC}"
echo "🌐 Web Application: http://localhost:8000"
echo "👨‍💼 Admin Panel: http://localhost:8000/admin"
echo "🌸 Flower (Celery Monitor): http://localhost:5555"
echo ""
echo -e "${BLUE}Default Admin Credentials:${NC}"
echo "Username: admin"
echo "Password: admin123"
echo ""
echo -e "${BLUE}Useful Commands:${NC}"
echo "📊 View logs: docker-compose logs -f"
echo "🔄 Restart: docker-compose restart"
echo "🛑 Stop: docker-compose down"
echo "🗑️  Clean up: docker-compose down -v"
echo ""
print_warning "Remember to update your .env file with production settings!"
