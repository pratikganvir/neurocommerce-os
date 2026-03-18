# ML Data Pipeline Documentation

## Overview

Complete ML training data collection and export system for NeuroCommerce OS. Ensures all event data, store configurations, and customer information is captured in ClickHouse for analytics and model training.

**Status:** ✅ Implementation complete - ready for integration

## Architecture

### Data Flow

```
PostgreSQL Events API
        ↓
Event Ingestion (/events/batch endpoint)
        ↓
    PostgreSQL Storage (Event table)
        ├─→ Kafka (real-time processing)
        └─→ ML Data Pipeline Service
                ↓
        Feature Enrichment (add context)
                ↓
        ClickHouse Analytics DB
                ├─→ Analytics Queries
                └─→ Training Dataset Export
                        ↓
                ML Model Training
```

### Components

| Component | File | Purpose |
|-----------|------|---------|
| **Pipeline Service** | `backend/services/ml_data_pipeline.py` | Central coordinator for all ML data flows |
| **ClickHouse Client** | `backend/services/clickhouse_client.py` | Database interface for analytics storage |
| **Data Export** | `backend/ml/data_export.py` | Feature engineering and dataset export |

## Services

### 1. ML Data Pipeline Service

**File:** `backend/services/ml_data_pipeline.py`

Central service that ensures all event data is properly captured and enriched for ML training.

#### Key Methods

##### `ingest_event()`
```python
async def ingest_event(
    event_id: str,
    session_id: str,
    store_id: str,
    event_type: str,
    event_data: Dict[str, Any],
    timestamp: datetime,
    db: Session
) -> None
```

**Purpose:** Process single event and send to all analytics pipelines

**Data Captured:**
- Event metadata (type, timestamp, IDs)
- Session context (page views, scroll depth, device)
- Customer context (LTV, segment, churn risk)
- Store context (plan, domain)

**Flow:**
1. Query enrichment data (session, customer, store)
2. Build enriched event JSON
3. Send to ClickHouse
4. Publish to Kafka (async processing)

**Example:**
```python
pipeline = get_ml_pipeline()
await pipeline.ingest_event(
    event_id="evt_123",
    session_id="sess_456",
    store_id="store_789",
    event_type="product_view",
    event_data={"product_id": "prod_001", "category": "shoes"},
    timestamp=datetime.utcnow(),
    db=db
)
```

##### `capture_agent_action()`
```python
async def capture_agent_action(
    action_id: str,
    session_id: str,
    store_id: str,
    agent_type: str,
    action: str,
    action_details: Dict[str, Any],
    confidence: float,
    db: Session
) -> None
```

**Purpose:** Record agent decisions and actions for supervised learning

**What It Tracks:**
- Which agent made the decision
- What action was recommended
- Confidence level of the decision
- Full action details (parameters, variants, etc)

**Why It Matters:**
- Enables feedback loop (action → outcome)
- Measures agent performance over time
- Identifies failing patterns
- Trains next generation of models

**Example:**
```python
await pipeline.capture_agent_action(
    action_id="act_123",
    session_id="sess_456",
    store_id="store_789",
    agent_type="checkout_persuasion",
    action="show_free_shipping_offer",
    action_details={
        "offer_type": "free_shipping",
        "min_cart_value": 50,
        "estimated_impact": 0.15
    },
    confidence=0.82,
    db=db
)
```

##### `capture_conversion()`
```python
async def capture_conversion(
    session_id: str,
    store_id: str,
    customer_id: str,
    cart_value: float,
    conversion_time: datetime,
    db: Session
) -> None
```

**Purpose:** Record purchase conversions (critical for training labels)

**Why Critical:**
- Creates training labels for conversion models
- Links sessions to outcomes
- Enables multi-touch attribution
- Measures agent effectiveness

**Example:**
```python
await pipeline.capture_conversion(
    session_id="sess_456",
    store_id="store_789",
    customer_id="cust_001",
    cart_value=250.00,
    conversion_time=datetime.utcnow(),
    db=db
)
```

