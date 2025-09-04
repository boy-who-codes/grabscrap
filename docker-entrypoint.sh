#!/bin/bash
set -e

# Wait for database
echo "Waiting for database..."
while ! pg_isready -h $DB_HOST -p $DB_PORT -U $DB_USER; do
    sleep 1
done
echo "Database is ready!"

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
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@kabaadwala.com', 'admin123')
    print('Superuser created: admin/admin123')
else:
    print('Superuser already exists')
EOF

# Execute the main command
exec "$@"
