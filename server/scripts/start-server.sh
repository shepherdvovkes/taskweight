#!/bin/bash

# TaskWeight Development Server Startup Script

echo "🚀 Starting TaskWeight development server..."

# Check if virtual environment is activated
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo "⚠️  Virtual environment not activated. Activating..."
    source venv/bin/activate
fi

# Check if database is running
if ! docker ps --format "table {{.Names}}" | grep -q "taskweight_postgres_dev"; then
    echo "❌ Database is not running. Starting it now..."
    ./scripts/start-db.sh
    if [ $? -ne 0 ]; then
        echo "❌ Failed to start database. Exiting."
        exit 1
    fi
fi

# Install dependencies if needed
if ! pip show fastapi > /dev/null 2>&1; then
    echo "📦 Installing dependencies..."
    pip install -r requirements.txt
fi

# Run migrations
echo "🔄 Running database migrations..."
./scripts/migrate.sh

# Start the server
echo "🌐 Starting FastAPI server..."
cd server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
