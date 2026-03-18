# ML Pipeline Integration Guide

Quick reference for integrating the ML data pipeline into existing code.

## 1. Event Ingestion Integration

**File:** `backend/api/routers/events.py`

### Before (Current)
```python
@router.post("/batch")
async def batch_events(request: BatchEventRequest, store_id: str = Header(...), db: Session = Depends(get_db)):
    for event_req in request.events:
        db_event = Event(
            session_id=event_req.session_id,
            event_type=event_req.event_type,
            event_data=event_req.event_data,
            store_id=store_id
        )
        db.add(db_event)
    db.commit()
    return {"status": "ok"}
```

### After (With ML Pipeline)
```python
from ..services.ml_data_pipeline import get_ml_pipeline
from datetime import datetime
import uuid

@router.post("/batch")
async def batch_events(request: BatchEventRequest, store_id: str = Header(...), db: Session = Depends(get_db)):
    pipeline = get_ml_pipeline()
    
    for event_req in request.events:
        # Store in PostgreSQL
        db_event = Event(
            id=str(uuid.uuid4()),
            session_id=event_req.session_id,
            event_type=event_req.event_type,
            event_data=event_req.event_data,
            store_id=store_id,
            created_at=datetime.utcnow()
        )
        db.add(db_event)
    db.commit()
    
    # Send to ML pipeline for enrichment and ClickHouse
    for idx, event_req in enumerate(request.events):
        await pipeline.ingest_event(
            event_id=db.query(Event).filter(
                Event.session_id == event_req.session_id,
                Event.event_type == event_req.event_type
            ).order_by(Event.created_at.desc()).first().id,
            session_id=event_req.session_id,
            store_id=store_id,
            event_type=event_req.event_type,
            event_data=event_req.event_data,
            timestamp=datetime.utcnow(),
            db=db
        )
    
    return {"status": "ok"}
```

## 2. Agent Action Integration

**File:** `backend/agents/[agent_name].py` (all 7 agents)

### Before (Current)
```python
async def suggest_action(self, session_id: str, store_id: str, db: Session):
    # ... agent logic ...
    return {
        "action": "show_free_shipping",
        "parameters": {...},
        "confidence": 0.85
    }
```

### After (With ML Pipeline)
```python
from ..services.ml_data_pipeline import get_ml_pipeline
import uuid
from datetime import datetime

async def suggest_action(self, session_id: str, store_id: str, db: Session):
    # ... agent logic ...
    
    action_result = {
        "action": "show_free_shipping",
        "parameters": {...},
        "confidence": 0.85
    }
    
    # NEW: Capture for ML training
    pipeline = get_ml_pipeline()
    await pipeline.capture_agent_action(
        action_id=str(uuid.uuid4()),
        session_id=session_id,
        store_id=store_id,
        agent_type=self.agent_type,  # e.g., "checkout_persuasion"
        action=action_result["action"],
        action_details=action_result,
        confidence=action_result.get("confidence", 0),
        db=db
    )
    
    return action_result
```

## 3. Conversion Tracking Integration

**File:** `backend/api/routers/orders.py` (or wherever orders are created)

### Before (Current)
```python
@router.post("/orders")
async def create_order(order_data: OrderRequest, db: Session = Depends(get_db)):
    order = Order(
        customer_id=order_data.customer_id,
        session_id=order_data.session_id,
        total_amount=order_data.total_amount,
        store_id=order_data.store_id
    )
    db.add(order)
    db.commit()
    return order
```

### After (With ML Pipeline)
```python
from ..services.ml_data_pipeline import get_ml_pipeline
from datetime import datetime

@router.post("/orders")
async def create_order(order_data: OrderRequest, db: Session = Depends(get_db)):
    order = Order(
        customer_id=order_data.customer_id,
        session_id=order_data.session_id,
        total_amount=order_data.total_amount,
        store_id=order_data.store_id,
        created_at=datetime.utcnow()
    )
    db.add(order)
    db.commit()
    
    # NEW: Capture conversion for ML training labels
    pipeline = get_ml_pipeline()
    await pipeline.capture_conversion(
        session_id=order_data.session_id,
        store_id=order_data.store_id,
        customer_id=order_data.customer_id,
        cart_value=order_data.total_amount,
        conversion_time=datetime.utcnow(),
        db=db
    )
    
    return order
```

## 4. Daily Metrics Scheduling (Optional)

