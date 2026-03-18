#!/bin/bash
# NeuroCommerce OS Quick Start Script

set -e

echo "🚀 NeuroCommerce OS - Quick Start"
echo "=================================="

# Check Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker not found. Please install Docker Desktop."
    exit 1
fi

echo "✓ Docker is installed"

# Check Docker Compose
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose not found. Please install Docker Compose."
    exit 1
fi

echo "✓ Docker Compose is installed"

# Create .env if not exists
if [ ! -f .env ]; then
    echo "📝 Creating .env file..."
    cp .env.example .env
    echo "✓ .env created - please configure with your API keys"
fi

# Start services
echo ""
echo "🐳 Starting Docker services..."
docker-compose up -d

echo ""
echo "⏳ Waiting for services to be healthy..."
sleep 10

# Check health
RETRIES=0
MAX_RETRIES=30
while [ $RETRIES -lt $MAX_RETRIES ]; do
    if curl -f http://localhost:8000/health > /dev/null 2>&1; then
        echo "✓ API is healthy"
        break
    fi
    RETRIES=$((RETRIES + 1))
    sleep 1
done

if [ $RETRIES -eq $MAX_RETRIES ]; then
    echo "❌ API failed to start. Check logs: docker-compose logs api"
    exit 1
fi

# Initialize database
echo ""
echo "🗄️  Initializing database..."
docker-compose exec -T api python -c "from backend.api.database import init_db; init_db()" || echo "⚠️  Database may already be initialized"

echo ""
echo "✅ NeuroCommerce OS is running!"
echo ""
echo "📊 Dashboard:     http://localhost:3000"
echo "🔌 API:           http://localhost:8000"
echo "📈 Grafana:       http://localhost:3001 (admin:admin)"
echo "📉 Prometheus:    http://localhost:9090"
echo ""
echo "Next steps:"
echo "1. Configure your .env file with API keys"
echo "2. Register a store: curl -X POST http://localhost:8000/api/v1/auth/register"
echo "3. Get your API key from the dashboard"
echo "4. Embed SDK in your store"
echo ""
echo "For deployment to Kubernetes, see docs/DEPLOYMENT.md"
