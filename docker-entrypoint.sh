#!/bin/bash
set -e

# Wait for Redis
echo "Waiting for Redis..."
while ! redis-cli -h $REDIS_HOST -p $REDIS_PORT ping; do
    sleep 1
done
echo "Redis is ready!"

# Run migrations
echo "Running migrations..."
python manage.py migrate

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Setup defaults
echo "Setting up defaults..."
python manage.py setup_defaults

# Create superuser if it doesn't exist
echo "Creating superuser..."
python manage.py shell << EOF
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(email='no-reply@kabaadwala.com').exists():
    User.objects.create_superuser(
        username='admin',
        email='no-reply@kabaadwala.com', 
        password='admin@kwala',
        full_name='Admin User',
        is_verified=True
    )
    print('Superuser created: no-reply@kabaadwala.com / admin@kwala')
else:
    print('Superuser already exists')
EOF

# Execute the main command
exec "$@"
