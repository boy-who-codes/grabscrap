
============================
KABAADWALA™ Project Command Reference
============================

# 1. Environment Setup
python -m venv env                # Create virtual environment
./env/Scripts/activate            # Activate virtualenv (Windows)
pip install -r requirements.txt   # Install dependencies

# 2. Database
python manage.py makemigrations   # Create new migrations
python manage.py migrate          # Apply migrations
python manage.py createsuperuser  # Create admin user

# 3. Running the Project
python manage.py runserver        # Start Django dev server
celery -A core worker --loglevel=info   # Start Celery worker
wsl redis-server                  # Start Redis server (in WSL)

# 4. All-in-One (Windows Only)
start_services.bat                # Starts Django, Celery, and Redis in separate windows

# 5. Other Useful Commands
python manage.py shell            # Open Django shell
python manage.py collectstatic    # Collect static files

# 6. Environment Variables (.env)
DEBUG=True
EMAIL_HOST=smtp.example.com
EMAIL_PORT=587
EMAIL_HOST_USER=your_smtp_user
EMAIL_HOST_PASSWORD=your_smtp_password
EMAIL_USE_TLS=True
DEFAULT_FROM_EMAIL=noreply@kabaadwala.com

# 7. Celery/Redis Troubleshooting
celery -A core worker --loglevel=debug   # Verbose Celery logs
wsl redis-cli                            # Redis CLI (in WSL)

# 8. Requirements
pip freeze > requirements.txt            # Update requirements.txt 