##### `capture_store_metrics()`
```python
async def capture_store_metrics(
    store_id: str,
    db: Session
) -> None
```

**Purpose:** Capture aggregated store performance metrics

**Metrics Captured:**
- Customer count and avg LTV
- Campaign performance (open rate, conversion rate)
- Agent effectiveness by type
- Overall store health

**Frequency:** Called periodically (recommended: daily)

**Example:**
```python
await pipeline.capture_store_metrics(
    store_id="store_789",
    db=db
)
```

##### `export_training_dataset()`
```python
async def export_training_dataset(
    store_id: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    output_format: str = "csv"
) -> str
```

**Purpose:** Export training data for model training

**Supported Formats:**
- CSV (default)
- JSON
- Parquet

**Example:**
```python
filepath = await pipeline.export_training_dataset(
    store_id="store_789",
    start_date=datetime(2024, 1, 1),
    end_date=datetime(2024, 3, 31),
    output_format="csv"
)
# Returns: /tmp/training_data_2024-01-15T10:30:00.csv
```

##### `validate_data_quality()`
```python
async def validate_data_quality(
    store_id: Optional[str] = None
) -> Dict[str, Any]
```

**Purpose:** Check data completeness and quality

**Returns:**
```python
{
    "timestamp": "2024-01-15T10:30:00",
    "checks": {
        "total_events": 15234,
        "events_24h": 1256,
        "total_sessions": 5432,
        "sessions_with_customer": 4987,  # 91.8% coverage
        "total_customers": 2341,
        "customers_with_ltv": 2156,  # 92.1% coverage
        "total_agent_actions": 1234,
        "actions_with_outcome": 980,  # 79.4% coverage
    },
    "overall_quality_score": 0.854  # 85.4%
}
```

**Usage:**
```python
report = await pipeline.validate_data_quality(store_id="store_789")
if report["overall_quality_score"] < 0.8:
    logger.warning("Data quality below threshold")
```

### 2. ClickHouse Client

**File:** `backend/services/clickhouse_client.py`

Database interface for analytics and ML training data storage.

#### Tables Schema

##### `events` Table
```sql
CREATE TABLE events (
    event_id String,              -- Unique event ID
    session_id String,            -- Session identifier
    store_id String,              -- Merchant/store ID
    event_type String,            -- page_view, product_view, click, scroll, add_to_cart, etc.
    event_data String,            -- JSON payload
    customer_id Nullable(String), -- Customer identifier
    customer_ltv Nullable(Float64), -- Customer lifetime value
    customer_segment Nullable(String), -- vip, active, new, churned
    page_views UInt32,           -- Session page view count
    product_views UInt32,        -- Session product view count
    scroll_depth Float64,        -- Max scroll depth (0-1)
    time_on_site UInt32,         -- Session duration in seconds
    device Nullable(String),     -- mobile, desktop, tablet
    traffic_source Nullable(String), -- organic, direct, paid, social
    created_at DateTime          -- Event timestamp
) ENGINE = MergeTree()
ORDER BY (store_id, session_id, created_at)
PARTITION BY toYYYYMM(created_at)
```

**Usage in Analytics:**
```sql
-- Conversion rate by traffic source
SELECT traffic_source, COUNT(*) as events, 
       SUM(has_purchase) as purchases,
       SUM(has_purchase)/COUNT(*) as conversion_rate
FROM events
WHERE created_at >= subtractMonths(now(), 3)
GROUP BY traffic_source
ORDER BY conversion_rate DESC
```

##### `agent_actions` Table
```sql
CREATE TABLE agent_actions (
    action_id String,           -- Unique action ID
    session_id String,          -- Session identifier
    store_id String,            -- Merchant/store ID
    agent_type String,          -- Agent type (checkout_persuasion, retention, etc)
    action String,              -- Action name
    action_details String,      -- JSON with parameters
    confidence Float64,         -- Agent confidence (0-1)
    created_at DateTime         -- Action timestamp
) ENGINE = MergeTree()
ORDER BY (store_id, session_id, created_at)
PARTITION BY toYYYYMM(created_at)
```

