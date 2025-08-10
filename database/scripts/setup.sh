#!/bin/bash

# TaskWeight Database Setup Script
# This script sets up the complete database environment

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== TaskWeight Database Setup ===${NC}"
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}Docker is not running. Please start Docker and try again.${NC}"
    exit 1
fi

# Check if Docker Compose is available
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}Docker Compose is not installed. Please install it and try again.${NC}"
    exit 1
fi

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo -e "${YELLOW}Creating .env file from template...${NC}"
    cp env.example .env
    echo -e "${GREEN}✓ .env file created. Please edit it with your actual values.${NC}"
    echo -e "${YELLOW}Press Enter to continue after editing .env file...${NC}"
    read
fi

# Load environment variables
source .env

# Make scripts executable
echo -e "${YELLOW}Making scripts executable...${NC}"
chmod +x scripts/*.sh

# Create necessary directories
echo -e "${YELLOW}Creating necessary directories...${NC}"
mkdir -p backup
mkdir -p postgres/log

# Start database services
echo -e "${YELLOW}Starting database services...${NC}"
docker-compose up -d

# Wait for services to be ready
echo -e "${YELLOW}Waiting for services to be ready...${NC}"
sleep 30

# Check service health
echo -e "${YELLOW}Checking service health...${NC}"
./scripts/health-check.sh

echo ""
echo -e "${GREEN}=== Setup completed successfully! ===${NC}"
echo ""
echo -e "${BLUE}Services running:${NC}"
echo -e "  PostgreSQL: localhost:${POSTGRES_PORT:-5432}"
echo -e "  PgAdmin: http://localhost:${PGADMIN_PORT:-8080}"
echo -e "  Redis: localhost:${REDIS_PORT:-6379}"
echo ""
echo -e "${BLUE}Useful commands:${NC}"
echo -e "  Check status: docker-compose ps"
echo -e "  View logs: docker-compose logs postgres"
echo -e "  Health check: ./scripts/health-check.sh"
echo -e "  Backup: ./scripts/backup.sh"
echo -e "  Stop services: docker-compose down"
echo ""
echo -e "${GREEN}Database is ready for use!${NC}"