**File:** `backend/background_tasks.py` (create if doesn't exist)

```python
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from .services.ml_data_pipeline import get_ml_pipeline
from .database import SessionLocal
from .models.models import Store
import logging

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()

@scheduler.scheduled_job(CronTrigger(hour=2, minute=0))
async def capture_daily_store_metrics():
    """Capture store metrics daily at 2 AM UTC"""
    db = SessionLocal()
    try:
        stores = db.query(Store).all()
        pipeline = get_ml_pipeline()
        
        logger.info(f"Capturing metrics for {len(stores)} stores...")
        
        for store in stores:
            try:
                await pipeline.capture_store_metrics(store.id, db)
                logger.info(f"Metrics captured for store {store.id}")
            except Exception as e:
                logger.error(f"Failed to capture metrics for {store.id}: {e}")
        
        logger.info("Daily metrics capture completed")
    finally:
        db.close()

def start_background_tasks():
    """Initialize and start background task scheduler"""
    if not scheduler.running:
        scheduler.start()
        logger.info("Background task scheduler started")
```

## 5. Data Export Endpoint (Optional)

**File:** `backend/api/routers/ml.py` (create if doesn't exist)

```python
from fastapi import APIRouter, Header, Depends
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from ..services.ml_data_pipeline import get_ml_pipeline
from ..database import get_db

router = APIRouter(prefix="/api/ml", tags=["ml"])

@router.post("/export-training-data")
async def export_training_data(
    store_id: str = Header(...),
    days: int = 90,
    format: str = "csv",
    db: Session = Depends(get_db)
):
    """Export training data for ML model development"""
    
    pipeline = get_ml_pipeline()
    
    filepath = await pipeline.export_training_dataset(
        store_id=store_id,
        start_date=datetime.utcnow() - timedelta(days=days),
        end_date=datetime.utcnow(),
        output_format=format
    )
    
    return {
        "status": "ok",
        "filepath": filepath,
        "format": format,
        "days": days
    }

@router.get("/data-quality")
async def get_data_quality(
    store_id: str = Header(...),
    db: Session = Depends(get_db)
):
    """Check data quality metrics"""
    
    pipeline = get_ml_pipeline()
    report = await pipeline.validate_data_quality(store_id)
    
    return {
        "status": "ok",
        "quality_report": report
    }
```

## Implementation Checklist

- [ ] **Event Ingestion:** Add `pipeline.ingest_event()` call to `/events/batch` endpoint
- [ ] **Agent Actions:** Add `pipeline.capture_agent_action()` to all 7 agents
- [ ] **Conversions:** Add `pipeline.capture_conversion()` to order creation
- [ ] **Metrics (Optional):** Set up daily metrics capture scheduler
- [ ] **Export Endpoint (Optional):** Create ML export API endpoint
- [ ] **ClickHouse:** Deploy and initialize tables (`await ch.create_tables()`)
- [ ] **Testing:** Verify data flows to ClickHouse
- [ ] **Monitoring:** Set up metrics and alerts

## Verification Steps

### 1. Check Event Ingestion
```bash
# SSH into ClickHouse
docker exec -it clickhouse-server clickhouse-client

# Query events
SELECT COUNT(*) FROM events;
SELECT event_type, COUNT(*) FROM events GROUP BY event_type;
```

### 2. Check Agent Actions
```sql
SELECT agent_type, COUNT(*), AVG(confidence) 
FROM agent_actions 
GROUP BY agent_type;
```

### 3. Check Conversions
```sql
SELECT COUNT(*) as conversions, SUM(conversion_value) as total_revenue
FROM conversions
WHERE created_at >= subtractDays(now(), 1);
```

### 4. Validate Data Quality
```python
pipeline = get_ml_pipeline()
report = await pipeline.validate_data_quality()
print(f"Quality Score: {report['overall_quality_score']:.1%}")
```

## Common Mistakes to Avoid

❌ **Don't:** Call pipeline synchronously
```python
# WRONG - blocks event processing
pipeline.ingest_event(...)  # Missing await
```

✅ **Do:** Use async/await
```python
# CORRECT - non-blocking
await pipeline.ingest_event(...)
```

---

❌ **Don't:** Forget to pass db session
```python
# WRONG - crashes on missing context
await pipeline.capture_agent_action(..., db=None)
```

✅ **Do:** Pass valid db session
```python
# CORRECT
await pipeline.capture_agent_action(..., db=db)
```

---

❌ **Don't:** Inline timestamps
```python
# WRONG - uses server time, not event time
await pipeline.ingest_event(..., timestamp=datetime.utcnow())
```

✅ **Do:** Use event's original timestamp
```python
# CORRECT - preserves event time
await pipeline.ingest_event(..., timestamp=event.timestamp)
```

## Minimal Integration Example

If you only want the absolute essentials:

```python
# 1. Add to event ingestion
pipeline = get_ml_pipeline()
await pipeline.ingest_event(
    event_id=event.id,
    session_id=event.session_id,
    store_id=store_id,
    event_type=event.event_type,
    event_data=event.event_data,
    timestamp=datetime.utcnow(),
    db=db
)

# 2. Add to purchase handler
await pipeline.capture_conversion(
    session_id=session_id,
    store_id=store_id,
    customer_id=customer_id,
    cart_value=total_amount,
    conversion_time=datetime.utcnow(),
    db=db
)

# That's it! Events and conversions are now in ClickHouse
```

## Support & Troubleshooting

**Q: ClickHouse connection failed**
A: Ensure ClickHouse is running: `docker ps | grep clickhouse`

**Q: Events not appearing in ClickHouse**
A: Check logs: `logger.debug(f"Event ingested: {event_id}")`

**Q: Data quality score too low**
A: Ensure sessions have customer_id populated

**Q: ClickHouse insert timeout**
A: Increase batch size or check ClickHouse memory usage