**Usage in Analytics:**
```sql
-- Agent effectiveness by type
SELECT agent_type, COUNT(*) as actions,
       AVG(confidence) as avg_confidence
FROM agent_actions
WHERE created_at >= subtractMonths(now(), 1)
GROUP BY agent_type
ORDER BY actions DESC
```

##### `conversions` Table
```sql
CREATE TABLE conversions (
    session_id String,          -- Session identifier
    store_id String,            -- Merchant/store ID
    customer_id String,         -- Customer identifier
    conversion_value Float64,   -- Purchase amount
    conversion_time DateTime,   -- Conversion timestamp
    created_at DateTime         -- Record creation time
) ENGINE = MergeTree()
ORDER BY (store_id, created_at)
PARTITION BY toYYYYMM(created_at)
```

**Usage in Analytics:**
```sql
-- Daily revenue and conversion count
SELECT toDate(conversion_time) as date,
       COUNT(*) as orders,
       SUM(conversion_value) as revenue,
       AVG(conversion_value) as aov
FROM conversions
WHERE store_id = 'store_789'
  AND conversion_time >= subtractDays(now(), 90)
GROUP BY date
ORDER BY date DESC
```

##### `store_metrics` Table
```sql
CREATE TABLE store_metrics (
    store_id String,                -- Merchant/store ID
    store_plan String,              -- free, starter, growth, enterprise
    total_customers UInt32,         -- Total customer count
    avg_ltv Float64,               -- Average customer LTV
    total_revenue Float64,         -- Aggregated revenue
    total_campaigns UInt32,        -- Campaign count
    total_conversions UInt32,      -- Conversion count
    conversion_rate Float64,       -- Overall conversion rate
    total_agent_actions UInt32,    -- Total agent decisions
    agent_conversion_rate Float64, -- Agent-influenced conversion rate
    avg_agent_confidence Float64,  -- Average agent confidence
    created_at DateTime            -- Metric timestamp
) ENGINE = MergeTree()
ORDER BY (store_id, created_at)
PARTITION BY toYYYYMM(created_at)
```

**Usage in Analytics:**
```sql
-- Store performance comparison
SELECT store_id, store_plan,
       total_customers,
       avg_ltv,
       total_revenue,
       conversion_rate
FROM store_metrics
WHERE created_at = (SELECT max(created_at) FROM store_metrics)
ORDER BY total_revenue DESC
LIMIT 10
```

#### Methods

##### `create_tables()`
```python
await clickhouse.create_tables()
```

**Purpose:** Create all required ClickHouse tables

**Run Once:** During initial setup

##### `insert_event()`
```python
await clickhouse.insert_event(enriched_event)
```

**Called By:** ML Data Pipeline on every event

##### `insert_agent_action()`
```python
await clickhouse.insert_agent_action(action)
```

**Called By:** ML Data Pipeline on agent decisions

##### `insert_conversion()`
```python
await clickhouse.insert_conversion(conversion)
```

**Called By:** ML Data Pipeline on purchases

##### `insert_store_metrics()`
```python
await clickhouse.insert_store_metrics(metrics)
```

**Called By:** ML Data Pipeline periodically

##### `query_events()`
```python
results = await clickhouse.query_events(
    store_id="store_789",
    start_date=datetime(2024, 1, 1),
    end_date=datetime(2024, 3, 31),
    event_types=["product_view", "add_to_cart"],
    limit=10000
)
```

**Purpose:** Query events for analysis or export

