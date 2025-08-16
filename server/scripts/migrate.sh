#!/bin/bash

# TaskWeight Database Migration Script

echo "🔄 Running database migrations..."

# Check if virtual environment is activated
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo "⚠️  Virtual environment not activated. Activating..."
    source venv/bin/activate
fi

# Check if database is running
if ! docker ps --format "table {{.Names}}" | grep -q "taskweight_postgres_dev"; then
    echo "❌ Database is not running. Please start it first with: ./scripts/start-db.sh"
    exit 1
fi

# Install dependencies if needed
if ! pip show alembic > /dev/null 2>&1; then
    echo "📦 Installing dependencies..."
    pip install -r requirements.txt
fi

# Run migrations
echo "🚀 Running Alembic migrations..."
cd server
alembic upgrade head

if [ $? -eq 0 ]; then
    echo "✅ Migrations completed successfully!"
else
    echo "❌ Migration failed!"
    exit 1
fi
