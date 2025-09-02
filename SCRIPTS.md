# 🚀 KABAADWALA™ Startup Scripts

## Available Scripts

### 🔧 **Development Scripts**

#### `./dev.sh`
**Best for development** - Runs all services with live logs
```bash
./dev.sh
```
- Starts Django development server
- Starts Celery worker & beat
- Starts Redis server
- Shows live Django logs
- Press `Ctrl+C` to stop all services

#### `./start.sh`
**Quick start** - Runs all services in background
```bash
./start.sh
```
- Starts all services as background processes
- Returns to terminal immediately
- Use `./stop.sh` to stop services

### 🏭 **Production Scripts**

#### `./prod.sh`
**Production deployment** - Optimized for production
```bash
./prod.sh
```
- Runs database migrations
- Collects static files
- Starts Gunicorn with 4 workers
- Starts Celery with 4 worker processes
- All services run as daemons
- Comprehensive logging

### 🛑 **Control Scripts**

#### `./stop.sh`
**Stop all services**
```bash
./stop.sh
```
- Stops Django/Gunicorn server
- Stops Celery worker & beat
- Stops Redis server

#### `./status.sh`
**Check service status**
```bash
./status.sh
```
- Shows status of all services
- Health check for web server & Redis
- Recent log entries

## 📋 **Quick Start Guide**

### For Development:
```bash
# Start development environment
./dev.sh

# In another terminal, check status
./status.sh

# Stop when done
# Press Ctrl+C in dev.sh terminal
```

### For Production:
```bash
# Start production services
./prod.sh

# Check status
./status.sh

# Stop services
./stop.sh
```

## 📝 **Log Files**

All logs are stored in `./logs/` directory:
- `django.log` - Django application logs
- `celery_worker.log` - Celery worker logs
- `celery_beat.log` - Celery scheduler logs
- `redis.log` - Redis server logs
- `access.log` - Gunicorn access logs (production)
- `error.log` - Gunicorn error logs (production)

## 🔍 **Troubleshooting**

### Services won't start:
```bash
# Check what's running
./status.sh

# Stop everything and restart
./stop.sh
./start.sh
```

### Port already in use:
```bash
# Kill processes using port 8000
sudo lsof -ti:8000 | xargs kill -9

# Restart services
./start.sh
```

### Redis connection issues:
```bash
# Check Redis status
redis-cli ping

# Restart Redis
sudo systemctl restart redis
# or
redis-server --port 6379
```

## ⚙️ **Service Ports**

- **Django/Gunicorn**: `8000`
- **Redis**: `6379`
- **Celery**: Background processes (no port)

## 🎯 **Recommended Usage**

- **Development**: Use `./dev.sh` for active development
- **Testing**: Use `./start.sh` for background testing
- **Production**: Use `./prod.sh` for deployment
- **Monitoring**: Use `./status.sh` regularly to check health
