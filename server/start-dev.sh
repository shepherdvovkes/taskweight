#!/bin/bash

# TaskWeight Development Environment Startup Script

echo "🚀 Starting TaskWeight Development Environment"
echo "=============================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if we're in the right directory
if [ ! -f "requirements.txt" ]; then
    print_error "Please run this script from the server directory"
    exit 1
fi

# Check Docker
print_status "Checking Docker..."
if ! docker info > /dev/null 2>&1; then
    print_error "Docker is not running. Please start Docker first."
    exit 1
fi
print_success "Docker is running"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    print_warning "Virtual environment not found. Creating one..."
    python3 -m venv venv
    print_success "Virtual environment created"
fi

# Activate virtual environment
print_status "Activating virtual environment..."
source venv/bin/activate
print_success "Virtual environment activated"

# Install dependencies
print_status "Installing dependencies..."
pip install -r requirements.txt
if [ $? -eq 0 ]; then
    print_success "Dependencies installed"
else
    print_error "Failed to install dependencies"
    exit 1
fi

# Start database
print_status "Starting database services..."
./scripts/start-db.sh
if [ $? -eq 0 ]; then
    print_success "Database services started"
else
    print_error "Failed to start database services"
    exit 1
fi

# Wait a bit for services to be ready
print_status "Waiting for services to be ready..."
sleep 15

# Run migrations
print_status "Running database migrations..."
./scripts/migrate.sh
if [ $? -eq 0 ]; then
    print_success "Migrations completed"
else
    print_error "Migrations failed"
    exit 1
fi

# Health check
print_status "Performing health check..."
./scripts/health-check.sh
if [ $? -eq 0 ]; then
    print_success "All services are healthy"
else
    print_warning "Some services may need attention"
fi

echo ""
echo "🎉 TaskWeight Development Environment is ready!"
echo ""
echo "📊 Services:"
echo "   PostgreSQL: localhost:5432"
echo "   Redis: localhost:6379"
echo "   pgAdmin: http://localhost:5050"
echo "   Server: http://localhost:8000"
echo ""
echo "📚 Useful commands:"
echo "   Start server: ./scripts/start-server.sh"
echo "   Stop database: ./scripts/stop-db.sh"
echo "   Health check: ./scripts/health-check.sh"
echo "   View logs: docker-compose -f docker-compose.dev.yml logs -f"
echo ""
echo "🔗 API Documentation:"
echo "   Swagger UI: http://localhost:8000/docs"
echo "   ReDoc: http://localhost:8000/redoc"
echo ""
print_status "You can now start the server with: ./scripts/start-server.sh"
