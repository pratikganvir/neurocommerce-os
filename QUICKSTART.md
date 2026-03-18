# NeuroCommerce OS - Quick Start Guide

Get the complete AI Revenue Operating System running in under 5 minutes.

## Prerequisites

- **Docker Desktop** 20.10+ ([Download](https://www.docker.com/products/docker-desktop))
- **8GB RAM** minimum
- **20GB disk space** for containers

## Installation (5 minutes)

### 1. Clone Repository

```bash
git clone https://github.com/neurocommerce/neurocommerce-os.git
cd neurocommerce-os
```

### 2. Run Quick Start Script

```bash
chmod +x scripts/start-local.sh
./scripts/start-local.sh
```

**What this does:**
- ✅ Validates Docker installation
- ✅ Creates `.env` configuration file
- ✅ Starts 12 Docker containers (API, databases, Kafka, monitoring)
- ✅ Initializes PostgreSQL database
- ✅ Displays service URLs

**Expected output:**
```
✅ NeuroCommerce OS is running!

📊 Dashboard:     http://localhost:3000
🔌 API:           http://localhost:8000
📈 Grafana:       http://localhost:3001 (admin:admin)
📉 Prometheus:    http://localhost:9090
```

### 3. Manual Setup (Alternative)

If the script doesn't work, manually start services:

```bash
# Start all services
docker-compose up -d

# Wait for services to be healthy (30 seconds)
sleep 30

# Initialize database
docker-compose exec api python -c "from backend.api.database import init_db; init_db()"
```

## First Steps

### Register Your Store (1 minute)

```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "merchant@example.com",
    "password": "MySecurePassword123!",
    "name": "John Merchant",
    "store_name": "My Awesome Store"
  }'
```

**Response (save these values):**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "user_id": "user_123abc",
  "store_id": "store_456def",
  "api_key": "sk_live_xyz789"
}
```

### Get API Key for SDK

The `api_key` above (e.g., `sk_live_xyz789`) is what you embed in your store.

### Embed SDK in Your Store (1 minute)

Add this single line to your ecommerce store's HTML footer:

```html
<script src="https://cdn.neurocommerce.io/neurocommerce.js"></script>
<script>
  window.neurocommerce = new NeuroCommerceSDK({
    apiKey: 'sk_live_xyz789'  // Replace with your API key
  });
</script>
```

**The SDK automatically tracks:**
- Page views
- Product views
- Product clicks
- Add to cart
- Checkout start
- Order completion
- Exit intent
- Scroll depth

### Test Event Ingestion (1 minute)

Send a test event:

```bash
curl -X POST http://localhost:8000/api/v1/events/track \
  -H "Content-Type: application/json" \
  -H "api-key: sk_live_xyz789" \
  -d '{
    "session_id": "test_session_123",
    "event_type": "page_view",
    "event_data": {
      "path": "/products",
      "title": "Our Products"
    }
  }'
