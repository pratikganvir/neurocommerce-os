# NeuroCommerce OS - Start Here 👋

Welcome to **NeuroCommerce OS** - a production-grade AI Revenue Operating System for ecommerce stores.

This document guides you through the project and helps you get started quickly.

---

## 🚀 Getting Started (Choose One)

### Option 1: Quick Start (5 minutes) ⚡
If you just want to see it running:
```bash
./scripts/start-local.sh
```
Then open http://localhost:3000

**→ Read: [QUICKSTART.md](QUICKSTART.md)**

---

### Option 2: Understand the System (20 minutes) 📚
If you want to understand how everything works:
1. Read [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md) - High-level overview
2. Read [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) - Detailed design
3. Explore the code in `/backend/agents/`

**→ Read: [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md) first**

---

### Option 3: Deploy to Production (1 hour) 🌐
If you want to deploy to production:
1. Read [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)
2. Choose your deployment option (Kubernetes or AWS Terraform)
3. Follow the step-by-step instructions

**→ Read: [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)**

---

## 📋 What's Included

### Core Platform
- ✅ **7 AI Agents** - Autonomous decision-making for revenue optimization
- ✅ **FastAPI Backend** - Production-grade REST API
- ✅ **Event Streaming** - Real-time Kafka-based architecture
- ✅ **Next.js Dashboard** - Merchant analytics and controls
- ✅ **JavaScript SDK** - Lightweight event tracking (15KB, zero dependencies)
- ✅ **Multi-Tenant** - Complete isolation between stores

### Infrastructure
- ✅ **Docker Compose** - Local development (all services)
- ✅ **Kubernetes** - Production deployment manifests
- ✅ **Terraform** - AWS infrastructure as code
- ✅ **Monitoring** - Prometheus + Grafana dashboards

### Documentation
- ✅ **QUICKSTART.md** - 5-minute setup guide
- ✅ **API.md** - Complete API reference
- ✅ **SDK.md** - JavaScript SDK documentation
- ✅ **ARCHITECTURE.md** - Detailed system design
- ✅ **DEPLOYMENT.md** - Production deployment guide
- ✅ **PROJECT_SUMMARY.md** - Complete project overview

### Testing
- ✅ **Unit Tests** - Core functionality tests
- ✅ **Integration Tests** - End-to-end flow tests
- ✅ **Test Coverage** - Models, APIs, agents, webhooks, multi-tenancy

---

## 📚 Documentation Map

```
START HERE
    ↓
[QUICKSTART.md] ← Want to run it now?
    ↓
[PROJECT_SUMMARY.md] ← Want the full picture?
    ↓
    ├─→ [docs/ARCHITECTURE.md] ← How does it work?
    ├─→ [docs/API.md] ← API reference?
    ├─→ [docs/SDK.md] ← Embedding the SDK?
    ├─→ [docs/DEPLOYMENT.md] ← Deploy to production?
    └─→ [docs/REQUIREMENTS.md] ← What are the requirements?
```

---

## 🎯 7 AI Agents Explained

### 1. **Behavior Intelligence** 🧠
Predicts what customers will do next:
- Purchase probability (0-100%)
- Abandonment risk (0-100%)
- Intent classification (browser, buyer, converter)

**Example Decision**: "This customer has 85% chance of buying - show persuasion offer"

### 2. **Checkout Persuasion** 💰
Real-time conversion optimization at checkout (<200ms):
- Coupon offers ("Save 10%")
- Social proof ("1,234 recently bought")
- Urgency ("Only 3 left in stock")
- Bundle suggestions ("Add this for $5 more")
- Free shipping ("Free shipping on orders over $50")

**Example Decision**: "Show $5 off coupon to complete checkout"

### 3. **Cart Recovery** 🛒
Recovers abandoned carts with multi-channel strategy:
- Wave 1 (1 hour): "Your cart is waiting"
- Wave 2 (24 hours): "10% off if you complete now"
- Wave 3 (72 hours): "Last chance! Your items are running out"
- Channels: Email, SMS, Push, WhatsApp

