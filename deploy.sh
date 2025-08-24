#!/bin/bash

# Stop any existing containers
docker-compose down

# Pull latest code
git pull origin main

# Build and start containers
docker-compose up -d --build

# Run database migrations
docker-compose exec web python manage.py migrate

# Collect static files
docker-compose exec web python manage.py collectstatic --noinput

# Restart Celery services
docker-compose restart celery celery-beat