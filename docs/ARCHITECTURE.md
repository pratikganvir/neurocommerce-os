# NeuroCommerce OS Architecture

## System Overview

NeuroCommerce OS is a production-grade AI Revenue Operating System for ecommerce. It autonomously increases revenue through intelligent agents that optimize every step of the customer journey.

### High-Level Data Flow

```
Merchant Store
    ↓
JavaScript Tracking SDK (neurocommerce.js)
    ↓
Event Ingestion API (/api/v1/events)
    ↓
Kafka Event Streaming
    ├→ user_behavior_events topic
    ├→ shopify_events topic
    ├→ agent_actions topic
    └→ conversion_events topic
    ↓
Event Workers (Kafka Consumers)
    ↓
Agent Orchestrator
    ├→ Behavior Intelligence Agent
    ├→ Checkout Persuasion Agent
    ├→ Cart Recovery Agent
    ├→ Pricing Optimization Agent
    ├→ Recommendation Agent
    ├→ Retention Agent
    └→ Experimentation Agent
    ↓
Execution Layer
    ├→ Email (SendGrid)
    ├→ SMS (Twilio)
    ├→ WhatsApp (Twilio)
    ├→ In-app Banners/Popups
    └→ Coupon Generation (Shopify)
    ↓
Merchant Dashboard (Analytics & Campaign Management)
```

## Core Components

### 1. Tracking SDK (`sdk/js-tracking-sdk/`)

**Purpose**: Collect user behavior data from merchant stores

**Key Features**:
- Automatic event tracking (page views, product views, scrolls, clicks)
- Exit intent detection
- Mouse movement tracking
- Event batching (configurable batch size)
- Automatic retry with exponential backoff
- Client-side caching

**Usage**:
```html
<script src="https://cdn.neurocommerce.io/neurocommerce.js"></script>
<script>
  window.neurocommerce = new NeuroCommerceSDK({
    apiKey: 'sk_live_xxx',
    customerId: 'optional_customer_id',
    enableAutoTrack: true
  });
</script>
```

### 2. Event Ingestion API (`backend/api/`)

**FastAPI-based REST API** handling:

- **Authentication**: JWT + API Keys
- **Event Ingestion**: `/api/v1/events/batch`, `/api/v1/events/track`
- **Auth**: `/api/v1/auth/login`, `/api/v1/auth/register`
- **Shopify Webhooks**: `/api/v1/shopify/webhooks/*`
- **Campaign Management**: `/api/v1/campaigns`
- **Experiments**: `/api/v1/experiments`
- **Billing**: `/api/v1/billing`

**Database**:
- **PostgreSQL**: Transactional data (stores, customers, sessions, carts, agent actions)
- **ClickHouse**: Analytical queries (events, metrics, funnels)
- **Redis**: Caching, rate limiting, session state

### 3. Event Streaming (`backend/workers/`)

**Kafka Topics**:
- `user_behavior_events`: Page views, product views, clicks, scrolls
- `shopify_events`: Orders, customers, products from Shopify webhooks
- `checkout_hesitation`: Detected checkout hesitation
- `cart_abandoned`: Cart abandonment detection
- `agent_actions`: Agent decisions to execute
- `conversion_events`: Purchase completions

**Workers**: Consume events asynchronously and trigger agent orchestration

### 4. AI Agent Architecture (`backend/agents/` + `backend/orchestration/`)

Six specialized agents make autonomous revenue decisions:

#### 4a. Behavior Intelligence Agent
- **Predicts**: Purchase probability, abandonment risk, intent class
- **Models**: Gradient boosted trees, behavior embeddings
- **Inputs**: Page views, scroll depth, time on site, device, traffic source
- **Output**: purchase_probability (0-1), abandonment_probability (0-1), intent_class (high/medium/low)

#### 4b. Checkout Persuasion Agent
- **Purpose**: Real-time conversion optimization during checkout
- **Latency**: <200ms
- **Actions**:
  - `coupon_offer`: Discount code
  - `social_proof`: "50,000 customers already bought"
  - `urgency_banner`: "Only 3 left in stock"
  - `bundle_suggestion`: Product bundle
  - `free_shipping`: Shipping incentive
- **Logic**: Higher abandonment risk → more aggressive persuasion

#### 4c. Cart Recovery Agent
- **Triggers**: After cart abandonment (24+ hours without checkout)
- **Channels**: Email (primary), SMS (secondary), WhatsApp (opt-in), Push
- **Campaign Schedule**:
  - 1 hour: Reminder email
  - 24 hours: Personal message with incentive
  - 72 hours: Last chance (SMS/WhatsApp)

#### 4d. Pricing Optimization Agent
- **Determines**: Optimal discount percentage
- **Formula**: 
  ```
  discount = (abandonment_prob × 0.25) + (price_sensitivity × 0.15) - (LTV_penalty)
  ```
- **Output**: discount_percentage (0-35%), coupon_code, expected_conversion_lift

#### 4e. Recommendation Agent
- **Techniques**:
  - Collaborative filtering ("customers who bought X also bought Y")
  - Embedding similarity (product vectors)
  - Frequently bought together
  - Best sellers in category
- **Output**: [product_id1, product_id2, ...], confidence score

#### 4f. Retention Agent
- **Triggers**: After purchase
- **Actions**:
  - Replenishment reminders (7 days before expected reorder)
  - Cross-sell campaigns (complementary products)
  - Loyalty perks (VIP discounts for high-LTV customers)
  - Win-back campaigns (inactive customers, churn risk > 0.7)

