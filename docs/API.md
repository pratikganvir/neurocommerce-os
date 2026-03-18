# API Reference

## Authentication

All API endpoints require either:
1. JWT token in `Authorization: Bearer <token>` header
2. API key in `api-key` header

### Login

```bash
POST /api/v1/auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "password"
}
```

**Response**:
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer",
  "user_id": "user_123",
  "store_id": "store_123"
}
```

### Register

```bash
POST /api/v1/auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "password",
  "name": "John Doe",
  "store_name": "My Store"
}
```

## Event Tracking

### Batch Event Ingestion

Track multiple events in a single request:

```bash
POST /api/v1/events/batch
Content-Type: application/json
api-key: sk_live_xxx

{
  "session_id": "sess_123",
  "customer_id": "cust_123",
  "events": [
    {
      "event_type": "page_view",
      "event_data": {
        "path": "/products",
        "title": "Products"
      },
      "timestamp": "2024-01-14T12:00:00Z"
    },
    {
      "event_type": "product_view",
      "event_data": {
        "product_id": "prod_123",
        "product_name": "Widget",
        "price": 49.99
      }
    }
  ]
}
```

**Response**:
```json
[
  {"event_id": "event_123", "status": "queued"},
  {"event_id": "event_124", "status": "queued"}
]
```

### Single Event

```bash
POST /api/v1/events/track?session_id=sess_123
Content-Type: application/json
api-key: sk_live_xxx

{
  "event_type": "click",
  "event_data": {
    "element": "button",
    "label": "Buy Now"
  }
}
```

## Agent Decisions

### Get Agent Decisions

```bash
GET /api/v1/agents/decisions/{store_id}?agent_type=checkout_persuasion&limit=100
Authorization: Bearer <token>
```

**Response**:
```json
[
  {
    "id": "action_123",
    "agent_type": "checkout_persuasion",
    "action": "coupon_offer",
    "action_details": {
      "coupon_code": "SAVE10",
      "discount_percent": 10
    },
    "confidence": 0.85,
    "created_at": "2024-01-14T12:00:00Z"
  }
]
```

### Agent Statistics

```bash
GET /api/v1/agents/stats/{store_id}
Authorization: Bearer <token>
```

**Response**:
```json
{
  "total_decisions": 1250,
  "executed": 1200,
  "delivered": 1150,
  "converted": 287,
  "conversion_rate": 0.229,
  "avg_confidence": 0.78,
  "by_agent_type": {
    "checkout_persuasion": 450,
    "cart_recovery": 380,
    "recommendation": 420
  }
}
```

## Campaigns

### Create Campaign

```bash
POST /api/v1/campaigns
Content-Type: application/json
Authorization: Bearer <token>

{
  "name": "Cart Recovery Campaign",
  "campaign_type": "cart_recovery",
  "target_segment": "abandoned_carts",
  "channels": ["email", "sms"],
  "message_template": "Your cart is waiting! Complete your order and get 10% off."
}
```

### Get Campaigns

```bash
GET /api/v1/campaigns/{store_id}?status=running
Authorization: Bearer <token>
```

## Experiments

### Create Experiment

```bash
POST /api/v1/experiments/{store_id}
Content-Type: application/json
Authorization: Bearer <token>

{
  "name": "Discount Size Test",
  "experiment_type": "discount",
  "control_variant": {
    "name": "Control (10% off)",
    "discount_percent": 10
  },
  "test_variants": [
    {
      "name": "Variant A (15% off)",
      "discount_percent": 15
    },
    {
      "name": "Variant B (20% off)",
      "discount_percent": 20
    }
  ],
  "allocation": {
    "control": 0.33,
    "variant_a": 0.33,
    "variant_b": 0.34
  },
  "duration_days": 7
}
```

### Get Experiments

```bash
GET /api/v1/experiments/{store_id}?status=running
Authorization: Bearer <token>
```

## Billing

### Get Billing Information

```bash
GET /api/v1/billing/{store_id}
Authorization: Bearer <token>
```

**Response**:
```json
{
  "current_plan": "pro",
  "subscription_status": "active",
  "stripe_customer_id": "cus_123",
  "usage": {
    "api_calls": 150000,
    "emails_sent": 45000,
    "sms_sent": 12000,
    "agent_decisions": 23000
  }
}
```

## Shopify Integration

### OAuth Callback

```bash
GET /api/v1/shopify/oauth/callback?code=AUTHORIZATION_CODE&shop=myshop.myshopify.com
```

### Webhooks (Incoming)

Shopify will POST to these endpoints:

```
POST /api/v1/shopify/webhooks/checkout/create
POST /api/v1/shopify/webhooks/checkout/update
POST /api/v1/shopify/webhooks/orders/create
POST /api/v1/shopify/webhooks/orders/paid
POST /api/v1/shopify/webhooks/carts/create
```

All webhook requests are HMAC-SHA256 signed. Verify signature:
```python
import hmac
import hashlib
import base64

signature = request.headers.get('X-Shopify-Hmac-SHA256')
expected = base64.b64encode(
    hmac.new(
        SECRET.encode(),
        request.body,
        hashlib.sha256
    ).digest()
).decode()

assert hmac.compare_digest(signature, expected)
```

## Health Check

```bash
GET /health
```

**Response**:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "database": "healthy",
  "cache": "healthy"
}
```

---

## Error Responses

All errors follow this format:

```json
{
  "detail": "Error message",
  "status_code": 400
}
```

Common error codes:
- `400`: Bad Request
- `401`: Unauthorized (invalid token/key)
- `403`: Forbidden (insufficient permissions)
- `404`: Not Found
- `422`: Unprocessable Entity (validation error)
- `429`: Too Many Requests (rate limited)
- `500`: Internal Server Error

---

For more information, see [Architecture Guide](ARCHITECTURE.md) and [SDK Documentation](SDK.md)
