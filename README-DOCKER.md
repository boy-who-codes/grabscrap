# KABAADWALA™ Docker Deployment

Complete Docker setup for KABAADWALA™ hyperlocal scrap marketplace.

## 🚀 Quick Start (Development)

```bash
# Clone and navigate to project
cd Kwala_backend

# Run deployment script
./deploy.sh
```

**That's it!** Your application will be running at:
- 🌐 **Web App**: http://localhost:8000
- 👨‍💼 **Admin**: http://localhost:8000/admin (admin/admin123)
- 🌸 **Flower**: http://localhost:5555

## 🏭 Production Deployment

```bash
# On your server (run as root)
sudo ./production-deploy.sh
```

This will:
- Install Docker & Docker Compose
- Setup Nginx reverse proxy
- Configure SSL-ready setup
- Create systemd service for auto-start
- Setup firewall rules

## 📁 Docker Files Overview

- **`Dockerfile`** - Main application container
- **`docker-compose.yml`** - Development setup
- **`docker-entrypoint.sh`** - Container startup script
- **`.env.docker`** - Environment template
- **`deploy.sh`** - Development deployment
- **`production-deploy.sh`** - Production deployment

## 🔧 Services Included

| Service | Port | Description |
|---------|------|-------------|
| **web** | 8000 | Django application |
| **db** | 5432 | PostgreSQL database |
| **redis** | 6379 | Redis cache & message broker |
| **celery** | - | Background task worker |
| **celery-beat** | - | Task scheduler |
| **flower** | 5555 | Celery monitoring |

## 🛠️ Useful Commands

```bash
# View logs
docker-compose logs -f

# Restart services
docker-compose restart

# Stop all services
docker-compose down

# Clean up (removes data)
docker-compose down -v

# Access Django shell
docker-compose exec web python manage.py shell

# Run migrations
docker-compose exec web python manage.py migrate

# Create superuser
docker-compose exec web python manage.py createsuperuser
```

## 🔐 Environment Configuration

Update `.env` file with your settings:

```env
# Production Settings
DEBUG=False
SECRET_KEY=your-secret-key
ALLOWED_HOSTS=your-domain.com

# Email Configuration
EMAIL_HOST=smtp.gmail.com
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

# Razorpay Configuration
RAZORPAY_KEY_ID=rzp_live_your_key
RAZORPAY_KEY_SECRET=rzp_live_your_secret
```

## 🌐 Production Setup

1. **Update Domain**:
   ```bash
   sudo nano /etc/nginx/sites-available/kabaadwala
   # Change server_name to your domain
   ```

2. **SSL Certificate** (recommended):
   ```bash
   sudo apt install certbot python3-certbot-nginx
   sudo certbot --nginx -d your-domain.com
   ```

3. **Restart Services**:
   ```bash
   sudo systemctl restart nginx
   docker-compose -f docker-compose.prod.yml restart
   ```

## 📊 Monitoring

- **Application Logs**: `docker-compose logs -f web`
- **Celery Tasks**: http://your-domain.com/flower
- **System Status**: `docker-compose ps`
- **Resource Usage**: `docker stats`

## 🔄 Updates & Maintenance

```bash
# Pull latest code
git pull

# Rebuild and restart
docker-compose build
docker-compose up -d

# Run migrations if needed
docker-compose exec web python manage.py migrate
```

## 🆘 Troubleshooting

**Services won't start?**
```bash
docker-compose logs
```

**Database connection issues?**
```bash
docker-compose exec db psql -U kabaadwala_user -d kabaadwala_db
```

**Redis connection issues?**
```bash
docker-compose exec redis redis-cli ping
```

**Permission issues?**
```bash
sudo chown -R $USER:$USER .
```

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐
│     Nginx       │    │    Docker       │
│  (Reverse Proxy)│────│   Containers    │
└─────────────────┘    └─────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
   ┌────▼────┐         ┌─────▼─────┐         ┌─────▼─────┐
   │   Web   │         │    DB     │         │   Redis   │
   │ Django  │         │PostgreSQL │         │   Cache   │
   └─────────┘         └───────────┘         └───────────┘
        │
   ┌────▼────┐
   │ Celery  │
   │Workers  │
   └─────────┘
```

## 📝 Notes

- All data is persisted in Docker volumes
- Media files are handled via Docker volumes
- Static files are served by Nginx in production
- Automatic database migrations on startup
- Health checks ensure services are ready
- Auto-restart on failure (production)

## 🎯 Features Included

✅ **Complete Django Setup**
✅ **PostgreSQL Database**
✅ **Redis Cache & Message Broker**
✅ **Celery Background Tasks**
✅ **WebSocket Support (Channels)**
✅ **Email System**
✅ **File Upload Handling**
✅ **Admin Interface**
✅ **API Endpoints**
✅ **Production-Ready Nginx Config**
✅ **SSL Certificate Support**
✅ **Auto-Start on Boot**
✅ **Health Checks**
✅ **Monitoring (Flower)**

Your KABAADWALA™ application is now fully containerized and ready for deployment! 🎉
