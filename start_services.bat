@echo off
REM Activate virtualenv and start Django runserver
start "Django Runserver" cmd /k ".\env\Scripts\activate && python manage.py runserver"

REM Activate virtualenv and start Celery worker
start "Celery Worker" cmd /k ".\env\Scripts\activate && celery -A core worker --loglevel=info"

REM Start Redis server in WSL
start "Redis (WSL)" wsl redis-server 