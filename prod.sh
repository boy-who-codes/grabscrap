#!/bin/bash

# KABAADWALA™ Production Script
echo "🚀 Starting KABAADWALA™ Production Services..."

# Activate virtual environment
source kabaadwala_env/bin/activate

# Create logs directory
mkdir -p logs

# Stop existing services
./stop.sh 2>/dev/null

# Run migrations
echo "🔄 Running database migrations..."
python manage.py migrate

# Collect static files
echo "📁 Collecting static files..."
python manage.py collectstatic --noinput

# Start Redis
echo "📡 Starting Redis server..."
redis-server --daemonize yes --port 6379 --logfile logs/redis.log

# Start Celery worker with multiple processes
echo "⚙️  Starting Celery workers..."
python manage_celery.py worker --loglevel=info --concurrency=4 --detach --logfile=logs/celery_worker.log

# Start Celery beat
echo "⏰ Starting Celery beat scheduler..."
python manage_celery.py beat --loglevel=info --detach --logfile=logs/celery_beat.log

# Start Gunicorn server (production WSGI server)
echo "🌐 Starting Gunicorn server..."
gunicorn kabaadwala.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers 4 \
    --worker-class gevent \
    --worker-connections 1000 \
    --max-requests 1000 \
    --max-requests-jitter 100 \
    --timeout 30 \
    --keep-alive 2 \
    --access-logfile logs/access.log \
    --error-logfile logs/error.log \
    --log-level info \
    --daemon

echo ""
echo "✅ Production services started!"
echo ""
echo "📊 Service Status:"
echo "   🌐 Gunicorn Server: http://0.0.0.0:8000"
echo "   📡 Redis Server: localhost:6379"
echo "   ⚙️  Celery Workers: 4 processes"
echo "   ⏰ Celery Beat: Running"
echo ""
echo "📝 Logs Location: ./logs/"
echo "🛑 To stop: ./stop.sh"
echo ""
