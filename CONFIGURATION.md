# NeuroCommerce OS Configuration Guide

This document describes all configuration options for the NeuroCommerce OS platform. All configuration is managed through environment variables defined in `.env` file.

## Table of Contents

1. [Getting Started](#getting-started)
2. [Application Configuration](#application-configuration)
3. [Security & Authentication](#security--authentication)
4. [Database Configuration](#database-configuration)
5. [Cache Configuration](#cache-configuration)
6. [Message Queue Configuration](#message-queue-configuration)
7. [ML & Agent Configuration](#ml--agent-configuration)
8. [External Integrations](#external-integrations)
9. [Observability & Monitoring](#observability--monitoring)
10. [Production Deployment](#production-deployment)

---

## Getting Started

### 1. Copy Environment Template

```bash
cp .env.example .env
```

### 2. Update Critical Values

Edit `.env` and set these required values:

**Minimum for Local Development:**
- `ENVIRONMENT=development`
- `DATABASE_URL=postgresql://neurocommerce:password@localhost:5432/neurocommerce`
- `REDIS_URL=redis://localhost:6379/0`
- `JWT_SECRET_KEY=your-random-secret-key-min-32-chars`

**For Shopify Integration:**
- `SHOPIFY_API_KEY=xxx`
- `SHOPIFY_API_SECRET=xxx`

### 3. Validate Configuration

The system validates critical configuration on startup:
- In production, all required API keys must be set
- JWT secret must not be the default placeholder
- Database URL must be accessible

---

## Application Configuration

### Environment Type

```env
ENVIRONMENT=development                    # Options: development, staging, production
```

**Behavior:**
- `development`: Debug logging, relaxed CORS, detailed error messages
- `staging`: Production-like but less strict rate limiting
- `production`: Strict validation, security checks enabled

### API Configuration

```env
API_VERSION=1.0.0                          # Semantic version number
API_TITLE=NeuroCommerce OS API             # API title in documentation
API_DESCRIPTION=AI Revenue Operating System for ecommerce
API_HOST=0.0.0.0                           # Bind address
API_PORT=8000                              # Port number
API_LOG_LEVEL=info                         # Logging level: debug, info, warning, error
```

**Network Configuration:**

| Setting | Development | Docker | Production |
|---------|-------------|--------|-----------|
| `API_HOST` | `127.0.0.1` | `0.0.0.0` | `0.0.0.0` |
| `API_PORT` | `8000` | `8000` | `8000` |

---

## Security & Authentication

### JWT Configuration

```env
JWT_SECRET_KEY=your-secret-key-min-32-chars  # 🔐 CRITICAL: Change in production!
JWT_ALGORITHM=HS256                           # HS256 or RS256
JWT_EXPIRATION_HOURS=24                       # Token lifetime in hours
TOKEN_TYPE=bearer                             # Token type in responses
```

**JWT Secret Generation:**

```bash
# Generate a secure random key (min 32 characters)
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

**Recommended Values:**

| Environment | JWT_ALGORITHM | Expiration | Notes |
|-------------|---------------|-----------|-------|
| Development | HS256 | 24 hours | Use simple symmetric key |
| Production | RS256 | 12 hours | Use public/private key pair |

### Password Hashing

```env
BCRYPT_ROUNDS=12                           # Cost factor (10-14 recommended)
```

**Bcrypt Rounds:**
- `10`: ~10ms (fast, development)
- `12`: ~100ms (recommended for production)
- `14`: ~1000ms (very secure, slower)

### Role-Based Access Control (RBAC)

```env
DEFAULT_USER_ROLE=viewer                   # New user default role
DEFAULT_ADMIN_ROLE=admin                   # First registered user role
```

**Available Roles:**
- `admin`: Full platform access, user management, settings
- `editor`: Can manage campaigns, experiments, view analytics
- `viewer`: Read-only access to dashboards and reports

---

## Database Configuration

### PostgreSQL Connection

```env
DATABASE_URL=postgresql://neurocommerce:password@postgres:5432/neurocommerce
```

**Connection String Format:**
```
postgresql://[user[:password]@][netloc][:port][/dbname][?param1=value1&...]
```

**Examples:**

```env
# Local Development (no password)
DATABASE_URL=postgresql://neurocommerce:password@localhost:5432/neurocommerce

# Docker Compose
DATABASE_URL=postgresql://neurocommerce:password@postgres:5432/neurocommerce

# AWS RDS
DATABASE_URL=postgresql://user:password@prod-db.xxxxx.us-east-1.rds.amazonaws.com:5432/neurocommerce?sslmode=require

# Azure PostgreSQL
DATABASE_URL=postgresql://user@server:password@server.postgres.database.azure.com:5432/neurocommerce?sslmode=require

# Heroku
DATABASE_URL=postgresql://user:password@ec2-xxx.compute-1.amazonaws.com:5432/dbname?sslmode=require
```

**Connection Pool Settings:**
- NullPool for Kafka workers (no persistent connections)
- Recommended: Use RDS Proxy or PgBouncer for production connection pooling

### Database Initialization

```bash
# Run migrations on startup (automatic)
# Tables created from SQLAlchemy models
```

---

## Cache Configuration

### Redis Connection

```env
REDIS_URL=redis://redis:6379/0
```

**Examples:**

```env
# Local Development
REDIS_URL=redis://localhost:6379/0

# Docker Compose
REDIS_URL=redis://redis:6379/0

# AWS ElastiCache
REDIS_URL=redis://prod-redis.xxxxx.cache.amazonaws.com:6379/0

# With Authentication
REDIS_URL=redis://:password@redis:6379/0

# TLS Connection
REDIS_URL=rediss://:password@redis:6379/0
```

### Cache Expiration

```env
CACHE_DEFAULT_EXPIRE=3600                  # Default TTL: 1 hour
CACHE_SHORT_EXPIRE=300                     # Short TTL: 5 minutes
CACHE_LONG_EXPIRE=86400                    # Long TTL: 1 day
```

**Use Cases:**
- `CACHE_SHORT_EXPIRE`: Real-time metrics, hot data
- `CACHE_DEFAULT_EXPIRE`: Dashboard data, API responses
- `CACHE_LONG_EXPIRE`: User profiles, store settings

---

## Message Queue Configuration

### Kafka Brokers

```env
KAFKA_BROKERS=kafka:9092                   # Comma-separated broker list
KAFKA_CONSUMER_GROUP=neurocommerce-group   # Consumer group name
```

**Examples:**

```env
# Local Development
KAFKA_BROKERS=localhost:9092

# Docker Compose
KAFKA_BROKERS=kafka:9092

# Confluent Cloud
KAFKA_BROKERS=broker1.region.provider.confluent.cloud:9092,broker2.region.provider.confluent.cloud:9092

# AWS MSK
KAFKA_BROKERS=b-1.msk-cluster.xxxxx.kafka.us-east-1.amazonaws.com:9092,b-2.msk-cluster.xxxxx.kafka.us-east-1.amazonaws.com:9092
```

### Kafka Topics

Auto-created topics:
- `neurocommerce.events`: Customer behavior events
- `neurocommerce.decisions`: Agent decisions
- `neurocommerce.actions`: Executed actions (campaigns, discounts)
- `neurocommerce.billing`: Billing events

---

## Store & Multi-Tenancy Configuration

### ID Prefixes

```env
STORE_ID_PREFIX=store_
USER_ID_PREFIX=user_
SESSION_ID_PREFIX=sess_
CUSTOMER_ID_PREFIX=cust_
CART_ID_PREFIX=cart_
CAMPAIGN_ID_PREFIX=camp_
EXPERIMENT_ID_PREFIX=exp_
```

**Usage:** Helps identify resource type and improve debuggability.

Example IDs:
- `store_abc123def456`
- `user_xyz789abc123`
- `sess_prod789_session123`

### Store Plans

```env
DEFAULT_STORE_PLAN=starter                 # starter, pro, growth, enterprise
```

**Plan Tiers:**

| Plan | Agents | Events/Month | API Calls/Min | Price |
|------|--------|-------------|---------------|-------|
| starter | 3 | 10K | 100 | Free/Trial |
| pro | 5 | 100K | 1000 | $99/mo |
| growth | 7 | 1M | 10K | $299/mo |
| enterprise | 7 | Unlimited | Unlimited | Custom |

---

## ML & Agent Configuration

### ML Model Thresholds

These values control AI agent decision-making and ML model behavior.

```env
# Purchase Intent Prediction (0.0 - 1.0)
PURCHASE_PROBABILITY_THRESHOLD=0.6         # Trigger purchase incentives when probability > 0.6
ABANDONMENT_PROBABILITY_THRESHOLD=0.7      # Trigger recovery when abandonment probability > 0.7
CHURN_RISK_THRESHOLD=0.75                  # Flag customers for retention when > 0.75
```

**Interpretation:**
- Lower threshold → More aggressive recommendations (more actions)
- Higher threshold → Conservative (fewer but high-confidence actions)

### Discount Optimization

```env
MIN_DISCOUNT=0.0                           # Minimum discount (0%)
MAX_DISCOUNT=35.0                          # Maximum discount (35%)
DEFAULT_DISCOUNT=10.0                      # Default offer discount (10%)
```

**Agent Behavior:**
- Pricing Optimization Agent uses these bounds
- Respects margin constraints (won't go below cost)
- Learns optimal discounts based on conversion data

### Agent Confidence

```env
MIN_AGENT_CONFIDENCE=0.5                   # Execute if confidence > 0.5
OPTIMAL_AGENT_CONFIDENCE=0.75              # Target confidence level for logging
```

**Available Agents:**
- `behavior_intelligence`: Predict user intent
- `cart_recovery`: Recover abandoned carts
- `checkout_persuasion`: Increase checkout conversion
- `experimentation`: Run A/B tests
- `pricing_optimization`: Optimize discounts
- `recommendation`: Product recommendations
- `retention`: Prevent customer churn

---

## External Integrations

### Shopify Integration

```env
SHOPIFY_API_KEY=xxx                        # Get from Shopify Partner Dashboard
SHOPIFY_API_SECRET=xxx                     # Get from Shopify Partner Dashboard
SHOPIFY_SCOPES=read_orders,read_products,read_customers,read_checkouts,write_discounts
SHOPIFY_API_VERSION=2024-01                # Shopify API version
SHOPIFY_WEBHOOK_TIMEOUT=30                 # Webhook timeout in seconds
```

**Required Scopes:**
- `read_orders`: View store orders
- `read_products`: View products
- `read_customers`: View customer data
- `read_checkouts`: View checkout data
- `write_discounts`: Create discount codes

**Setup:**
1. Create Shopify app in Partner Dashboard
2. Set webhook URLs: `https://your-domain.com/api/v1/shopify/webhooks`
3. Copy API key and secret to `.env`

### Stripe Integration

```env
STRIPE_API_KEY=sk_live_xxx                 # Production: sk_live_*, Test: sk_test_*
STRIPE_WEBHOOK_SECRET=whsec_xxx            # From webhook endpoints
```

**For Development (Test Mode):**
```env
STRIPE_API_KEY=sk_test_xxx
STRIPE_WEBHOOK_SECRET=whsec_test_xxx
```

### OpenAI/ChatGPT Integration

```env
OPENAI_API_KEY=sk-xxx                      # Get from OpenAI API dashboard
OPENAI_MODEL=gpt-4                         # gpt-4, gpt-4-turbo, gpt-3.5-turbo
OPENAI_TEMPERATURE=0.7                     # Creativity: 0=deterministic, 2=creative
OPENAI_MAX_TOKENS=1000                     # Max tokens per request
```

**Model Comparison:**

| Model | Speed | Cost | Quality | Recommended Use |
|-------|-------|------|---------|-----------------|
| gpt-3.5-turbo | Fast | $ | Good | High volume |
| gpt-4-turbo | Medium | $$ | Excellent | Balanced |
| gpt-4 | Slow | $$$ | Best | High accuracy |

### SendGrid Email

```env
SENDGRID_API_KEY=SG_xxx                    # Get from SendGrid dashboard
SENDGRID_FROM_EMAIL=noreply@your-domain.com
```

### Twilio SMS

```env
TWILIO_ACCOUNT_SID=ACxxx                   # Twilio Account SID
TWILIO_AUTH_TOKEN=xxx                      # Auth Token
TWILIO_PHONE_NUMBER=+1234567890            # Twilio number for SMS
```

---

## Observability & Monitoring

### Prometheus Metrics

```env
PROMETHEUS_ENABLED=true                    # Enable Prometheus metrics
PROMETHEUS_PORT=9090                       # Metrics port
```

**Metrics Available:**
- API request latency, count, errors
- Cache hit/miss rates
- Database query performance
- Agent decision statistics
- Message queue lag

Access at: `http://localhost:9090`

### OpenTelemetry

```env
OTEL_ENABLED=false                         # Enable distributed tracing
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317
```

### ClickHouse Analytics

```env
CLICKHOUSE_URL=http://clickhouse:8123/neurocommerce
CLICKHOUSE_BATCH_SIZE=100                  # Batch inserts for performance
CLICKHOUSE_BATCH_TIMEOUT=5                 # Flush every 5 seconds
```

---

## CORS & Security

### Cross-Origin Configuration

```env
CORS_ORIGINS=http://localhost:3000,https://yourdomain.com
ALLOWED_HOSTS=localhost,127.0.0.1,neurocommerce.local
```

**Development:**
```env
CORS_ORIGINS=http://localhost:3000,http://localhost:3001,http://localhost:5173
ALLOWED_HOSTS=localhost,127.0.0.1
```

**Production:**
```env
CORS_ORIGINS=https://yourdomain.com,https://app.yourdomain.com
ALLOWED_HOSTS=yourdomain.com,app.yourdomain.com
```

---

## Rate Limiting & Performance

```env
DEFAULT_QUERY_LIMIT=100                    # Default results per query
MAX_QUERY_LIMIT=1000                       # Maximum allowed
DEFAULT_PAGE_SIZE=50                       # Pagination default
MAX_PAGE_SIZE=500                          # Pagination maximum

REQUEST_TIMEOUT=30                         # Request timeout in seconds
MAX_BATCH_SIZE=1000                        # Max event batch size
RATE_LIMIT_ENABLED=true                    # Enable rate limiting
RATE_LIMIT_REQUESTS_PER_MINUTE=100         # Per user per minute
```

---

## Production Deployment Checklist

### Security

- [ ] Set `ENVIRONMENT=production`
- [ ] Generate and set secure `JWT_SECRET_KEY` (min 32 chars)
- [ ] Use RS256 instead of HS256 for JWT
- [ ] Set all external API keys
- [ ] Use strong database password
- [ ] Enable SSL/TLS for all connections
- [ ] Configure CORS_ORIGINS to your domain only
- [ ] Set ALLOWED_HOSTS to your domain only

### Performance

- [ ] Configure Redis URL with authentication
- [ ] Enable Prometheus metrics
- [ ] Set up log aggregation (ELK, CloudWatch, etc.)
- [ ] Configure database connection pooling
- [ ] Use CDN for static assets
- [ ] Enable gzip compression

### Reliability

- [ ] Configure health checks
- [ ] Set up alerting for error rates
- [ ] Configure database backups
- [ ] Test disaster recovery procedures
- [ ] Document runbooks for common issues

### Compliance

- [ ] Encrypt database (RDS encryption, etc.)
- [ ] Enable audit logging
- [ ] Configure data retention policies
- [ ] Review and implement SOC 2 controls
- [ ] Test PCI-DSS compliance (for payment data)

---

## Example Configuration Files

### Local Development

```env
ENVIRONMENT=development
API_HOST=127.0.0.1
API_PORT=8000
API_LOG_LEVEL=debug

DATABASE_URL=postgresql://neurocommerce:password@localhost:5432/neurocommerce
REDIS_URL=redis://localhost:6379/0
KAFKA_BROKERS=localhost:9092

JWT_SECRET_KEY=dev-secret-key-change-in-production
JWT_EXPIRATION_HOURS=24

CORS_ORIGINS=http://localhost:3000,http://localhost:3001
ALLOWED_HOSTS=localhost,127.0.0.1

SHOPIFY_API_KEY=dev-api-key
SHOPIFY_API_SECRET=dev-api-secret

OPENAI_API_KEY=sk-test-xxx
```

### Docker Compose Development

```env
ENVIRONMENT=development
API_HOST=0.0.0.0
API_PORT=8000

DATABASE_URL=postgresql://neurocommerce:password@postgres:5432/neurocommerce
REDIS_URL=redis://redis:6379/0
KAFKA_BROKERS=kafka:9092

JWT_SECRET_KEY=docker-dev-secret-key

CORS_ORIGINS=http://localhost:3000
ALLOWED_HOSTS=localhost,127.0.0.1
```

### Staging Environment

```env
ENVIRONMENT=staging
API_HOST=0.0.0.0
API_PORT=8000
API_LOG_LEVEL=info

DATABASE_URL=postgresql://user:password@staging-db.example.com:5432/neurocommerce
REDIS_URL=redis://:password@staging-cache.example.com:6379/0
KAFKA_BROKERS=kafka1.staging.example.com:9092,kafka2.staging.example.com:9092

JWT_SECRET_KEY=<secure-random-key>
JWT_ALGORITHM=RS256
JWT_EXPIRATION_HOURS=12

CORS_ORIGINS=https://staging.yourdomain.com
ALLOWED_HOSTS=staging.yourdomain.com

STRIPE_API_KEY=sk_test_xxx
SHOPIFY_API_KEY=staging-key
OPENAI_API_KEY=sk-xxx

PROMETHEUS_ENABLED=true
```

### Production Environment

```env
ENVIRONMENT=production
API_HOST=0.0.0.0
API_PORT=8000
API_LOG_LEVEL=warning

DATABASE_URL=postgresql://user:password@prod-db.example.com:5432/neurocommerce?sslmode=require
REDIS_URL=rediss://:password@prod-cache.example.com:6379/0?ssl_cert_reqs=required
KAFKA_BROKERS=kafka1.prod.example.com:9092,kafka2.prod.example.com:9092,kafka3.prod.example.com:9092

JWT_SECRET_KEY=<secure-random-key-min-32-chars>
JWT_ALGORITHM=RS256
JWT_EXPIRATION_HOURS=12

CORS_ORIGINS=https://yourdomain.com,https://app.yourdomain.com
ALLOWED_HOSTS=yourdomain.com,app.yourdomain.com

STRIPE_API_KEY=sk_live_xxx
SHOPIFY_API_KEY=prod-key
OPENAI_API_KEY=sk-prod-xxx

PROMETHEUS_ENABLED=true
OTEL_ENABLED=true

RATE_LIMIT_REQUESTS_PER_MINUTE=1000
```

---

## Troubleshooting

### Configuration Not Taking Effect

1. Ensure `.env` file is in the root directory
2. Restart the application (environment variables loaded at startup)
3. Check if value is overridden in code

### Database Connection Errors

```bash
# Test connection
psql "postgresql://user:password@host:5432/database"

# Check URL format
# postgresql://[user[:password]@][host][:port][/dbname]
```

### Redis Connection Issues

```bash
# Test Redis connection
redis-cli -h localhost -p 6379 ping
# Should return: PONG
```

### SSL/TLS Certificate Issues

For production databases:
```env
DATABASE_URL=postgresql://user:password@host:5432/db?sslmode=require
```

For Redis with TLS:
```env
REDIS_URL=rediss://:password@host:6379/0?ssl_cert_reqs=required
```

---

## Configuration Validation

The system validates critical settings on startup:

```python
# From backend/api/config.py
def validate_config():
    # Checks JWT secret in production
    # Validates API keys for production
    # Ensures database connectivity
```

To manually validate:

```bash
# Docker
docker-compose exec api python -c "from backend.api.config import validate_config; validate_config()"

# Local
python -c "from backend.api.config import validate_config; validate_config()"
```

---

## Need Help?

- Check logs: `docker-compose logs api`
- View this file: `CONFIGURATION.md`
- See example `.env.example`
- Review API docs: `http://localhost:8000/docs`
