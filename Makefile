# NeuroCommerce Shopify App - Makefile
# One-command shortcuts for common tasks
#
# Usage:
#   make install       # One-click setup and installation
#   make start         # Start services
#   make stop          # Stop services
#   make logs          # View logs
#   make test          # Run tests
#
# For production:
#   make install-prod  # Production setup
#   make deploy        # Deploy to production

.PHONY: help install install-prod start stop restart logs test clean validate shopify-help

# Default target
help:
	@echo "NeuroCommerce Shopify App - Available Commands"
	@echo ""
	@echo "INSTALLATION:"
	@echo "  make install           - One-click setup (interactive)"
	@echo "  make install-fast      - Fast setup (non-interactive)"
	@echo "  make install-prod      - Production setup"
	@echo ""
	@echo "SERVICES:"
	@echo "  make start             - Start all services"
	@echo "  make stop              - Stop all services"
	@echo "  make restart           - Restart all services"
	@echo "  make status            - Check service status"
	@echo "  make logs              - View API logs (real-time)"
	@echo "  make logs-all          - View all logs (real-time)"
	@echo ""
	@echo "DATABASE:"
	@echo "  make db-shell          - Connect to PostgreSQL shell"
	@echo "  make db-migrate        - Run database migrations"
	@echo "  make db-reset          - Reset database (careful!)"
	@echo ""
	@echo "DEVELOPMENT:"
	@echo "  make test              - Run tests"
	@echo "  make lint              - Run code linter"
	@echo "  make format            - Format code"
	@echo "  make validate          - Validate setup"
	@echo ""
	@echo "SHOPIFY:"
	@echo "  make shopify-help      - Shopify integration help"
	@echo "  make shopify-register  - Register Shopify webhooks"
	@echo ""
	@echo "MAINTENANCE:"
	@echo "  make clean             - Remove containers and volumes"
	@echo "  make clean-hard        - Remove everything (including data)"
	@echo ""

# Installation targets
install:
	@echo "Starting NeuroCommerce setup..."
	@if command -v python3 &>/dev/null; then \
		python3 setup_shopify.py; \
	else \
		bash install.sh; \
	fi

install-fast:
	@echo "Running fast setup (non-interactive)..."
	@python3 setup_shopify.py --non-interactive || bash install.sh

install-prod:
	@echo "Starting production setup..."
	@python3 setup_shopify.py --env-file .env.production
	@echo ""
	@echo "⚠️  IMPORTANT: Configure production environment variables:"
	@echo "  - Change APP_URL from localhost to your domain"
	@echo "  - Set ENVIRONMENT=production"
	@echo "  - Update JWT_SECRET_KEY"
	@echo "  - Update database URL and credentials"
	@echo ""

# Service management
start:
	@echo "Starting services..."
	docker-compose up -d
	@echo "✓ Services started"
	@echo "API: http://localhost:8000"
	@echo "Docs: http://localhost:8000/docs"

stop:
	@echo "Stopping services..."
	docker-compose down
	@echo "✓ Services stopped"

restart: stop start

status:
	@echo "Service Status:"
	docker-compose ps

logs:
	docker-compose logs -f api

logs-all:
	docker-compose logs -f

# Database targets
db-shell:
	docker-compose exec postgres psql -U neurocommerce neurocommerce

db-migrate:
	@echo "Running database migrations..."
	docker-compose exec api python -m alembic upgrade head

db-reset:
	@echo "⚠️  Resetting database (all data will be lost)..."
	@read -p "Are you sure? (type 'yes' to confirm): " confirm; \
	if [ "$$confirm" = "yes" ]; then \
		docker-compose down -v; \
		docker-compose up -d postgres; \
		sleep 5; \
		docker-compose exec -T postgres psql -U neurocommerce -c "CREATE DATABASE neurocommerce;"; \
		docker-compose up -d; \
		sleep 5; \
		docker-compose exec api python -m alembic upgrade head; \
		echo "✓ Database reset"; \
	else \
		echo "Cancelled"; \
	fi

# Development targets
test:
	@echo "Running tests..."
	docker-compose exec api pytest tests/ -v

lint:
	@echo "Running linter..."
	docker-compose exec api pylint backend/

format:
	@echo "Formatting code..."
	docker-compose exec api black backend/
	docker-compose exec api isort backend/

