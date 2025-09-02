#!/bin/bash

echo "🚀 KABAADWALA™ Docker Deployment Script"
echo "========================================"

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Stop existing containers
echo "🛑 Stopping existing containers..."
docker-compose down

# Build and start containers
echo "🔨 Building Docker image..."
docker-compose build

echo "🚀 Starting containers..."
docker-compose up -d

# Wait for container to be ready
echo "⏳ Waiting for application to start..."
sleep 10

# Check if container is running
if docker-compose ps | grep -q "Up"; then
    echo "✅ Deployment successful!"
    echo ""
    echo "🌐 Application is running at: http://localhost:8000"
    echo "👤 Admin login: admin@admin.com / admin123"
    echo ""
    echo "📋 Useful commands:"
    echo "   View logs: docker-compose logs -f"
    echo "   Stop app:  docker-compose down"
    echo "   Restart:   docker-compose restart"
    echo ""
else
    echo "❌ Deployment failed. Check logs with: docker-compose logs"
    exit 1
fi
