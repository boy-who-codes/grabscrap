#!/usr/bin/env python
"""
Celery management script for KABAADWALA™
Usage:
    python manage_celery.py worker
    python manage_celery.py beat
    python manage_celery.py flower
    python manage_celery.py purge
"""
import os
import sys

if __name__ == '__main__':
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kabaadwala.settings')
    
    # Import Django and setup
    import django
    django.setup()
    
    from kabaadwala.celery import app
    
    if len(sys.argv) > 1:
        if sys.argv[1] == 'worker':
            # Start Celery worker
            app.worker_main(['worker', '--loglevel=info', '--concurrency=4'])
        elif sys.argv[1] == 'beat':
            # Start Celery beat scheduler
            app.control.purge()  # Clear any pending tasks
            os.system('celery -A kabaadwala beat --loglevel=info')
        elif sys.argv[1] == 'flower':
            # Start Flower monitoring
            os.system('celery -A kabaadwala flower --port=5555')
        elif sys.argv[1] == 'purge':
            # Purge all tasks
            app.control.purge()
            print("All tasks purged")
        else:
            print("Usage: python manage_celery.py [worker|beat|flower|purge]")
    else:
        print("Available commands:")
        print("  worker  - Start Celery worker")
        print("  beat    - Start Celery beat scheduler") 
        print("  flower  - Start Flower monitoring")
        print("  purge   - Purge all pending tasks")
