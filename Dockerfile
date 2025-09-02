FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Create directories for media and static files
RUN mkdir -p media static

# Use Docker settings
ENV DJANGO_SETTINGS_MODULE=settings_docker

# Collect static files
RUN python manage.py collectstatic --noinput

# Create superuser script
RUN echo '#!/bin/bash\necho "from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.create_superuser(\"admin\", \"admin@admin.com\", \"admin123\") if not User.objects.filter(username=\"admin\").exists() else None" | python manage.py shell' > create_superuser.sh
RUN chmod +x create_superuser.sh

EXPOSE 8000

CMD ["sh", "-c", "python manage.py migrate && ./create_superuser.sh && python manage.py runserver 0.0.0.0:8000"]
