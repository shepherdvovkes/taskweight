#!/bin/bash

# TaskWeight Database Migration Script
# This script runs all database migrations in order

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
DB_HOST=${DB_HOST:-localhost}
DB_PORT=${DB_PORT:-5433}
DB_NAME=${POSTGRES_DB:-taskweight}
DB_USER=${POSTGRES_USER:-taskweight_user}
DB_PASSWORD=${POSTGRES_PASSWORD:-taskweight_password}

echo -e "${YELLOW}Starting TaskWeight database migration...${NC}"

# Function to run SQL script
run_sql_script() {
    local script_file=$1
    local description=$2
    
    echo -e "${YELLOW}Running: ${description}${NC}"
    
    if PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -f "$script_file" > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Successfully executed: ${description}${NC}"
    else
        echo -e "${RED}✗ Failed to execute: ${description}${NC}"
        return 1
    fi
}

# Check if PostgreSQL is running
echo "Checking PostgreSQL connection..."
if ! PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "SELECT 1;" > /dev/null 2>&1; then
    echo -e "${RED}Error: Cannot connect to PostgreSQL database${NC}"
    echo "Please check your database connection settings"
    exit 1
fi

echo -e "${GREEN}✓ Database connection successful${NC}"

# Run migrations in order
cd "$(dirname "$0")/../postgres/init"

echo -e "${YELLOW}Running database initialization scripts...${NC}"

# Run main initialization script
run_sql_script "01-init-database.sql" "Database initialization"

# Run migrations
run_sql_script "02-migrations.sql" "Database migrations"

# Run sample data (optional)
if [ "${LOAD_SAMPLE_DATA:-false}" = "true" ]; then
    run_sql_script "03-sample-data.sql" "Sample data"
else
    echo -e "${YELLOW}Skipping sample data (set LOAD_SAMPLE_DATA=true to include)${NC}"
fi

# Run views
run_sql_script "04-views.sql" "Database views"

# Run functions
run_sql_script "05-functions.sql" "Database functions"

# Run webhooks system
run_sql_script "06-webhooks.sql" "Webhooks system"

# Run metrics and analytics
run_sql_script "07-metrics.sql" "Metrics and analytics system"

# Run notifications system
run_sql_script "08-notifications.sql" "Notifications system"

# Run extended sample data (optional)
if [ "${LOAD_SAMPLE_DATA:-false}" = "true" ]; then
    run_sql_script "09-sample-data-extended.sql" "Extended sample data"
else
    echo -e "${YELLOW}Skipping extended sample data (set LOAD_SAMPLE_DATA=true to include)${NC}"
fi

echo -e "${GREEN}✓ All database migrations completed successfully!${NC}"

# Show database status
echo -e "${YELLOW}Database status:${NC}"
PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "
SELECT 
    schemaname,
    tablename,
    attname,
    n_distinct,
    correlation
FROM pg_stats 
WHERE schemaname = 'public' 
ORDER BY tablename, attname;
" 2>/dev/null || echo "Could not retrieve statistics"