##### `get_store_conversion_metrics()`
```python
metrics = await clickhouse.get_store_conversion_metrics(
    store_id="store_789",
    days=30
)
# Returns: {
#     "total_sessions": 5432,
#     "conversions": 432,
#     "conversion_rate": 0.0796,
#     "avg_order_value": 125.50,
#     "total_revenue": 54156.00
# }
```

### 3. Data Export Utilities

**File:** `backend/ml/data_export.py`

Feature engineering and training dataset creation.

#### Feature Engineer

**Purpose:** Transform raw events into ML-ready features

##### Session Features
```python
features = FeatureEngineer.extract_session_features(events, session_data)
# Returns:
{
    "page_views": 5,
    "product_views": 3,
    "scroll_depth": 0.75,
    "time_on_site": 300,
    "total_events": 12,
    "page_view_ratio": 0.417,
    "product_view_ratio": 0.25,
    "scroll_engagement": 0.75,
    "avg_time_per_page": 60,
    "add_to_cart_count": 1,
    "has_cart_action": 1,
    "has_purchase": 0
}
```

##### Customer Features
```python
features = FeatureEngineer.extract_customer_features(customer_data)
# Returns:
{
    "customer_ltv": 450.00,
    "total_orders": 3,
    "avg_order_value": 150.00,
    "churn_risk": 0.15,
    "is_vip": 0,
    "is_active": 1,
    "is_churned": 0,
    "is_new": 0,
    "ltv_high": 0,
    "ltv_medium": 1,
    "ltv_low": 0,
    "ltv_zero": 0
}
```

##### Store Features
```python
features = FeatureEngineer.extract_store_features(store_data)
# Returns:
{
    "store_id": "store_789",
    "plan_free": 0,
    "plan_starter": 1,
    "plan_growth": 0,
    "plan_enterprise": 0
}
```

#### Data Validator

**Purpose:** Ensure data quality before training

```python
is_valid, errors = DataValidator.validate_feature_set(features)
if not is_valid:
    print(f"Validation errors: {errors}")

report = DataValidator.validate_dataset(data)
print(f"Quality score: {report['quality_score']}")  # 0.854 = 85.4%
```

#### Training Data Exporter

**Purpose:** Export in various formats

```python
# Export to CSV
TrainingDataExporter.export_to_csv(data, "/tmp/training.csv")

# Export to JSON
TrainingDataExporter.export_to_json(data, "/tmp/training.json")

# Export to Parquet (requires pandas)
TrainingDataExporter.export_to_parquet(data, "/tmp/training.parquet")

# Generic export
TrainingDataExporter.export(
    data,
    "/tmp/training.csv",
    format=ExportFormat.CSV
)
```

#### Pre-built Datasets

##### Conversion Prediction Dataset
```python
dataset = ConversionPredictionDataset.build_dataset(
    sessions=[...],
    events_map={"session_id": [...]},
    conversions={"session_id": True/False}
)
# Features: engagement, customer value, store plan
# Target: conversion (0/1)
```

##### Cart Abandonment Dataset
```python
dataset = CartAbandonmentDataset.build_dataset(
    abandoned_carts=[...],
    recoveries={"cart_id": True/False}
)
# Features: cart value, customer LTV, time since abandon
# Target: recovery (0/1)
```

##### Agent Performance Dataset
```python
dataset = AgentPerformanceDataset.build_dataset(
    agent_actions=[...],
    outcomes={"action_id": {"converted": True, "engaged": True}}
)
# Features: agent type, action, confidence, customer context
# Target: conversion and engagement
```

## Integration Guide

### Step 1: Hook into Event Ingestion

**File:** `backend/api/routers/events.py`

Add pipeline call after event storage:

