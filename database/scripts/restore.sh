#!/bin/bash

# Database Restore Script for TaskWeight
# This script restores PostgreSQL database from backup

set -e

# Load environment variables
source .env

# Configuration
BACKUP_DIR="/backup"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to show usage
usage() {
    echo "Usage: $0 <backup_file>"
    echo "Example: $0 taskweight_backup_20241201_143022.sql.gz"
    echo ""
    echo "Available backups:"
    ls -la "${BACKUP_DIR}"/*.gz 2>/dev/null || echo "No backups found"
    exit 1
}

# Check if backup file is provided
if [ $# -eq 0 ]; then
    usage
fi

BACKUP_FILE="$1"

# Check if backup file exists
if [ ! -f "${BACKUP_DIR}/${BACKUP_FILE}" ]; then
    echo -e "${RED}Backup file not found: ${BACKUP_FILE}${NC}"
    usage
fi

echo -e "${YELLOW}Starting database restore from: ${BACKUP_FILE}${NC}"
echo -e "${RED}WARNING: This will overwrite the current database!${NC}"
read -p "Are you sure you want to continue? (y/N): " -n 1 -r
echo

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}Restore cancelled.${NC}"
    exit 0
fi

# Stop the application if running (optional)
echo -e "${YELLOW}Stopping application containers...${NC}"
docker-compose stop app 2>/dev/null || true

# Restore database
echo -e "${YELLOW}Restoring database...${NC}"

if [[ "${BACKUP_FILE}" == *.gz ]]; then
    # Compressed backup
    gunzip -c "${BACKUP_DIR}/${BACKUP_FILE}" | docker exec -i taskweight_postgres psql \
        -U "${POSTGRES_USER}" \
        -d "${POSTGRES_DB}"
else
    # Uncompressed backup
    docker exec -i taskweight_postgres psql \
        -U "${POSTGRES_USER}" \
        -d "${POSTGRES_DB}" \
        < "${BACKUP_DIR}/${BACKUP_FILE}"
fi

if [ $? -eq 0 ]; then
    echo -e "${GREEN}Database restored successfully!${NC}"
    
    # Restart application containers
    echo -e "${YELLOW}Restarting application containers...${NC}"
    docker-compose start app 2>/dev/null || true
    
    echo -e "${GREEN}Restore completed successfully!${NC}"
else
    echo -e "${RED}Restore failed!${NC}"
    exit 1
fi
