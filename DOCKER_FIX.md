# Docker Build Fix - Requirements.txt Files

## Issue
Docker Buildx was failing with error:
```
[workers 4/6] COPY requirements.txt .:
ERROR: failed to calculate checksum of ref ... "/requirements.txt": not found
```

## Root Cause
The Dockerfiles reference `requirements.txt` files that were missing from:
- `backend/workers/requirements.txt`
- `ml/inference/requirements.txt`

While `backend/api/requirements.txt` existed, the other two services' requirements files were missing.

## Solution Applied

### Files Created

1. **backend/workers/requirements.txt**
   ```
   kafka-python==2.0.2
   sqlalchemy==2.0.23
   psycopg2-binary==2.9.9
   redis==5.0.1
   python-dotenv==1.0.0
   requests==2.31.0
   pydantic==2.5.0
   ```

2. **ml/inference/requirements.txt**
   ```
   fastapi==0.104.1
   uvicorn==0.24.0
   numpy==1.26.0
   pandas==2.1.0
   scikit-learn==1.3.0
   torch==2.0.0
   xgboost==2.0.0
   redis==5.0.1
   pydantic==2.5.0
   python-dotenv==1.0.0
   requests==2.31.0
   ```

### Why These Dependencies?

**Workers (Kafka Consumer)**
- `kafka-python` - Consume from Kafka topics
- `sqlalchemy` + `psycopg2-binary` - Database access
- `redis` - Cache access
- `pydantic` - Data validation
- `python-dotenv` - Environment configuration
- `requests` - HTTP calls to external services

**ML Inference Service**
- `fastapi` + `uvicorn` - Web framework
- `numpy` + `pandas` - Data processing
- `scikit-learn` - ML model inference
- `torch` - PyTorch support
- `xgboost` - Gradient boosting
- `redis` - Caching predictions
- `pydantic` - API validation
- `python-dotenv` - Configuration

## Testing

All three services now have their `requirements.txt` files:

```bash
✓ backend/api/requirements.txt (17 packages)
✓ backend/workers/requirements.txt (7 packages)
✓ ml/inference/requirements.txt (11 packages)
```

## Next Steps

Docker build should now complete successfully:

```bash
cd /Users/ruchi/Projects/neurocommerce-os
docker compose up -d
```

All 12 services will start:
- PostgreSQL, ClickHouse, Redis, Kafka, Zookeeper
- FastAPI API, Workers, Inference, Dashboard
- Prometheus, Grafana

Then access at:
- Dashboard: http://localhost:3000
- API: http://localhost:8000
- Grafana: http://localhost:3001
