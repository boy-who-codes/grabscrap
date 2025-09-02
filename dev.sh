#!/bin/bash

# KABAADWALA™ Development Script with Monitoring
echo "🚀 Starting KABAADWALA™ Development Environment..."

# Activate virtual environment
source kabaadwala_env/bin/activate

# Kill existing processes
pkill -f "manage.py runserver" 2>/dev/null
pkill -f "manage_celery.py" 2>/dev/null
pkill -f "redis-server" 2>/dev/null
sleep 2

# Create logs directory
mkdir -p logs

# Start Redis
echo "📡 Starting Redis..."
redis-server --daemonize yes --port 6379 --logfile logs/redis.log

# Start Celery worker
echo "⚙️  Starting Celery worker..."
python manage_celery.py worker --loglevel=info > logs/celery_worker.log 2>&1 &

# Start Celery beat
echo "⏰ Starting Celery beat..."
python manage_celery.py beat --loglevel=info > logs/celery_beat.log 2>&1 &

# Start Django server
echo "🌐 Starting Django server..."
python manage.py runserver 127.0.0.1:8000

# This will keep the script running and show Django logs
# Press Ctrl+C to stop all services
