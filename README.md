# NeuroCommerce OS

**AI Revenue Operating System for ecommerce stores**

NeuroCommerce OS autonomously increases revenue through conversion optimization, checkout persuasion, cart recovery, pricing optimization, product recommendations, retention automation, and growth experimentation.

## Quick Start

### Prerequisites
- Docker & Docker Compose
- Python 3.11+
- Node.js 18+
- Kafka
- PostgreSQL

### Local Development

```bash
git clone https://github.com/neurocommerce/neurocommerce-os.git
cd neurocommerce-os

# Start all services
docker-compose up -d

# Initialize database
docker-compose exec api alembic upgrade head

# Run frontend dev server
cd frontend/dashboard
npm install
npm run dev

# API available at http://localhost:8000
# Dashboard available at http://localhost:3000
```

## Architecture

```
Tracking SDK → Event Streaming (Kafka) → Behavior Intelligence Engine → AI Agent Orchestration → Revenue Optimization Agents → Execution Layer → Merchant Dashboard
```

### Core Components

- **API**: FastAPI, handles authentication, tenant management, webhooks, event ingestion
- **Agents**: Behavior prediction, checkout persuasion, cart recovery, pricing optimization, recommendations, retention
- **Orchestrator**: Routes events to agents, ranks actions, executes best decisions
- **Event Streaming**: Kafka for async processing of user behavior and merchant actions
- **Dashboard**: Next.js UI for analytics, campaigns, experiments, and settings
- **SDK**: JavaScript tracking SDK embedded in merchant stores
- **ML Pipelines**: Model training and inference for behavior prediction

## Tech Stack

### Backend
- FastAPI, Pydantic, SQLAlchemy
- PostgreSQL (transactional), ClickHouse (analytics), Redis (cache)
- Kafka (event streaming)

### Frontend
- Next.js, TypeScript, TailwindCSS, Recharts

### ML/AI
- PyTorch, scikit-learn, XGBoost
- OpenAI API for LLM-based agents
- Vector embeddings for recommendations

### Infrastructure
- Docker, Kubernetes
- Helm (K8s package manager)
- Terraform (IaC)

### Observability
- Prometheus + Grafana (metrics)
- OpenTelemetry (distributed tracing)

## Documentation

- [Architecture Guide](docs/ARCHITECTURE.md)
- [API Documentation](docs/API.md)
- [SDK Documentation](docs/SDK.md)
- [Deployment Guide](docs/DEPLOYMENT.md)
- [Database Schema](docs/DATABASE.md)

## Project Structure

```
neurocommerce-os/
├── backend/              # Python FastAPI services
│   ├── api/              # Main API service
│   ├── agents/           # AI agent implementations
│   ├── orchestration/    # Agent orchestration
│   ├── services/         # Business logic services
│   ├── models/           # SQLAlchemy ORM models
│   ├── integrations/     # External integrations (Shopify, Stripe, etc)
│   └── workers/          # Kafka consumer workers
├── frontend/
│   └── dashboard/        # Next.js merchant dashboard
├── sdk/
│   └── js-tracking-sdk/  # JavaScript tracking SDK
├── ml/
│   ├── training/         # Model training pipelines
│   └── inference/        # Real-time inference service
├── data/
│   └── pipelines/        # Data processing pipelines
├── infrastructure/
│   ├── docker/           # Dockerfiles
│   ├── helm/             # Kubernetes Helm charts
│   └── terraform/        # Terraform IaC
├── tests/                # Test suites
├── docs/                 # Documentation
└── docker-compose.yml    # Local dev environment
```

## Key Features

### Revenue Optimization
- **Conversion Intelligence**: Real-time purchase intent prediction
- **Checkout Persuasion**: Dynamic offers (coupons, social proof, urgency) in <200ms
- **Cart Recovery**: Multi-channel recovery (email, SMS, WhatsApp, push)
- **Pricing Optimization**: Dynamic discounts based on customer sensitivity
- **Product Recommendations**: Collaborative filtering + embedding similarity
- **Retention Automation**: Replenishment reminders, cross-sell campaigns
- **Experimentation**: Multi-armed bandit A/B tests with auto-optimization

### Multi-Tenant SaaS
- Secure tenant isolation
- JWT + OAuth authentication
- RBAC for user permissions
- Stripe billing with usage-based pricing

### Shopify Integration
- OAuth authentication
- Webhook support (orders, carts, checkouts)
- HMAC signature validation
- Full Shopify API client

### Monitoring & Observability
- Agent decision tracking
- Conversion impact metrics
- Message delivery analytics
- Latency monitoring

## Development

### Running Tests

```bash
# Unit tests
docker-compose exec api pytest tests/unit -v

# Integration tests
docker-compose exec api pytest tests/integration -v

# Load tests
docker-compose exec api locust -f tests/load/locustfile.py
```

### Contributing

1. Create feature branch
2. Make changes
3. Run tests locally
4. Submit PR

## License

MIT License - See LICENSE file

## Support

For issues, questions, or contributions: support@neurocommerce.io
