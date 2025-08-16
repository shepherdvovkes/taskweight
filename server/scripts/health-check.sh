#!/bin/bash

# TaskWeight Health Check Script

echo "🏥 TaskWeight Health Check"
echo "=========================="

# Check Docker
echo "🐳 Checking Docker..."
if docker info > /dev/null 2>&1; then
    echo "   ✅ Docker is running"
else
    echo "   ❌ Docker is not running"
    exit 1
fi

# Check database containers
echo "🗄️  Checking database containers..."
if docker ps --format "table {{.Names}}" | grep -q "taskweight_postgres_dev"; then
    echo "   ✅ PostgreSQL container is running"
    
    # Check PostgreSQL connection
    if docker exec taskweight_postgres_dev pg_isready -U taskweight_user -d taskweight > /dev/null 2>&1; then
        echo "   ✅ PostgreSQL is accepting connections"
    else
        echo "   ⚠️  PostgreSQL is not accepting connections"
    fi
else
    echo "   ❌ PostgreSQL container is not running"
fi

if docker ps --format "table {{.Names}}" | grep -q "taskweight_redis_dev"; then
    echo "   ✅ Redis container is running"
    
    # Check Redis connection
    if docker exec taskweight_redis_dev redis-cli ping > /dev/null 2>&1; then
        echo "   ✅ Redis is responding"
    else
        echo "   ⚠️  Redis is not responding"
    fi
else
    echo "   ❌ Redis container is not running"
fi

# Check server
echo "🌐 Checking server..."
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "   ✅ Server is responding"
    
    # Get server status
    response=$(curl -s http://localhost:8000/health)
    echo "   📊 Server status: $response"
else
    echo "   ❌ Server is not responding"
fi

# Check ports
echo "🔌 Checking ports..."
if netstat -an 2>/dev/null | grep -q ":5432.*LISTEN"; then
    echo "   ✅ PostgreSQL port 5432 is open"
else
    echo "   ❌ PostgreSQL port 5432 is not open"
fi

if netstat -an 2>/dev/null | grep -q ":6379.*LISTEN"; then
    echo "   ✅ Redis port 6379 is open"
else
    echo "   ❌ Redis port 6379 is not open"
fi

if netstat -an 2>/dev/null | grep -q ":8000.*LISTEN"; then
    echo "   ✅ Server port 8000 is open"
else
    echo "   ❌ Server port 8000 is not open"
fi

# Check virtual environment
echo "🐍 Checking Python environment..."
if [[ "$VIRTUAL_ENV" != "" ]]; then
    echo "   ✅ Virtual environment is activated: $VIRTUAL_ENV"
    
    # Check key packages
    if pip show fastapi > /dev/null 2>&1; then
        echo "   ✅ FastAPI is installed"
    else
        echo "   ❌ FastAPI is not installed"
    fi
    
    if pip show sqlalchemy > /dev/null 2>&1; then
        echo "   ✅ SQLAlchemy is installed"
    else
        echo "   ❌ SQLAlchemy is not installed"
    fi
else
    echo "   ⚠️  Virtual environment is not activated"
fi

echo ""
echo "📋 Summary:"
echo "==========="

# Count running containers
running_containers=$(docker ps --format "table {{.Names}}" | grep -c "taskweight_")
echo "   Containers running: $running_containers/3"

# Check if all services are healthy
if [ $running_containers -eq 3 ] && curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "   🎉 All services are healthy!"
    exit 0
else
    echo "   ⚠️  Some services need attention"
    exit 1
fi
