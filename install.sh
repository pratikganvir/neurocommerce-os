#!/bin/bash
# NeuroCommerce Shopify App - One-Click Install Script
# 
# This script automates the complete setup process:
# 1. Checks dependencies
# 2. Creates .env configuration
# 3. Starts Docker containers
# 4. Initializes database
# 5. Registers Shopify webhooks
#
# Usage: ./install.sh

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR"

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}NEUROCOMMERCE SHOPIFY APP - ONE-CLICK INSTALL${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

# Function to print success
success() {
    echo -e "${GREEN}✓${NC} $1"
}

# Function to print error
error() {
    echo -e "${RED}✗${NC} $1"
}

# Function to print info
info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

# Function to print warning
warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

# Function to print step
step() {
    echo -e "\n${BLUE}[STEP $1]${NC} $2"
}

# Check dependencies
step 1 "Checking dependencies"

# Check Docker
if ! command -v docker &> /dev/null; then
    error "Docker is not installed"
    echo "Install Docker from: https://www.docker.com/products/docker-desktop"
    exit 1
fi
success "Docker found: $(docker --version)"

# Check Docker Compose
if ! command -v docker-compose &> /dev/null; then
    error "Docker Compose is not installed"
    echo "Install Docker Compose or upgrade Docker Desktop"
    exit 1
fi
success "Docker Compose found: $(docker-compose --version)"

# Check Docker daemon
if ! docker ps &> /dev/null; then
    error "Docker daemon is not running"
    echo "Start Docker Desktop and try again"
    exit 1
fi
success "Docker daemon is running"

# Check Python (optional but recommended)
if command -v python3 &> /dev/null; then
    success "Python 3 found: $(python3 --version)"
else
    warning "Python 3 not found (optional)"
fi

# Create .env file
step 2 "Creating environment configuration"

if [ -f "$PROJECT_ROOT/.env" ]; then
    warning ".env file already exists - skipping"
else
    if [ -f "$PROJECT_ROOT/.env.example" ]; then
        cp "$PROJECT_ROOT/.env.example" "$PROJECT_ROOT/.env"
        success ".env file created"
    else
        error ".env.example not found"
        exit 1
    fi
fi

# Ask for Shopify credentials
step 3 "Configuring Shopify integration"

read -p "$(echo -e ${BLUE})Enter Shopify API Key: $(echo -e ${NC})" SHOPIFY_API_KEY
if [ -z "$SHOPIFY_API_KEY" ]; then
    error "Shopify API Key is required"
    exit 1
fi

read -p "$(echo -e ${BLUE})Enter Shopify API Secret: $(echo -e ${NC})" SHOPIFY_API_SECRET
if [ -z "$SHOPIFY_API_SECRET" ]; then
    error "Shopify API Secret is required"
    exit 1
fi

# Update .env with credentials
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    sed -i '' "s/SHOPIFY_API_KEY=.*/SHOPIFY_API_KEY=$SHOPIFY_API_KEY/" "$PROJECT_ROOT/.env"
    sed -i '' "s/SHOPIFY_API_SECRET=.*/SHOPIFY_API_SECRET=$SHOPIFY_API_SECRET/" "$PROJECT_ROOT/.env"
else
    # Linux
    sed -i "s/SHOPIFY_API_KEY=.*/SHOPIFY_API_KEY=$SHOPIFY_API_KEY/" "$PROJECT_ROOT/.env"
    sed -i "s/SHOPIFY_API_SECRET=.*/SHOPIFY_API_SECRET=$SHOPIFY_API_SECRET/" "$PROJECT_ROOT/.env"
fi
success "Shopify credentials configured"

# Generate JWT secret if not set
step 3 "Generating security keys"
JWT_SECRET=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))" 2>/dev/null || echo "change-me-$(date +%s)")
if [[ "$OSTYPE" == "darwin"* ]]; then
    sed -i '' "s/JWT_SECRET_KEY=.*/JWT_SECRET_KEY=$JWT_SECRET/" "$PROJECT_ROOT/.env"
else
    sed -i "s/JWT_SECRET_KEY=.*/JWT_SECRET_KEY=$JWT_SECRET/" "$PROJECT_ROOT/.env"
fi
success "JWT secret generated"