```python
from ..services.ml_data_pipeline import get_ml_pipeline

@router.post("/batch")
async def batch_events(
    request: BatchEventRequest,
    store_id: str = Header(...),
    db: Session = Depends(get_db)
):
    # ... existing validation ...
    
    # Store events
    for event in request.events:
        db_event = Event(
            session_id=event.session_id,
            event_type=event.event_type,
            event_data=event.event_data,
            store_id=store_id
        )
        db.add(db_event)
    db.commit()
    
    # NEW: Send to ML pipeline
    pipeline = get_ml_pipeline()
    for event in request.events:
        await pipeline.ingest_event(
            event_id=db_event.id,
            session_id=event.session_id,
            store_id=store_id,
            event_type=event.event_type,
            event_data=event.event_data,
            timestamp=datetime.utcnow(),
            db=db
        )
    
    return {"status": "ok"}
```

### Step 2: Hook into Agent Actions

**File:** `backend/agents/base_agent.py` (or each agent)

Add pipeline call when action is executed:

```python
from ..services.ml_data_pipeline import get_ml_pipeline

async def execute_action(self, session_id, store_id, action_details):
    # ... agent decision logic ...
    
    # NEW: Capture for ML training
    pipeline = get_ml_pipeline()
    await pipeline.capture_agent_action(
        action_id=str(uuid4()),
        session_id=session_id,
        store_id=store_id,
        agent_type=self.agent_type,
        action=action_details.get("action"),
        action_details=action_details,
        confidence=action_details.get("confidence", 0),
        db=db
    )
    
    return action_details
```

### Step 3: Hook into Conversions

**File:** `backend/api/routers/orders.py` (or payment handler)

Add pipeline call on purchase:

```python
from ..services.ml_data_pipeline import get_ml_pipeline

async def create_order(order_data, db):
    # ... create order ...
    
    # NEW: Capture conversion
    pipeline = get_ml_pipeline()
    await pipeline.capture_conversion(
        session_id=order_data["session_id"],
        store_id=order_data["store_id"],
        customer_id=order_data["customer_id"],
        cart_value=order_data["total_amount"],
        conversion_time=datetime.utcnow(),
        db=db
    )
    
    return order
```

### Step 4: Schedule Metrics Capture (Optional)

**File:** `backend/services/scheduler.py` (or async task runner)

Add daily store metrics capture:

```python
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from ..services.ml_data_pipeline import get_ml_pipeline

scheduler = AsyncIOScheduler()

@scheduler.scheduled_job('cron', hour=2, minute=0)  # 2 AM daily
async def capture_daily_metrics():
    """Capture store metrics daily for analytics"""
    db = SessionLocal()
    try:
        stores = db.query(Store).all()
        pipeline = get_ml_pipeline()
        
        for store in stores:
            await pipeline.capture_store_metrics(store.id, db)
    finally:
        db.close()

scheduler.start()
```

## Usage Examples

### Export Training Data for Model Development

```python
from backend.services.ml_data_pipeline import get_ml_pipeline
from datetime import datetime, timedelta

pipeline = get_ml_pipeline()

# Export last 90 days
filepath = await pipeline.export_training_dataset(
    store_id=None,  # All stores
    start_date=datetime.utcnow() - timedelta(days=90),
    end_date=datetime.utcnow(),
    output_format="csv"
)

# Load with pandas
import pandas as pd
df = pd.read_csv(filepath)
print(df.describe())
```

### Check Data Quality Before Training

```python
report = await pipeline.validate_data_quality()

if report["overall_quality_score"] < 0.8:
    print("⚠️  Data quality below threshold")
    print(f"Valid records: {report['valid_records']}/{report['total_records']}")
    
    for issue in report['issues'][:5]:  # First 5 issues
        print(f"Record {issue['record_idx']}: {issue['errors']}")
else:
    print(f"✅ Data quality score: {report['overall_quality_score']:.1%}")
```

### Query Conversion Metrics

```python
from backend.services.clickhouse_client import ClickHouseClient

ch = ClickHouseClient()
metrics = await ch.get_store_conversion_metrics("store_789", days=30)

print(f"Conversion Rate: {metrics['conversion_rate']:.1%}")
print(f"Avg Order Value: ${metrics['avg_order_value']:.2f}")
print(f"Total Revenue: ${metrics['total_revenue']:.2f}")
```

