#!/bin/bash

# Database Backup Script for TaskWeight
# This script creates automated backups of PostgreSQL database

set -e

# Load environment variables
source .env

# Configuration
BACKUP_DIR="/backup"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="taskweight_backup_${DATE}.sql"
RETENTION_DAYS=${BACKUP_RETENTION_DAYS:-30}

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Starting database backup...${NC}"

# Create backup directory if it doesn't exist
mkdir -p "${BACKUP_DIR}"

# Perform database backup
echo -e "${YELLOW}Creating backup: ${BACKUP_FILE}${NC}"
docker exec taskweight_postgres pg_dump \
    -U "${POSTGRES_USER}" \
    -d "${POSTGRES_DB}" \
    -h localhost \
    --clean \
    --create \
    --verbose \
    > "${BACKUP_DIR}/${BACKUP_FILE}"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}Backup completed successfully: ${BACKUP_FILE}${NC}"
    
    # Compress backup
    gzip "${BACKUP_DIR}/${BACKUP_FILE}"
    echo -e "${GREEN}Backup compressed: ${BACKUP_FILE}.gz${NC}"
    
    # Clean old backups
    echo -e "${YELLOW}Cleaning backups older than ${RETENTION_DAYS} days...${NC}"
    find "${BACKUP_DIR}" -name "*.gz" -mtime +${RETENTION_DAYS} -delete
    
    # List current backups
    echo -e "${GREEN}Current backups:${NC}"
    ls -la "${BACKUP_DIR}"/*.gz 2>/dev/null || echo "No backups found"
    
else
    echo -e "${RED}Backup failed!${NC}"
    exit 1
fi