#### 4g. Experimentation Agent
- **Algorithm**: Thompson sampling (multi-armed bandit)
- **Experiments**:
  - Discount sizes (5%, 10%, 15%, 20%)
  - Checkout copy (different persuasion messages)
  - Offer timing (when to show offers)
  - Offer types (discount vs free shipping)
- **Auto-optimization**: Allocates more traffic to winning variants

### 5. Agent Orchestrator (`backend/orchestration/orchestrator.py`)

**Responsibilities**:
1. **Receive** events from Kafka
2. **Invoke** relevant agents in parallel
3. **Rank** decisions by expected value
4. **Execute** best action
5. **Record** decisions and outcomes

**Decision Ranking Formula**:
```
expected_value = confidence × conversion_lift × revenue_impact
best_action = argmax(expected_value)
```

### 6. Execution Layer

Implements agent actions across channels:

- **Email**: SendGrid integration
- **SMS**: Twilio integration
- **WhatsApp**: Twilio WhatsApp API
- **Website**: In-app banners, popups
- **Shopify**: Create coupons, apply discounts

### 7. ML Inference Service (`ml/inference/`)

**Real-time predictions** for:
- Behavior classification (purchase_probability)
- Product recommendations
- Churn prediction
- Customer segment classification

**Models**:
- Gradient Boosting (XGBoost)
- Random Forest
- Neural embeddings

### 8. Merchant Dashboard (`frontend/dashboard/`)

**Next.js + React** interface for merchants to:

- **Overview**: Revenue, conversions, AOV, recovered revenue
- **Agent Decisions**: See all agent actions and outcomes
- **Recovery Campaigns**: Manage cart recovery campaigns
- **Customer Journeys**: Visualize customer paths
- **Experiments**: Create and monitor A/B tests
- **Settings**: Store configuration, integrations

### 9. Shopify Integration

**OAuth Flow**:
1. Merchant installs NeuroCommerce app
2. OAuth callback: `/api/v1/shopify/oauth/callback`
3. Access token stored securely

**Webhooks** (HMAC validated):
- `checkout/create`: New checkout detected
- `checkout/update`: Checkout updated (items/prices changed)
- `orders/create`: Order created
- `orders/paid`: Payment confirmed
- `carts/create`: Cart created

**Discount Creation**: Create coupon codes via Shopify API

## Multi-Tenant Architecture

**Tenant Isolation**:
- Each store has unique `store_id`
- All queries filtered by `store_id` (database level)
- Separate Stripe customer records
- Isolated Kafka partitioning

**Row-Level Security**:
- PostgreSQL policies enforce store_id filtering
- API keys scoped to specific stores
- JWT tokens contain store_id claim

## Data Schema

### Key Tables

```sql
-- Stores
stores (id PK, domain, shopify_store_id, plan, subscription_status)

-- Users
users (id PK, store_id FK, email, role, password_hash)

-- Customers
customers (id PK, store_id FK, shopify_customer_id, email, lifetime_value, churn_risk)

-- Sessions
sessions (id PK, store_id FK, customer_id FK, page_views, product_views, purchase_probability, abandonment_probability)

-- Carts
carts (id PK, store_id FK, session_id FK, cart_value, status, items JSON)

-- Events (analytical)
events (id PK, session_id FK, event_type, event_data JSON, created_at)

-- Agent Actions
agent_actions (id PK, store_id FK, session_id, agent_type, action, executed, converted, confidence)

-- Experiments
experiments (id PK, store_id FK, status, variants JSON, allocation JSON, winner)

-- Campaigns
campaigns (id PK, store_id FK, type, status, sent_count, converted_count, revenue_generated)
```

## Performance Characteristics

### Latency Requirements

- **Event Ingestion**: <100ms (p95)
- **Checkout Persuasion**: <200ms (p99)
- **ML Inference**: <300ms (p95)
- **Dashboard Load**: <2s (p95)

### Throughput

- **Events**: 100k+ events/second across all stores
- **Concurrent Sessions**: 10,000+ concurrent active sessions
- **Orders**: 1,000+ orders/minute during peak

### Scaling

- **Horizontal**: API, workers, inference services
- **Vertical**: PostgreSQL read replicas, ClickHouse sharding
- **Storage**: S3 for model artifacts, event backups

## Security

- **JWT Authentication**: Signed tokens with 24-hour expiry
- **API Keys**: Store-scoped, can be revoked
- **RBAC**: admin, editor, viewer roles
- **PII Encryption**: Customer emails/phones encrypted at rest
- **Webhook Validation**: HMAC-SHA256 signature verification
- **Rate Limiting**: Per-API-key limits
- **CORS**: Configurable allowed origins

## Monitoring & Observability

- **Metrics**: Prometheus, Grafana dashboards
- **Tracing**: OpenTelemetry distributed tracing
- **Logs**: Structured JSON logs (ELK stack optional)
- **Alerts**: Agent decision anomalies, conversion drops, latency spikes

## Deployment

### Local Development
```bash
docker-compose up  # All services
```

### Kubernetes
```bash
kubectl apply -f infrastructure/k8s/
```

### AWS (Terraform)
```bash
terraform apply -var-file=prod.tfvars
```

## Cost Model

- **Base**: $99/month (starter)
- **Usage**: $0.01/event, $0.10/email, $0.05/SMS
- **Revenue Share**: 5% of incremental revenue for Pro+

---

For deployment and API documentation, see respective guides.
