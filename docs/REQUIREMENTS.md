# NeuroCommerce OS Requirements

## Runtime Dependencies

### Backend API

```
# Sync to /backend/api/requirements.txt
```

```
fastapi==0.104.1
uvicorn==0.24.0
pydantic==2.5.0
pydantic-settings==2.1.0
sqlalchemy==2.0.23
psycopg2-binary==2.9.9
alembic==1.13.0
python-jose==3.3.0
passlib==1.7.4
bcrypt==4.1.1
PyJWT==2.8.1
redis==5.0.1
kafka-python==2.0.2
aiohttp==3.9.1
requests==2.31.0
python-dotenv==1.0.0
click==8.1.7
pytest==7.4.3
pytest-asyncio==0.21.1
httpx==0.25.2
```

### ML/Inference

```
numpy==1.26.0
pandas==2.1.0
scikit-learn==1.3.0
torch==2.0.0
xgboost==2.0.0
```

### Frontend Dashboard

```json
{
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "next": "^14.0.0",
    "typescript": "^5.3.0",
    "tailwindcss": "^3.3.0",
    "recharts": "^2.10.0",
    "axios": "^1.6.0",
    "date-fns": "^2.30.0",
    "zustand": "^4.4.0"
  }
}
```

### JavaScript SDK

Standalone - no external dependencies. Minified bundle < 15KB.

## Infrastructure Requirements

### Development
- Docker Desktop 20.10+
- Docker Compose 2.0+
- 8GB RAM minimum
- 20GB disk space

### Production (AWS)

#### Compute
- EKS 1.27+ (3 t3.large nodes minimum)
- Auto-scaling group (2-10 nodes)
- EC2 instance types: t3.large → t3.2xlarge

#### Database
- RDS PostgreSQL 15
- Instance: db.t3.medium → db.t3.large
- Multi-AZ for HA
- 100GB+ storage

#### Cache
- ElastiCache Redis 7.0
- Instance: cache.t3.micro → cache.t3.small
- Single node (sharded mode for scale)

#### Messaging
- MSK (Managed Streaming for Kafka) 3.6.0
- 3 brokers minimum
- kafka.m5.large instance type

#### CDN & Storage
- CloudFront for SDK distribution
- S3 for model artifacts, event backups
- Glacier for log archival

#### Networking
- VPC with public/private subnets
- NAT Gateway for outbound traffic
- Application Load Balancer

## External Services

### Payment Processing
- **Stripe** (Billing, recurring subscriptions)
- Endpoint: `https://api.stripe.com`

### Email
- **SendGrid** (Transactional & marketing emails)
- Rate: 100/second
- Endpoint: `https://api.sendgrid.com`

### SMS & WhatsApp
- **Twilio** (SMS, WhatsApp, push notifications)
- Rate: 1,000/minute
- Endpoints: `https://api.twilio.com`, `https://media.twiliocdn.com`

### Ecommerce
- **Shopify** (Store data, webhooks)
- API Version: 2024-01
- Endpoint: `https://{shop}.myshopify.com/admin/api`

### LLM
- **OpenAI** (GPT-4 for personalization)
- API Key required
- Endpoint: `https://api.openai.com`

## Network Requirements

### Outbound Connections
- Stripe API (443)
- SendGrid API (443)
- Twilio API (443)
- OpenAI API (443)
- Shopify API (443)

### Inbound Connections
- HTTP (80) - redirect to HTTPS
- HTTPS (443) - main API
- TCP 5432 - PostgreSQL (internal only)
- TCP 6379 - Redis (internal only)
- TCP 9092 - Kafka (internal only)

## Performance Targets

| Metric | Target |
|--------|--------|
| API Latency (p95) | < 100ms |
| Persuasion Agent (p99) | < 200ms |
| ML Inference (p95) | < 300ms |
| Dashboard Load (p95) | < 2s |
| Event Ingestion | 100k/sec |
| Concurrent Sessions | 10k+ |
| Database QPS | 10k+ |

## Scaling Guidelines

| Metric | Trigger | Action |
|--------|---------|--------|
| API CPU | > 70% | +1 pod |
| API Memory | > 80% | +1 pod |
| DB CPU | > 80% | Scale up instance |
| Redis Memory | > 80% | Scale up node |
| Kafka Lag | > 30s | +1 broker/partition |

## Compliance & Security

- **PCI-DSS**: Stripe handles all payment data
- **GDPR**: Data residency, right to deletion
- **CCPA**: Data privacy compliance
- **SOC 2**: Audit logging, access controls
- **TLS 1.2+**: All data in transit encrypted
- **AES-256**: Data at rest encrypted

---

See [DEPLOYMENT.md](DEPLOYMENT.md) for installation instructions.
