#!/bin/bash
# Script to run the application and check for errors

# Colors for output
GREEN="\033[0;32m"
YELLOW="\033[1;33m"
RED="\033[0;31m"
NC="\033[0m" # No Color

echo -e "${YELLOW}Starting application check...${NC}"

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}Error: Docker is not running. Please start Docker and try again.${NC}"
    exit 1
fi

# Stop any existing containers
echo -e "${YELLOW}Stopping any existing containers...${NC}"
docker-compose down

# Build and start containers
echo -e "${YELLOW}Building and starting containers...${NC}"
docker-compose up -d --build

# Wait for services to start
echo -e "${YELLOW}Waiting for services to start...${NC}"
sleep 10

# Check if containers are running
echo -e "${YELLOW}Checking container status...${NC}"
if [ $(docker-compose ps -q | wc -l) -lt 4 ]; then
    echo -e "${RED}Error: Not all containers are running. Check logs for details.${NC}"
    docker-compose logs
    exit 1
fi

# Check Django for errors
echo -e "${YELLOW}Checking Django for errors...${NC}"
if ! docker-compose exec web python manage.py check; then
    echo -e "${RED}Error: Django check failed.${NC}"
    exit 1
fi

# Run migrations
echo -e "${YELLOW}Running migrations...${NC}"
if ! docker-compose exec web python manage.py migrate; then
    echo -e "${RED}Error: Database migrations failed.${NC}"
    exit 1
fi

# Collect static files
echo -e "${YELLOW}Collecting static files...${NC}"
if ! docker-compose exec web python manage.py collectstatic --noinput; then
    echo -e "${RED}Error: Static file collection failed.${NC}"
    exit 1
fi

# Check Celery
echo -e "${YELLOW}Checking Celery status...${NC}"
if ! docker-compose exec celery celery -A core inspect ping; then
    echo -e "${RED}Warning: Celery workers may not be running properly.${NC}"
fi

# Check Redis
echo -e "${YELLOW}Checking Redis connection...${NC}"
if ! docker-compose exec redis redis-cli ping; then
    echo -e "${RED}Error: Redis is not responding.${NC}"
    exit 1
fi

# Check if the web application is accessible
echo -e "${YELLOW}Checking web application accessibility...${NC}"
sleep 5
if ! curl -s http://localhost:8000 > /dev/null; then
    echo -e "${RED}Error: Web application is not accessible.${NC}"
    docker-compose logs web
    exit 1
fi

# All checks passed
echo -e "${GREEN}All checks passed! The application is running correctly.${NC}"

# Print application URLs
echo -e "${YELLOW}Application URLs:${NC}"
echo -e "  - Web: ${GREEN}http://localhost:8000${NC}"

# Print useful commands
echo -e "${YELLOW}Useful commands:${NC}"
echo -e "  - View logs: ${GREEN}docker-compose logs -f${NC}"
echo -e "  - Stop application: ${GREEN}docker-compose down${NC}"
echo -e "  - Restart services: ${GREEN}docker-compose restart${NC}"

# Keep containers running
echo -e "${YELLOW}Containers are running in the background.${NC}"
echo -e "${YELLOW}Use 'docker-compose down' to stop them when you're done.${NC}"