**Example Decision**: "Send SMS reminder with 15% off code"

### 4. **Pricing Optimization** 💵
Dynamic discounts based on customer value:
- Formula: `discount = (abandonment_risk × 0.25) + (price_sensitivity × 0.15) - LTV_penalty`
- Don't discount VIP customers (high LTV)
- Test different discount levels with A/B tests

**Example Decision**: "Offer 5% discount to price-sensitive customer"

### 5. **Recommendation Engine** 🎁
Personalized product recommendations:
- Collaborative filtering (people like you bought...)
- Item embeddings (semantically similar products)
- Real-time trending (what's popular now)
- Cached for 24 hours

**Example Decision**: "Recommend complementary products based on cart"

### 6. **Retention Agent** 📈
Keep customers coming back:
- Replenishment ("Time to reorder your favorite product")
- Cross-sell ("You might like these related items")
- Loyalty ("You earned 500 points - redeem them")
- Win-back ("We miss you - here's 20% off")

**Example Decision**: "Send replenishment email for frequently purchased item"

### 7. **Experimentation** 🧪
Optimizes all decisions through A/B testing:
- Thompson sampling multi-armed bandit
- Automatic variant assignment
- Real-time statistical analysis
- Picks winning variants automatically

**Example Decision**: "Customer gets variant A of pricing test (20% off)"

---

## 🏗️ System Architecture

```
┌─────────────────────────────────┐
│   Merchant's Ecommerce Store    │
│   (Shopify, WooCommerce, etc.)  │
└──────────────┬──────────────────┘
               │
        [NeuroCommerce SDK]
        (15KB, zero deps)
               │
               ▼
┌─────────────────────────────────┐
│      NeuroCommerce API (Port 8000)
│      (FastAPI, Python)          │
│  • Authenticates requests       │
│  • Ingests events               │
│  • Handles Shopify webhooks     │
└──────────────┬──────────────────┘
               │
               ▼ (publish events)
┌─────────────────────────────────┐
│    Apache Kafka                 │
│    (Event Streaming)            │
│  • user_behavior_events         │
│  • shopify_events               │
│  • agent_actions                │
│  • conversion_events            │
└──────────────┬──────────────────┘
               │
               ▼ (consume events)
┌─────────────────────────────────┐
│  7 AI Agents (Decision Making)  │
│                                 │
│  Behavior    │  Persuasion      │
│  Recovery    │  Pricing         │
│  Recommend   │  Retention       │
│  Experiment  │                  │
└──────────────┬──────────────────┘
               │
         (record & execute)
               ▼
┌─────────────────────────────────┐
│   PostgreSQL (Transactional)    │
│   ClickHouse (Analytics)        │
│   Redis (Cache)                 │
└──────────────┬──────────────────┘
               │
               ▼
┌─────────────────────────────────┐
│  Merchant Dashboard (Port 3000) │
│  (Next.js, React)               │
│  • KPI metrics                  │
│  • Agent insights               │
│  • Campaign performance         │
│  • A/B test results             │
└─────────────────────────────────┘
```

---

## 🔧 Quick Command Reference

### Start Everything
```bash
./scripts/start-local.sh
```

### View Logs
```bash
docker-compose logs -f api                    # API logs
docker-compose logs -f                        # All services
```

### Run Tests
```bash
docker-compose exec api pytest tests/ -v     # Run all tests
docker-compose exec api pytest tests/unit/ -v # Unit tests only
```

### Access Database
```bash
docker-compose exec postgres psql -U postgres -d neurocommerce
```

### Stop Services
```bash
docker-compose down                           # Stop (keep data)
docker-compose down -v                        # Stop and remove everything
```

### View Dashboard
```
http://localhost:3000  # Merchant dashboard
http://localhost:8000/docs  # API documentation (Swagger)
http://localhost:3001  # Grafana monitoring (admin/admin)
```

---

## 📖 Reading Guide

### For Merchants
1. **[QUICKSTART.md](QUICKSTART.md)** - Get it running
2. **[docs/SDK.md](docs/SDK.md)** - Embed in your store
3. **[docs/API.md](docs/API.md)** - Create campaigns

### For Developers
1. **[PROJECT_SUMMARY.md](PROJECT_SUMMARY.md)** - Overview
2. **[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)** - Deep dive
3. **Code**: Start with `backend/api/main.py`

### For DevOps/SRE
1. **[docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)** - Production deployment
2. **[docs/REQUIREMENTS.md](docs/REQUIREMENTS.md)** - System requirements
3. **Terraform**: `infrastructure/terraform/main.tf`

### For Data Scientists
1. **`backend/agents/`** - Agent implementations
2. **`ml/training/train.py`** - Model training
3. **`ml/inference/app.py`** - Inference service

---

## 🎯 Common Tasks

### How do I...?

**...embed the SDK in my store?**
→ [docs/SDK.md](docs/SDK.md) - Full integration guide

**...create a marketing campaign?**
→ [docs/API.md](docs/API.md#campaigns) - Campaign endpoint

**...run an A/B test?**
→ [docs/API.md](docs/API.md#experiments) - Experiment endpoint

**...deploy to production?**
→ [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) - Deployment guide

**...scale to 100k concurrent users?**
→ [docs/DEPLOYMENT.md#scaling](docs/DEPLOYMENT.md) - Scaling guide

**...understand how pricing optimization works?**
→ [docs/ARCHITECTURE.md#pricing-agent](docs/ARCHITECTURE.md) - Agent details

**...run the tests?**
→ [QUICKSTART.md#running-tests](QUICKSTART.md#running-tests) - Test guide

**...check the API reference?**
→ [docs/API.md](docs/API.md) - Full API documentation

---

## 💡 Key Concepts

### Multi-Tenancy
Each merchant's store is completely isolated. One API server can handle thousands of stores safely.

### Event-Driven
All customer actions (page view, click, add to cart, etc.) are published as events. Agents subscribe to these events and make decisions.

### Real-Time
Agents make decisions in milliseconds. The "Checkout Persuasion" agent decides what offer to show in <200ms.

### AI-First
Instead of fixed rules, each agent learns what works best through Thompson sampling (multi-armed bandit optimization).

### Production-Ready
The system is designed for scale: 100k+ events/second, 10k+ concurrent sessions, $1M+ daily revenue.

---

## 📊 By The Numbers

| Metric | Value |
|--------|-------|
| **Total Code** | 15,000+ lines |
| **Files Created** | 50+ |
| **AI Agents** | 7 |
| **Database Models** | 14 |
| **API Endpoints** | 15+ |
| **Event Topics** | 6 |
| **Docker Services** | 12 |
| **Documentation** | 1,500+ lines |
| **Test Coverage** | 500+ lines of tests |

---

## 🚀 Next Steps

**Pick your path:**

1. **I want to see it running** (5 min)
   ```bash
   ./scripts/start-local.sh
   open http://localhost:3000
   ```

2. **I want to understand the system** (20 min)
   - Read [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md)
   - Read [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)

3. **I want to deploy to production** (1 hour)
   - Read [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)
   - Run Terraform or Kubernetes

4. **I want to embed in my store** (30 min)
   - Read [docs/SDK.md](docs/SDK.md)
   - Grab API key and embed SDK

5. **I want to integrate with Stripe** (1 hour)
   - Configure Stripe keys in `.env`
   - Read [docs/API.md](docs/API.md#billing) - Billing endpoints

---

## 📞 Get Help

- **Quick Questions**: Check [QUICKSTART.md](QUICKSTART.md)
- **How Something Works**: Check [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
- **API Questions**: Check [docs/API.md](docs/API.md)
- **Deployment Issues**: Check [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)
- **Code Issues**: Check the relevant source file

---

## 📄 License

MIT License - See LICENSE file

---

**Ready? Let's go! 🚀**

**Recommended first step:** Run `./scripts/start-local.sh` and open http://localhost:3000