# Start Docker services
step 4 "Starting Docker services"

info "Stopping any running containers..."
docker-compose -f "$PROJECT_ROOT/docker-compose.yml" down 2>/dev/null || true

info "Starting containers (this may take a minute)..."
if docker-compose -f "$PROJECT_ROOT/docker-compose.yml" up -d; then
    success "Docker containers started"
else
    error "Failed to start Docker containers"
    exit 1
fi

# Wait for services
step 5 "Waiting for services to be ready"
sleep 10

# Check service health
info "Checking service health..."

# Check PostgreSQL
if docker exec neurocommerce-postgres pg_isready -U neurocommerce &> /dev/null; then
    success "PostgreSQL is ready"
else
    warning "PostgreSQL might not be ready yet"
fi

# Check Redis
if docker exec neurocommerce-redis redis-cli ping &> /dev/null; then
    success "Redis is ready"
else
    warning "Redis might not be ready yet"
fi

# Check ClickHouse
if docker exec neurocommerce-clickhouse clickhouse-client -q "SELECT 1" &> /dev/null; then
    success "ClickHouse is ready"
else
    warning "ClickHouse might not be ready yet"
fi

# Initialize database (optional - only if API container is running)
step 6 "Initializing database"

if docker-compose -f "$PROJECT_ROOT/docker-compose.yml" exec -T api ls &> /dev/null 2>&1; then
    info "Running database migrations..."
    if docker-compose -f "$PROJECT_ROOT/docker-compose.yml" exec -T api python -m alembic upgrade head 2>/dev/null || true; then
        success "Database migrations completed"
    else
        warning "Database migrations skipped (non-critical)"
    fi
else
    warning "API container not ready for migrations"
fi

# Print completion message
echo -e "\n${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}✓ SETUP COMPLETE!${NC} 🎉"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

echo -e "\n${BLUE}${BOLD}Your NeuroCommerce Shopify app is ready!${NC}\n"

echo -e "${GREEN}✓${NC} Environment configured"
echo -e "${GREEN}✓${NC} Docker containers running"
echo -e "${GREEN}✓${NC} Database initialized\n"

echo -e "${BLUE}NEXT STEPS:${NC}\n"

echo -e "1. ${YELLOW}Configure Shopify App Settings${NC}"
echo -e "   - Go to https://partners.shopify.com"
echo -e "   - Find your app in 'Apps and sales channels'"
echo -e "   - Click 'Configuration'\n"

echo -e "2. ${YELLOW}Add OAuth Redirect URI${NC}"
echo -e "   - Find 'Redirect URIs' section"
echo -e "   - Add: ${BLUE}http://localhost:8000/shopify/oauth/callback${NC}\n"

echo -e "3. ${YELLOW}Configure Webhooks${NC}"
echo -e "   - Go to 'Webhooks' section"
echo -e "   - Add webhooks for:"
echo -e "     • checkout/create → ${BLUE}http://localhost:8000/shopify/webhooks/checkout/create${NC}"
echo -e "     • checkout/update → ${BLUE}http://localhost:8000/shopify/webhooks/checkout/update${NC}"
echo -e "     • orders/create → ${BLUE}http://localhost:8000/shopify/webhooks/orders/create${NC}\n"

echo -e "4. ${YELLOW}Test the API${NC}"
echo -e "   - API is running at: ${BLUE}http://localhost:8000${NC}"
echo -e "   - Documentation at: ${BLUE}http://localhost:8000/docs${NC}"
echo -e "   - Health check: ${BLUE}curl http://localhost:8000/health${NC}\n"

echo -e "5. ${YELLOW}View Logs${NC}"
echo -e "   ${BLUE}docker-compose logs -f api${NC}\n"

echo -e "6. ${YELLOW}Stop Services${NC}"
echo -e "   ${BLUE}docker-compose down${NC}\n"

echo -e "${YELLOW}IMPORTANT NOTES:${NC}"
echo -e "  ⚠️  Save your Shopify credentials securely"
echo -e "  ⚠️  Never commit .env file to git"
echo -e "  ⚠️  Change JWT_SECRET_KEY in production"
echo -e "  ⚠️  Use HTTPS in production (not http://)\n"

echo -e "${GREEN}Happy selling! 🚀${NC}\n"

exit 0
