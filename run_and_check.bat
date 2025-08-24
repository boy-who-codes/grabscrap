@echo off
REM Script to run the application and check for errors on Windows

echo Starting application check...

REM Check if Docker is running
docker info > nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Error: Docker is not running. Please start Docker and try again.
    exit /b 1
)

REM Stop any existing containers
echo Stopping any existing containers...
docker-compose down

REM Build and start containers
echo Building and starting containers...
docker-compose up -d --build

REM Wait for services to start
echo Waiting for services to start...
timeout /t 10 /nobreak > nul

REM Check if containers are running
echo Checking container status...
for /f %%i in ('docker-compose ps -q ^| find /c /v ""') do set CONTAINER_COUNT=%%i
if %CONTAINER_COUNT% LSS 4 (
    echo Error: Not all containers are running. Check logs for details.
    docker-compose logs
    exit /b 1
)

REM Check Django for errors
echo Checking Django for errors...
docker-compose exec web python manage.py check
if %ERRORLEVEL% NEQ 0 (
    echo Error: Django check failed.
    exit /b 1
)

REM Run migrations
echo Running migrations...
docker-compose exec web python manage.py migrate
if %ERRORLEVEL% NEQ 0 (
    echo Error: Database migrations failed.
    exit /b 1
)

REM Collect static files
echo Collecting static files...
docker-compose exec web python manage.py collectstatic --noinput
if %ERRORLEVEL% NEQ 0 (
    echo Error: Static file collection failed.
    exit /b 1
)

REM Check Celery
echo Checking Celery status...
docker-compose exec celery celery -A core inspect ping
if %ERRORLEVEL% NEQ 0 (
    echo Warning: Celery workers may not be running properly.
)

REM Check Redis
echo Checking Redis connection...
docker-compose exec redis redis-cli ping
if %ERRORLEVEL% NEQ 0 (
    echo Error: Redis is not responding.
    exit /b 1
)

REM Check if the web application is accessible
echo Checking web application accessibility...
timeout /t 5 /nobreak > nul
curl -s http://localhost:8000 > nul
if %ERRORLEVEL% NEQ 0 (
    echo Error: Web application is not accessible.
    docker-compose logs web
    exit /b 1
)

REM All checks passed
echo All checks passed! The application is running correctly.

REM Print application URLs
echo Application URLs:
echo   - Web: http://localhost:8000

REM Print useful commands
echo Useful commands:
echo   - View logs: docker-compose logs -f
echo   - Stop application: docker-compose down
echo   - Restart services: docker-compose restart

REM Keep containers running
echo Containers are running in the background.
echo Use 'docker-compose down' to stop them when you're done.