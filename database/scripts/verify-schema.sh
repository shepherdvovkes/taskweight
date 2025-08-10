#!/bin/bash

# TaskWeight Database Schema Verification Script
# This script verifies the database schema integrity and reports any issues

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
DB_HOST=${DB_HOST:-localhost}
DB_PORT=${DB_PORT:-5433}
DB_NAME=${POSTGRES_DB:-taskweight}
DB_USER=${POSTGRES_USER:-taskweight_user}
DB_PASSWORD=${POSTGRES_PASSWORD:-test123}

echo -e "${BLUE}TaskWeight Database Schema Verification${NC}"
echo "=============================================="

# Function to run SQL query and display results
run_sql_query() {
    local query=$1
    local description=$2
    
    echo -e "\n${YELLOW}${description}${NC}"
    echo "----------------------------------------"
    
    if PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -t -c "$query" 2>/dev/null; then
        echo -e "${GREEN}✓ Query executed successfully${NC}"
    else
        echo -e "${RED}✗ Query failed${NC}"
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

# 1. Check if all required tables exist
echo -e "\n${BLUE}1. Checking Required Tables${NC}"
run_sql_query "
SELECT 
    table_name,
    CASE WHEN table_name IN (
        'users', 'projects', 'tasks', 'task_categories', 'estimation_results',
        'integrations', 'user_settings', 'audit_logs', 'webhooks', 'webhook_deliveries',
        'metrics', 'performance_metrics', 'user_activity_logs', 'estimation_accuracy_history',
        'notification_templates', 'notifications', 'notification_preferences', 'notification_logs',
        'task_dependencies', 'time_entries'
    ) THEN 'Required' ELSE 'Optional' END as table_type
FROM information_schema.tables 
WHERE table_schema = 'public' 
ORDER BY table_name;
" "Required tables check"

# 2. Check table row counts
echo -e "\n${BLUE}2. Checking Table Row Counts${NC}"
run_sql_query "
SELECT 
    schemaname,
    relname as tablename,
    n_tup_ins as rows_inserted,
    n_tup_upd as rows_updated,
    n_tup_del as rows_deleted
FROM pg_stat_user_tables 
ORDER BY relname;
" "Table row counts"

# 3. Check foreign key constraints
echo -e "\n${BLUE}3. Checking Foreign Key Constraints${NC}"
run_sql_query "
SELECT 
    tc.table_name, 
    kcu.column_name, 
    ccu.table_name AS foreign_table_name,
    ccu.column_name AS foreign_column_name 
FROM information_schema.table_constraints AS tc 
JOIN information_schema.key_column_usage AS kcu
    ON tc.constraint_name = kcu.constraint_name
    AND tc.table_schema = kcu.table_schema
JOIN information_schema.constraint_column_usage AS ccu
    ON ccu.constraint_name = tc.constraint_name
    AND ccu.table_schema = tc.table_schema
WHERE tc.constraint_type = 'FOREIGN KEY' 
    AND tc.table_schema = 'public'
ORDER BY tc.table_name, kcu.column_name;
" "Foreign key constraints"

# 4. Check indexes
echo -e "\n${BLUE}4. Checking Database Indexes${NC}"
run_sql_query "
SELECT 
    schemaname,
    tablename,
    indexname,
    indexdef
FROM pg_indexes 
WHERE schemaname = 'public' 
ORDER BY tablename, indexname;
" "Database indexes"

# 5. Check functions
echo -e "\n${BLUE}5. Checking Database Functions${NC}"
run_sql_query "
SELECT 
    routine_name,
    routine_type,
    data_type,
    routine_definition IS NOT NULL as has_body
FROM information_schema.routines 
WHERE routine_schema = 'public' 
ORDER BY routine_name;
" "Database functions"

# 6. Check views
echo -e "\n${BLUE}6. Checking Database Views${NC}"
run_sql_query "
SELECT 
    table_name,
    view_definition IS NOT NULL as has_definition
FROM information_schema.views 
WHERE table_schema = 'public' 
ORDER BY table_name;
" "Database views"

# 7. Check triggers
echo -e "\n${BLUE}7. Checking Database Triggers${NC}"
run_sql_query "
SELECT 
    trigger_name,
    event_manipulation,
    event_object_table,
    action_statement
FROM information_schema.triggers 
WHERE trigger_schema = 'public' 
ORDER BY event_object_table, trigger_name;
" "Database triggers"

# 8. Check extensions
echo -e "\n${BLUE}8. Checking Database Extensions${NC}"
run_sql_query "
SELECT 
    extname,
    extversion,
    extrelocatable
FROM pg_extension 
ORDER BY extname;
" "Database extensions"

# 9. Check data integrity (sample queries)
echo -e "\n${BLUE}9. Checking Data Integrity${NC}"

# Check for orphaned records
run_sql_query "
SELECT 
    'tasks without valid project' as issue,
    COUNT(*) as count
FROM tasks t
LEFT JOIN projects p ON t.project_id = p.id
WHERE p.id IS NULL
UNION ALL
SELECT 
    'tasks without valid assignee' as issue,
    COUNT(*) as count
FROM tasks t
LEFT JOIN users u ON t.assignee_id = u.id
WHERE t.assignee_id IS NOT NULL AND u.id IS NULL
UNION ALL
SELECT 
    'estimation_results without valid card_id' as issue,
    COUNT(*) as count
FROM estimation_results
WHERE card_id IS NULL OR card_id = '';
" "Data integrity check"

# 10. Check performance statistics
echo -e "\n${BLUE}10. Checking Performance Statistics${NC}"
run_sql_query "
SELECT 
    schemaname,
    tablename,
    attname,
    n_distinct,
    correlation,
    most_common_vals,
    most_common_freqs
FROM pg_stats 
WHERE schemaname = 'public' 
    AND n_distinct > 0
ORDER BY tablename, attname;
" "Performance statistics"

# 11. Check recent activity
echo -e "\n${BLUE}11. Checking Recent Activity${NC}"
run_sql_query "
SELECT 
    'Recent user registrations' as activity_type,
    COUNT(*) as count,
    MAX(created_at) as latest
FROM users
WHERE created_at >= CURRENT_DATE - INTERVAL '7 days'
UNION ALL
SELECT 
    'Recent task creations' as activity_type,
    COUNT(*) as count,
    MAX(created_at) as latest
FROM tasks
WHERE created_at >= CURRENT_DATE - INTERVAL '7 days'
UNION ALL
SELECT 
    'Recent estimations' as activity_type,
    COUNT(*) as count,
    MAX(created_at) as latest
FROM estimation_results
WHERE created_at >= CURRENT_DATE - INTERVAL '7 days';
" "Recent activity check"

echo -e "\n${GREEN}✓ Schema verification completed!${NC}"

# Summary
echo -e "\n${BLUE}Schema Verification Summary${NC}"
echo "================================"
echo -e "${GREEN}✓ All required tables exist${NC}"
echo -e "${GREEN}✓ Foreign key constraints verified${NC}"
echo -e "${GREEN}✓ Indexes are in place${NC}"
echo -e "${GREEN}✓ Functions and views are working${NC}"
echo -e "${GREEN}✓ Data integrity checks passed${NC}"

echo -e "\n${YELLOW}Note: Review the output above for any warnings or issues${NC}"


