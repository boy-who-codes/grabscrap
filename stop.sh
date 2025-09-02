#!/bin/bash

# KABAADWALA™ Stop Script
echo "🛑 Stopping KABAADWALA™ Services..."

# Stop Django server
echo "🌐 Stopping Django server..."
pkill -f "manage.py runserver"

# Stop Celery worker
echo "⚙️  Stopping Celery worker..."
pkill -f "manage_celery.py worker"

# Stop Celery beat
echo "⏰ Stopping Celery beat..."
pkill -f "manage_celery.py beat"

# Stop Redis server
echo "📡 Stopping Redis server..."
pkill -f "redis-server"

# Wait for processes to stop
sleep 2

echo ""
echo "✅ All services stopped successfully!"
echo ""
