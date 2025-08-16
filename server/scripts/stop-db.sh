#!/bin/bash

# TaskWeight Development Database Stop Script

echo "🛑 Stopping TaskWeight development database..."

# Check if containers are running
if ! docker ps --format "table {{.Names}}" | grep -q "taskweight_postgres_dev"; then
    echo "⚠️  No database containers are running."
    exit 0
fi

# Stop the database services
echo "📦 Stopping PostgreSQL, Redis, and pgAdmin..."
docker-compose -f docker-compose.dev.yml down

echo "✅ Development database stopped!"
echo ""
echo "💾 Data is preserved in Docker volumes."
echo "   To remove all data, run: docker-compose -f docker-compose.dev.yml down -v"
