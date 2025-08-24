# Deployment Guide

This document provides instructions for deploying the application in both development and production environments using Docker.

## Prerequisites

- Docker and Docker Compose installed
- Git installed (for production deployment)
- A VPS or server with SSH access (for production deployment)
- Domain name configured to point to your server (for production deployment)

## Local Development Deployment

### Using Windows

1. Make sure Docker Desktop is running
2. Open a command prompt in the project directory
3. Run the check script:

```bash
run_and_check.bat
```

This script will:
- Stop any existing containers
- Build and start all required containers
- Run database migrations
- Collect static files
- Check if all services are running correctly

### Using Linux/Mac

1. Make sure Docker is running
2. Open a terminal in the project directory
3. Make the script executable and run it:

```bash
chmod +x run_and_check.sh
./run_and_check.sh
```

## Production Deployment on VPS

### Initial Setup

1. SSH into your VPS
2. Clone the repository or upload your project files
3. Navigate to the project directory
4. Make the deployment script executable:

```bash
chmod +x deploy_docker_vps.sh
```

5. Edit the script to set your domain name and email address:

```bash
vim deploy_docker_vps.sh
# Update these variables:
# DOMAIN_NAME="yourdomain.com"
# EMAIL="your@email.com"
```

6. Run the deployment script:

```bash
./deploy_docker_vps.sh
```

This script will:
- Install Docker and Docker Compose if not already installed
- Install Nginx and Certbot for SSL
- Configure the firewall
- Set up the project directory
- Create production configuration files
- Start all Docker containers
- Set up SSL certificates with Let's Encrypt
- Run database migrations
- Collect static files
- Set up automatic backups

### Updating the Application

To update the application after making changes:

```bash
cd /opt/kabaadwala
git pull  # If using git
docker-compose down
docker-compose up -d --build
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py collectstatic --noinput
```

Or simply use the provided script:

```bash
./deploy.sh
```

## Docker Compose Services

The application consists of the following services:

- **web**: Django application served with Gunicorn
- **db**: PostgreSQL database
- **redis**: Redis for caching and as message broker
- **celery**: Celery worker for background tasks
- **celery-beat**: Celery beat for scheduled tasks
- **daphne**: Daphne server for WebSocket support
- **nginx**: Nginx web server (production only)
- **certbot**: Let's Encrypt certificate manager (production only)

## Troubleshooting

### Viewing Logs

To view logs for all services:

```bash
docker-compose logs -f
```

To view logs for a specific service:

```bash
docker-compose logs -f web  # Replace 'web' with the service name
```

### Common Issues

1. **Database connection errors**:
   - Check if the database container is running
   - Verify database credentials in .env file

2. **Static files not loading**:
   - Run `docker-compose exec web python manage.py collectstatic --noinput`
   - Check Nginx configuration for static file paths

3. **WebSocket connection issues**:
   - Verify Daphne is running: `docker-compose ps daphne`
   - Check Nginx configuration for WebSocket proxy settings

4. **Celery tasks not running**:
   - Check Celery logs: `docker-compose logs celery`
   - Verify Redis connection in .env file

## Backup and Restore

### Manual Backup

```bash
# Backup database
docker-compose exec db pg_dump -U postgres postgres > backup_$(date +%Y%m%d).sql

# Backup media files
tar -czf media_backup_$(date +%Y%m%d).tar.gz -C /opt/kabaadwala/media .
```

### Restore from Backup

```bash
# Restore database
cat backup_20230101.sql | docker-compose exec -T db psql -U postgres postgres

# Restore media files
tar -xzf media_backup_20230101.tar.gz -C /opt/kabaadwala/media
```

## Security Considerations

1. Always keep Docker, Nginx, and all system packages updated
2. Use strong passwords for database and admin accounts
3. Regularly backup your data
4. Monitor logs for suspicious activity
5. Consider implementing rate limiting for API endpoints
6. Use a firewall to restrict access to only necessary ports