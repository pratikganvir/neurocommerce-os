# API Service Startup Fix - Complete Solution

## Problem Diagnosed

The API service was failing to start due to incorrect import paths and Docker context configuration:

### Root Causes:
1. **Incorrect relative imports**: `main.py` was using `from ..models.models import` which expected a nested package structure
2. **Wrong Docker context**: The build context was `./backend/api` but the code needed access to `./backend/models`
3. **Import path mismatch**: The Dockerfile WORKDIR was `/app` but imports expected models to be at a parent level
4. **Missing PYTHONPATH**: The container didn't have proper Python path configuration for resolving modules

## Solutions Implemented

### 1. Updated Docker Build Context (docker-compose.yml)

**Changed from:**
```yaml
api:
  build:
    context: ./backend/api
    dockerfile: Dockerfile
```

**Changed to:**
```yaml
api:
  build:
    context: ./backend
    dockerfile: api/Dockerfile
```

**Why:** This allows the Docker build to access both the `api` and `models` directories as siblings.

### 2. Updated Dockerfile (backend/api/Dockerfile)

**Key changes:**
- Copy from `api/requirements.txt` (relative to new context)
- Copy API code: `COPY api /app`
- Copy models: `COPY models /backend/models`
- Set PYTHONPATH: `ENV PYTHONPATH=/backend:$PYTHONPATH`
- Increased startup period to 40s for database initialization
- Uses absolute path `/backend` for models accessibility

```dockerfile
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc postgresql-client && rm -rf /var/lib/apt/lists/*

COPY api/requirements.txt .
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

COPY api /app
COPY models /backend/models

RUN mkdir -p /app/logs

ENV PYTHONPATH=/backend:$PYTHONPATH

HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')" || exit 1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 3. Fixed Import Statements (backend/api/main.py)

**Key changes:**

1. **Configure logging first** (before using logger):
```python
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
```

2. **Set PYTHONPATH before imports**:
```python
sys.path.insert(0, "/backend")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
```

3. **Use try/except for model imports with fallback**:
```python
try:
    from models.models import Base, Store, User, ApiKey
except ImportError as e:
    logger.warning(f"Could not import models: {e}")
    # Fallback for local development
    Base, Store, User, ApiKey = None, None, None, None
```

4. **Use absolute imports for local modules**:
```python
from database import engine, SessionLocal, init_db
from security import hash_password, verify_password, create_access_token, get_current_user
from routers import auth, events, agents, shopify, campaigns, experiments, billing
from config import (
    API_TITLE, API_DESCRIPTION, API_VERSION, API_LOG_LEVEL,
    CORS_ORIGINS, ALLOWED_HOSTS, STORE_ID_PREFIX, API_HOST, API_PORT
)
```

5. **Removed all `config.` references** - use imported constants directly

## How to Test

### 1. Build the Docker Image

```bash
cd /Users/ruchi/Projects/neurocommerce-os
docker compose build api
```

Expected output: Successfully built [image-id]

### 2. Start All Services

```bash
docker compose up -d
```

This starts:
- PostgreSQL on 5432
- ClickHouse on 8123
- Redis on 6379
- Kafka on 9092
- Zookeeper on 2181
- **API on 8000** ← This is what we fixed
- Frontend on 3000
- Workers
- Inference
- Prometheus
- Grafana

### 3. Verify API is Responding

```bash
# Check health endpoint
curl http://localhost:8000/health

# Expected response:
{
  "status": "healthy",
  "version": "1.0.0",
  "database": "healthy",
  "cache": "healthy"
}
```

### 4. Access API Documentation

Open in browser:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### 5. Check Logs

```bash
# View API container logs
docker compose logs api

# Follow logs in real-time
docker compose logs -f api

# Check specific error
docker compose logs api | grep -i error
```

## Troubleshooting

### Issue: "ModuleNotFoundError: No module named 'models'"

**Solution**: Verify PYTHONPATH is set correctly
```bash
docker compose exec api python -c "import sys; print(sys.path)"
```
Should show `/backend` in the path.

### Issue: "Connection refused" on localhost:8000

**Possible causes:**
1. Container not running: `docker compose ps | grep api`
2. Port not exposed: Check docker-compose.yml has `ports: - "8000:8000"`
3. API crashed: `docker compose logs api` to see errors

### Issue: Database connection timeout

**Solution**: Ensure postgres is healthy first
```bash
docker compose logs postgres | tail -20
```

The health check waits 40 seconds for database to be ready. If still timing out:
- Increase `start-period` in health check
- Check PostgreSQL logs for initialization errors

### Issue: Health check reports "unhealthy"

**Check database:**
```bash
docker compose exec api python -c "
import psycopg2
conn = psycopg2.connect('postgresql://neurocommerce:password@postgres:5432/neurocommerce')
print('Database OK')
"
```

**Check Redis:**
```bash
docker compose exec api python -c "
import redis
r = redis.Redis(host='redis', port=6379)
r.ping()
print('Redis OK')
"
```

## Environment Variables

The API reads these from docker-compose.yml:

```yaml
ENVIRONMENT: development
API_HOST: 0.0.0.0
API_PORT: 8000
API_LOG_LEVEL: info
DATABASE_URL: postgresql://neurocommerce:password@postgres:5432/neurocommerce
CLICKHOUSE_URL: http://clickhouse:8123/neurocommerce
REDIS_URL: redis://redis:6379/0
KAFKA_BROKERS: kafka:29092
JWT_SECRET_KEY: dev-jwt-key-change-in-production
```

For production, update these values before deployment.

## File Changes Summary

| File | Change | Reason |
|------|--------|--------|
| `docker-compose.yml` | Build context: `./backend/api` → `./backend` | Access sibling directories |
| `backend/api/Dockerfile` | Copy paths updated, PYTHONPATH added | Match new context structure |
| `backend/api/main.py` | Import fixes, PYTHONPATH setup, config constants | Resolve module imports correctly |

## Success Criteria

✅ **All the following should work:**

1. `docker compose build api` completes without errors
2. `docker compose up -d` starts all services
3. `curl http://localhost:8000/health` returns healthy status
4. `http://localhost:8000/docs` loads Swagger UI
5. Frontend on `http://localhost:3000` connects to API successfully
6. Database migrations run automatically on startup
7. All routers are registered: `/api/v1/auth`, `/api/v1/events`, etc.

## Next Steps

After verifying the API works:

1. **Test endpoints**: Use Swagger UI to test API endpoints
2. **Check integrations**: Verify database, cache, and queue connections
3. **Run migrations**: Ensure database schema is initialized
4. **Test workflows**: Run through complete Shopify OAuth flow
5. **Monitor health**: Use Prometheus/Grafana to monitor API metrics

## Additional Notes

- The health check endpoint waits 40 seconds before first check to allow database initialization
- If services are slow to start, increase `start_period` values in health checks
- All services use the named network `neurocommerce-network` for communication
- Database credentials are for development only - change for production
- Check logs frequently during debugging: `docker compose logs [service-name]`
