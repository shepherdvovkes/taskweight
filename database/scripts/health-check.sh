#!/bin/bash

# Database Health Check Script for TaskWeight
# This script checks the health of PostgreSQL and Redis services

set -e

# Load environment variables
source .env

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== TaskWeight Database Health Check ===${NC}"
echo ""

# Check PostgreSQL container status
echo -e "${YELLOW}Checking PostgreSQL container...${NC}"
if docker ps | grep -q taskweight_postgres; then
    echo -e "${GREEN}✓ PostgreSQL container is running${NC}"
else
    echo -e "${RED}✗ PostgreSQL container is not running${NC}"
    exit 1
fi

# Check PostgreSQL connection
echo -e "${YELLOW}Checking PostgreSQL connection...${NC}"
if docker exec taskweight_postgres pg_isready -U "${POSTGRES_USER}" -d "${POSTGRES_DB}"; then
    echo -e "${GREEN}✓ PostgreSQL is accepting connections${NC}"
else
    echo -e "${RED}✗ PostgreSQL is not accepting connections${NC}"
    exit 1
fi

# Check Redis container status
echo -e "${YELLOW}Checking Redis container...${NC}"
if docker ps | grep -q taskweight_redis; then
    echo -e "${GREEN}✓ Redis container is running${NC}"
else
    echo -e "${RED}✗ Redis container is not running${NC}"
    exit 1
fi

# Check Redis connection
echo -e "${YELLOW}Checking Redis connection...${NC}"
if docker exec taskweight_redis redis-cli --raw incr ping > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Redis is responding to commands${NC}"
else
    echo -e "${RED}✗ Redis is not responding to commands${NC}"
    exit 1
fi

# Check database size
echo -e "${YELLOW}Checking database size...${NC}"
DB_SIZE=$(docker exec taskweight_postgres psql -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" -t -c "SELECT pg_size_pretty(pg_database_size('${POSTGRES_DB}'));" | xargs)
echo -e "${GREEN}✓ Database size: ${DB_SIZE}${NC}"

# Check active connections
echo -e "${YELLOW}Checking active connections...${NC}"
ACTIVE_CONNS=$(docker exec taskweight_postgres psql -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" -t -c "SELECT count(*) FROM pg_stat_activity WHERE state = 'active';" | xargs)
echo -e "${GREEN}✓ Active connections: ${ACTIVE_CONNS}${NC}"

# Check table counts
echo -e "${YELLOW}Checking table statistics...${NC}"
USERS_COUNT=$(docker exec taskweight_postgres psql -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" -t -c "SELECT count(*) FROM users;" | xargs)
PROJECTS_COUNT=$(docker exec taskweight_postgres psql -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" -t -c "SELECT count(*) FROM projects;" | xargs)
TASKS_COUNT=$(docker exec taskweight_postgres psql -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" -t -c "SELECT count(*) FROM tasks;" | xargs)

echo -e "${GREEN}✓ Users: ${USERS_COUNT}${NC}"
echo -e "${GREEN}✓ Projects: ${PROJECTS_COUNT}${NC}"
echo -e "${GREEN}✓ Tasks: ${TASKS_COUNT}${NC}"

echo ""
echo -e "${GREEN}=== All health checks passed! ===${NC}"
