#!/bin/bash

# KABAADWALA™ Status Monitoring Script
echo "📊 KABAADWALA™ Service Status"
echo "=" * 50

# Check Django server
if pgrep -f "manage.py runserver" > /dev/null; then
    echo "🌐 Django Server: ✅ Running"
else
    echo "🌐 Django Server: ❌ Stopped"
fi

# Check Gunicorn server
if pgrep -f "gunicorn" > /dev/null; then
    echo "🌐 Gunicorn Server: ✅ Running"
else
    echo "🌐 Gunicorn Server: ❌ Stopped"
fi

# Check Redis server
if pgrep -f "redis-server" > /dev/null; then
    echo "📡 Redis Server: ✅ Running"
else
    echo "📡 Redis Server: ❌ Stopped"
fi

# Check Celery worker
if pgrep -f "manage_celery.py worker" > /dev/null; then
    worker_count=$(pgrep -f "manage_celery.py worker" | wc -l)
    echo "⚙️  Celery Worker: ✅ Running ($worker_count processes)"
else
    echo "⚙️  Celery Worker: ❌ Stopped"
fi

# Check Celery beat
if pgrep -f "manage_celery.py beat" > /dev/null; then
    echo "⏰ Celery Beat: ✅ Running"
else
    echo "⏰ Celery Beat: ❌ Stopped"
fi

echo ""

# Check if services are accessible
echo "🔍 Service Health Check:"

# Test Django/Gunicorn
if curl -s http://127.0.0.1:8000/ > /dev/null 2>&1; then
    echo "🌐 Web Server: ✅ Accessible"
else
    echo "🌐 Web Server: ❌ Not accessible"
fi

# Test Redis
if redis-cli ping > /dev/null 2>&1; then
    echo "📡 Redis: ✅ Responding"
else
    echo "📡 Redis: ❌ Not responding"
fi

echo ""
echo "📝 Recent Logs:"
if [ -f "logs/django.log" ]; then
    echo "   Django: $(tail -1 logs/django.log 2>/dev/null || echo 'No recent logs')"
fi
if [ -f "logs/celery_worker.log" ]; then
    echo "   Celery: $(tail -1 logs/celery_worker.log 2>/dev/null || echo 'No recent logs')"
fi

echo ""
