#!/bin/bash

# KABAADWALA™ Startup Script
echo "🚀 Starting KABAADWALA™ Services..."

# Activate virtual environment
source kabaadwala_env/bin/activate

# Kill existing processes
echo "🔄 Stopping existing services..."
pkill -f "manage.py runserver" 2>/dev/null
pkill -f "manage_celery.py worker" 2>/dev/null
pkill -f "manage_celery.py beat" 2>/dev/null
pkill -f "redis-server" 2>/dev/null

# Wait for processes to stop
sleep 2

# Start Redis server
echo "📡 Starting Redis server..."
redis-server --daemonize yes --port 6379

# Start Celery worker
echo "⚙️  Starting Celery worker..."
python manage_celery.py worker --loglevel=info --detach

# Start Celery beat scheduler
echo "⏰ Starting Celery beat scheduler..."
python manage_celery.py beat --loglevel=info --detach

# Start Django development server
echo "🌐 Starting Django server..."
python manage.py runserver 127.0.0.1:8000 &

# Wait for services to start
sleep 3

echo ""
echo "✅ All services started successfully!"
echo ""
echo "📊 Service Status:"
echo "   🌐 Django Server: http://127.0.0.1:8000"
echo "   📡 Redis Server: localhost:6379"
echo "   ⚙️  Celery Worker: Running"
echo "   ⏰ Celery Beat: Running"
echo ""
echo "📝 Logs:"
echo "   Django: Check terminal output"
echo "   Celery: Check celery_worker.log & celery_beat.log"
echo ""
echo "🛑 To stop all services, run: ./stop.sh"
echo ""