```

**Response:**
```json
{
  "event_id": "event_abc123",
  "status": "queued"
}
```

## Explore the Platform

### Dashboard

Open **http://localhost:3000** in your browser

You'll see:
- 📊 **KPI Cards**: Revenue, conversion rate, AOV, recovered revenue
- 📈 **Charts**: Revenue trends over time, agent decision distribution
- 🤖 **Agents**: View decisions made by each agent

### API Documentation

Open **http://localhost:8000/docs** in your browser

Interactive Swagger UI showing all endpoints:
- `/auth/*` - Login, register
- `/events/*` - Event tracking
- `/agents/*` - Agent decisions
- `/campaigns/*` - Campaign CRUD
- `/experiments/*` - A/B test management
- `/billing/*` - Subscription info
- `/shopify/*` - Shopify webhooks

### Grafana Monitoring

Open **http://localhost:3001** in your browser

Default credentials: **admin** / **admin**

Pre-configured dashboards show:
- API latency and throughput
- Agent decision rates
- Event processing speed
- Database performance
- Cache hit rates

### Prometheus Metrics

Open **http://localhost:9090** in your browser

Query examples:
```
# API request latency (95th percentile)
histogram_quantile(0.95, api_request_duration_seconds)

# Events processed per second
rate(events_processed_total[1m])

# Agent decisions by type
sum(agent_decisions_total) by (agent_type)
```

## Next Steps

### 1. Understand the System

- Read [ARCHITECTURE.md](docs/ARCHITECTURE.md) for detailed design
- Read [API.md](docs/API.md) for API reference
- Read [SDK.md](docs/SDK.md) for SDK documentation

### 2. Create Your First Campaign

```bash
curl -X POST http://localhost:8000/api/v1/campaigns/store_456def \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc..." \
  -d '{
    "name": "Cart Recovery Campaign",
    "campaign_type": "cart_recovery",
    "target_segment": "abandoned_carts",
    "channels": ["email", "sms"],
    "message_template": "Your cart is waiting! Complete your order and get 10% off."
  }'
```

### 3. Run A/B Test

```bash
curl -X POST http://localhost:8000/api/v1/experiments/store_456def \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc..." \
  -d '{
    "name": "Discount Size Test",
    "experiment_type": "discount",
    "control_variant": {
      "name": "Control (10% off)",
      "discount_percent": 10
    },
    "test_variants": [
      {"name": "Variant A (15% off)", "discount_percent": 15},
      {"name": "Variant B (20% off)", "discount_percent": 20}
    ],
    "allocation": {"control": 0.33, "variant_a": 0.33, "variant_b": 0.34},
    "duration_days": 7
  }'
```

### 4. Deploy to Production

When ready to go live:

**Option A: Kubernetes (Recommended)**
```bash
kubectl apply -f infrastructure/k8s/
```

**Option B: AWS with Terraform**
```bash
terraform -chdir=infrastructure/terraform apply -var-file=prod.tfvars
```

See [DEPLOYMENT.md](docs/DEPLOYMENT.md) for detailed instructions.

## Troubleshooting

### Services Won't Start

```bash
# Check Docker is running
docker ps

# View error logs
docker-compose logs api
docker-compose logs postgres

# Restart services
docker-compose restart
```

### Port Already in Use

```bash
# Find process using port 8000
lsof -i :8000

# Kill the process
kill -9 [PID]

# Try starting again
docker-compose up -d
```

### Database Connection Error

```bash
# Verify PostgreSQL is running
docker-compose logs postgres

# Reinitialize database
docker-compose exec api python -c "from backend.api.database import init_db; init_db()"
```

### Event Not Appearing

```bash
# Check Kafka is running
docker-compose logs kafka

# Verify API key is correct
curl http://localhost:8000/api/v1/events/track \
  -H "api-key: sk_live_xyz789" \
  -H "Content-Type: application/json" \
  -d '{"session_id": "test", "event_type": "page_view", "event_data": {}}'

# Check event queue
docker-compose logs api | grep "queued"
```

## Running Tests

```bash
# Unit tests
docker-compose exec api pytest tests/unit/ -v

# Integration tests
docker-compose exec api pytest tests/integration/ -v

# All tests with coverage
docker-compose exec api pytest tests/ --cov=backend/ --cov-report=term
```

## Viewing Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f api
docker-compose logs -f postgres
docker-compose logs -f kafka

# Last 100 lines
docker-compose logs --tail=100 api
```

## Stopping Services

```bash
# Stop all services (keep data)
docker-compose stop

# Resume services
docker-compose start

# Stop and remove containers (keep volumes)
docker-compose down

# Complete cleanup (remove everything)
docker-compose down -v
```

## Configuration

### Environment Variables

Edit `.env` file to configure:

```bash
# Database
DATABASE_URL=postgresql://user:password@postgres:5432/neurocommerce

# Cache & Messaging
REDIS_URL=redis://redis:6379/0
KAFKA_BOOTSTRAP_SERVERS=kafka:9092

# External APIs (optional for testing)
SHOPIFY_API_KEY=xxx
STRIPE_SECRET_KEY=sk_live_xxx
SENDGRID_API_KEY=SG_xxx
TWILIO_ACCOUNT_SID=ACxxx

# JWT Settings
JWT_SECRET=change-this-to-random-32-char-secret
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24

# Debugging
DEBUG=false
LOG_LEVEL=info
```

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│ Your Ecommerce Store (Shopify, WooCommerce, Custom)         │
│ ↓                                                             │
│ [NeuroCommerce JS SDK - Auto-tracks all user actions]       │
└──────────────────────┬──────────────────────────────────────┘
                       │ HTTP/REST
                       ▼
┌──────────────────────────────────────────────────────────────┐
│ NeuroCommerce API (FastAPI) - Port 8000                     │
│ • Authentication (JWT + API keys)                           │
│ • Event ingestion (batch & single)                          │
│ • Shopify OAuth & webhooks                                  │
│ • Campaign & experiment management                          │
└──────────────────────┬──────────────────────────────────────┘
                       │ Publish events
                       ▼
┌──────────────────────────────────────────────────────────────┐
│ Apache Kafka - Real-time Event Streaming                    │
│ Topics: behavior_events, shopify_events, agent_actions      │
└──────────────────────┬──────────────────────────────────────┘
                       │ Consume events
                       ▼
┌──────────────────────────────────────────────────────────────┐
│ 7 AI Agents - Autonomous Decision Making                    │
│ ┌──────────────┬──────────────┬──────────────┐              │
│ │ Behavior     │ Persuasion   │ Recovery     │              │
│ │ Intelligence │ (< 200ms)    │              │              │
│ ├──────────────┼──────────────┼──────────────┤              │
│ │ Pricing      │ Recommend    │ Retention    │              │
│ │ Optimization │ Engine       │ Campaigns    │              │
│ ├──────────────┴──────────────┴──────────────┤              │
│ │ Experimentation (Thompson Sampling)        │              │
│ └──────────────────────────────────────────────┘              │
└──────────────────────┬──────────────────────────────────────┘
                       │ Store decisions
                       ▼
┌──────────────────────────────────────────────────────────────┐
│ Data Layer                                                   │
│ ┌────────────────┐  ┌──────────────┐  ┌──────────────┐     │
│ │ PostgreSQL     │  │ ClickHouse   │  │ Redis Cache  │     │
│ │ (Transactional)│  │ (Analytics)  │  │ (Sessions)   │     │
│ └────────────────┘  └──────────────┘  └──────────────┘     │
└──────────────────────┬──────────────────────────────────────┘
                       │ Query data
                       ▼
┌──────────────────────────────────────────────────────────────┐
│ Merchant Dashboard (Next.js) - Port 3000                     │
│ • KPI metrics                                                │
│ • Agent decision tracking                                    │
│ • Campaign management                                        │
│ • A/B test results                                           │
└──────────────────────────────────────────────────────────────┘
```

## Key Metrics

| Metric | Value |
|--------|-------|
| **Startup Time** | ~30 seconds |
| **Event Ingestion** | 100k+ events/second |
| **API Latency (p95)** | < 100ms |
| **Persuasion Agent (p99)** | < 200ms |
| **ML Inference (p95)** | < 300ms |
| **Dashboard Load** | < 2 seconds |
| **Concurrent Sessions** | 10k+ |

## What's Running?

| Service | Port | Purpose |
|---------|------|---------|
| API | 8000 | FastAPI server |
| Dashboard | 3000 | Next.js merchant UI |
| PostgreSQL | 5432 | Transactional database |
| ClickHouse | 8123 | Analytics database |
| Redis | 6379 | Cache layer |
| Kafka | 9092 | Event streaming broker |
| Zookeeper | 2181 | Kafka coordination |
| Prometheus | 9090 | Metrics collection |
| Grafana | 3001 | Metrics visualization |
| Inference | 8001 | ML prediction service |

## File Structure

```
neurocommerce-os/
├── backend/              # Python FastAPI backend
│   ├── api/             # API server & routes
│   ├── agents/          # 7 AI agents
│   ├── models/          # Database models
│   ├── services/        # External integrations
│   └── workers/         # Background job processing
├── frontend/            # Next.js merchant dashboard
│   └── dashboard/
├── sdk/                 # JavaScript tracking SDK
│   └── js-tracking-sdk/
├── ml/                  # ML pipelines
│   ├── inference/       # Prediction service
│   └── training/        # Model training
├── infrastructure/      # Deployment configs
│   ├── docker/         # Docker Compose
│   ├── k8s/            # Kubernetes manifests
│   └── terraform/      # AWS infrastructure
├── docs/               # Documentation
│   ├── ARCHITECTURE.md # Detailed design
│   ├── DEPLOYMENT.md   # Deployment guide
│   ├── API.md          # API reference
│   └── SDK.md          # SDK guide
└── docker-compose.yml  # Local development
```

## Common Commands

```bash
# View API logs
docker-compose logs -f api

# Execute command in API container
docker-compose exec api bash

# Access PostgreSQL
docker-compose exec postgres psql -U postgres -d neurocommerce

# Flush Redis cache
docker-compose exec redis redis-cli FLUSHALL

# View Kafka topics
docker-compose exec kafka kafka-topics --list --bootstrap-server kafka:9092

# Run tests
docker-compose exec api pytest tests/ -v --cov=backend/

# Stop all services
docker-compose down

# Clean up everything (fresh start)
docker-compose down -v && docker-compose up -d
```

## Next Steps

1. **[Read Architecture Guide](docs/ARCHITECTURE.md)** - Understand how agents work
2. **[API Documentation](docs/API.md)** - Learn all endpoints
3. **[SDK Integration Guide](docs/SDK.md)** - Embed in your store
4. **[Deployment Guide](docs/DEPLOYMENT.md)** - Deploy to production
5. **[Production Checklist](docs/DEPLOYMENT.md#production-checklist)** - Ready for launch

## Support

- 📖 **Documentation**: See `/docs` folder
- 💬 **GitHub Issues**: Report bugs or request features
- 📧 **Email**: support@neurocommerce.io
- 💡 **Slack**: Join our community

---

**Ready to revolutionize your store's revenue? Let's go! 🚀**

Questions? Check the [DEPLOYMENT.md](docs/DEPLOYMENT.md) or [API.md](docs/API.md) for more details.
