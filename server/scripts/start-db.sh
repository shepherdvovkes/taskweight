#!/bin/bash

# TaskWeight Development Database Startup Script

echo "🚀 Starting TaskWeight development database..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Check if containers are already running
if docker ps --format "table {{.Names}}" | grep -q "taskweight_postgres_dev"; then
    echo "⚠️  Database containers are already running."
    echo "   To restart, run: docker-compose -f docker-compose.dev.yml down && docker-compose -f docker-compose.dev.yml up -d"
    exit 0
fi

# Start the database services
echo "📦 Starting PostgreSQL, Redis, and pgAdmin..."
docker-compose -f docker-compose.dev.yml up -d

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
sleep 10

# Check if PostgreSQL is ready
echo "🔍 Checking PostgreSQL connection..."
until docker exec taskweight_postgres_dev pg_isready -U taskweight_user -d taskweight > /dev/null 2>&1; do
    echo "   Waiting for PostgreSQL..."
    sleep 2
done

echo "✅ PostgreSQL is ready!"

# Check if Redis is ready
echo "🔍 Checking Redis connection..."
until docker exec taskweight_redis_dev redis-cli ping > /dev/null 2>&1; do
    echo "   Waiting for Redis..."
    sleep 2
done

echo "✅ Redis is ready!"

echo ""
echo "🎉 Development database is running!"
echo ""
echo "📊 Services:"
echo "   PostgreSQL: localhost:5432"
echo "   Redis: localhost:6379"
echo "   pgAdmin: http://localhost:5050"
echo ""
echo "🔑 Database credentials:"
echo "   Database: taskweight"
echo "   Username: taskweight_user"
echo "   Password: taskweight_password"
echo ""
echo "📝 pgAdmin credentials:"
echo "   Email: admin@taskweight.com"
echo "   Password: admin"
echo ""
echo "🛑 To stop: docker-compose -f docker-compose.dev.yml down"
echo "📋 To view logs: docker-compose -f docker-compose.dev.yml logs -f"