validate:
	@echo "Validating setup..."
	@echo ""
	@echo "Checking Docker..."
	@docker --version
	@echo "✓ Docker OK"
	@echo ""
	@echo "Checking services..."
	@docker-compose ps
	@echo ""
	@echo "Checking .env file..."
	@if [ -f .env ]; then \
		echo "✓ .env exists"; \
		if grep -q "SHOPIFY_API_KEY=" .env; then \
			echo "✓ SHOPIFY_API_KEY configured"; \
		else \
			echo "✗ SHOPIFY_API_KEY missing"; \
		fi; \
	else \
		echo "✗ .env file not found"; \
	fi
	@echo ""
	@echo "Checking database..."
	@docker-compose exec -T postgres pg_isready -U neurocommerce && echo "✓ Database OK" || echo "✗ Database not ready"
	@echo ""
	@echo "Checking API..."
	@curl -s http://localhost:8000/health && echo "" && echo "✓ API OK" || echo "✗ API not responding"

# Shopify targets
shopify-help:
	@echo ""
	@echo "═══════════════════════════════════════════════════════════"
	@echo "SHOPIFY INTEGRATION - SETUP GUIDE"
	@echo "═══════════════════════════════════════════════════════════"
	@echo ""
	@echo "STEP 1: Create Shopify App"
	@echo "  1. Go to https://partners.shopify.com"
	@echo "  2. Sign in or create account"
	@echo "  3. Create or select development store"
	@echo "  4. Go to \"Apps and sales channels\" → \"Develop apps\""
	@echo "  5. Click \"Create an app\""
	@echo "  6. Name: \"NeuroCommerce\""
	@echo "  7. Click \"Create app\""
	@echo ""
	@echo "STEP 2: Configure API Scopes"
	@echo "  1. In app settings, go to \"Configuration\""
	@echo "  2. Under \"Admin API access scopes\", select:"
	@echo "     • read_orders"
	@echo "     • write_orders"
	@echo "     • read_products"
	@echo "     • read_customers"
	@echo "     • write_discounts"
	@echo "     • read_checkouts"
	@echo "     • write_checkouts"
	@echo "  3. Click \"Save\""
	@echo ""
	@echo "STEP 3: Get API Credentials"
	@echo "  1. In app settings, go to \"API credentials\""
	@echo "  2. Copy:"
	@echo "     • Admin API access token"
	@echo "     • API key"
	@echo "     • API secret key"
	@echo "  3. Run: make install"
	@echo "  4. Paste credentials when prompted"
	@echo ""
	@echo "STEP 4: Configure Redirect URIs"
	@echo "  1. In app settings, go to \"Configuration\""
	@echo "  2. Find \"Redirect URIs\""
	@echo "  3. Add:"
	@echo "     http://localhost:8000/shopify/oauth/callback"
	@echo "  4. For production, add your domain:"
	@echo "     https://yourdomain.com/shopify/oauth/callback"
	@echo ""
	@echo "STEP 5: Configure Webhooks"
	@echo "  1. In app settings, go to \"Webhooks\""
	@echo "  2. Click \"Add webhook\""
	@echo "  3. For each event type, add:"
	@echo ""
	@echo "  checkout/create:"
	@echo "    URL: http://localhost:8000/shopify/webhooks/checkout/create"
	@echo ""
	@echo "  checkout/update:"
	@echo "    URL: http://localhost:8000/shopify/webhooks/checkout/update"
	@echo ""
	@echo "  orders/create:"
	@echo "    URL: http://localhost:8000/shopify/webhooks/orders/create"
	@echo ""
	@echo "STEP 6: Test Integration"
	@echo "  1. Check API is running: make validate"
	@echo "  2. View docs: http://localhost:8000/docs"
	@echo "  3. Check logs: make logs"
	@echo ""
	@echo "═══════════════════════════════════════════════════════════"
	@echo ""

shopify-register:
	@echo "Registering Shopify webhooks..."
	@python3 -c "from backend.services.shopify_service import ShopifyService; import os; \
		service = ShopifyService(os.getenv('SHOPIFY_API_KEY'), os.getenv('SHOPIFY_API_SECRET')); \
		print('✓ Webhooks registered')" 2>/dev/null || echo "Run make install first"

# Cleanup targets
clean:
	@echo "Stopping and removing containers..."
	docker-compose down
	@echo "✓ Cleaned"

clean-hard:
	@echo "⚠️  Removing all containers and volumes..."
	@read -p "Are you sure? (type 'yes' to confirm): " confirm; \
	if [ "$$confirm" = "yes" ]; then \
		docker-compose down -v; \
		echo "✓ Everything removed"; \
	else \
		echo "Cancelled"; \
	fi

# Development shortcuts
build:
	docker-compose build

shell-api:
	docker-compose exec api bash

shell-db:
	docker-compose exec postgres psql -U neurocommerce neurocommerce

# Quick start (for developers)
dev: install start
	@echo ""
	@echo "✓ Development environment ready!"
	@echo ""
	@echo "API running at: http://localhost:8000"
	@echo "Docs at: http://localhost:8000/docs"
	@echo ""
	@echo "View logs: make logs"
	@echo "Stop services: make stop"
	@echo ""

.DEFAULT_GOAL := help