## Data Retention Policy

| Data Type | Retention | Purpose |
|-----------|-----------|---------|
| Events | Indefinite | Historical analysis, model retraining |
| Sessions | 2+ years | Feature engineering, behavioral analysis |
| Agent Actions | 2+ years | Agent performance measurement, feedback loops |
| Conversions | Indefinite | Revenue tracking, model training labels |
| Store Metrics | 3+ years | Trend analysis, growth tracking |

## Performance Optimization

### ClickHouse Query Optimization

1. **Use Partitioning:**
   ```sql
   SELECT * FROM events
   WHERE created_at >= '2024-01-01' AND created_at <= '2024-03-31'
   -- Automatically skips other partitions
   ```

2. **Aggregate Before Joining:**
   ```sql
   SELECT store_id, COUNT(*) as event_count
   FROM events
   GROUP BY store_id
   -- Much faster than raw event join
   ```

3. **Use Pre-aggregated Tables:**
   ```sql
   SELECT * FROM store_metrics
   WHERE created_at = '2024-01-31'
   -- Use aggregated metrics instead of raw events
   ```

### Batch Inserts

```python
# Efficient: Insert batch
events = [event1, event2, event3, ...]
clickhouse.execute("INSERT INTO events (...) VALUES", [events])

# Inefficient: Insert individually
for event in events:
    clickhouse.execute("INSERT INTO events (...) VALUES", [event])
```

## Monitoring

### Key Metrics to Track

1. **Event Ingestion Rate**
   ```sql
   SELECT toStartOfHour(created_at) as hour,
          COUNT(*) as events
   FROM events
   GROUP BY hour
   ORDER BY hour DESC
   ```

2. **Data Latency**
   ```python
   latest_event = await ch.query_events(limit=1)[0]
   latency = datetime.utcnow() - latest_event['created_at']
   print(f"Data latency: {latency.total_seconds()} seconds")
   ```

3. **Data Completeness**
   ```python
   report = await pipeline.validate_data_quality()
   print(f"Customer coverage: {report['checks']['sessions_with_customer'] / report['checks']['total_sessions']:.1%}")
   ```

## Troubleshooting

### Issue: ClickHouse Connection Failed

**Solution:** Ensure ClickHouse is running and accessible

```bash
# Test connection
clickhouse-client --host localhost --port 8123 -q "SELECT 1"

# Check Docker logs
docker logs clickhouse
```

### Issue: High Event Ingestion Latency

**Solution:** Increase batch size and connection pooling

```python
# In ClickHouse client init
self.client = clickhouse_driver.Client(
    host=host,
    port=port,
    send_block_size=1000,  # Increase batch size
    insert_block_size=1000,
)
```

### Issue: Missing Customer Data in Events

**Solution:** Ensure sessions have customer_id populated

```python
# In event ingestion
session = db.query(SessionModel).filter(
    SessionModel.id == session_id
).first()

if not session or not session.customer_id:
    logger.warning(f"Session {session_id} missing customer")
```

## Next Steps

1. **Deploy ClickHouse**
   ```bash
   docker-compose up -d clickhouse
   ```

2. **Initialize Tables**
   ```python
   ch = ClickHouseClient()
   await ch.create_tables()
   ```

3. **Integrate with Event API**
   - Add pipeline calls to event ingestion
   - Add pipeline calls to agent actions
   - Add pipeline calls to conversion tracking

4. **Set Up Daily Metrics**
   - Schedule store metrics capture
   - Set up dashboards in Grafana

5. **Export and Train**
   - Export training datasets
   - Train/retrain ML models
   - Monitor agent performance

## References

- ClickHouse Documentation: https://clickhouse.com/docs
- Feature Engineering Best Practices: https://www.deeplearningbook.org/
- ML Model Training: https://scikit-learn.org/stable/documentation.html
