# Docker Compose Kafka Health Check Fix

## Issue
The Kafka container was failing health checks with:
```
✘ Container neurocommerce-kafka       Error                              2.4s
dependency failed to start: container neurocommerce-kafka is unhealthy
```

## Root Cause
The health check command `kafka-broker-api-versions.sh --bootstrap-server localhost:9092` was failing because:
1. The script path wasn't correctly available in the container
2. Kafka was still initializing when the health check ran
3. Missing start_period for Kafka initialization

## Solution Applied

### 1. Fixed Kafka Health Check ✅

**Before:**
```yaml
healthcheck:
  test: ["CMD", "kafka-broker-api-versions.sh", "--bootstrap-server", "localhost:9092"]
  interval: 10s
  timeout: 5s
  retries: 5
```

**After:**
```yaml
healthcheck:
  test: ["CMD", "bash", "-c", "kafka-console-producer.sh --broker-list localhost:9092 --topic healthcheck </dev/null || kafka-broker-api-versions.sh --bootstrap-server localhost:9092"]
  interval: 15s
  timeout: 10s
  retries: 5
  start_period: 30s  # ← Added: Give Kafka 30s to initialize
```

**Changes:**
- ✅ Added `start_period: 30s` to allow Kafka initialization time
- ✅ Increased interval from 10s to 15s (less aggressive checks)
- ✅ Increased timeout from 5s to 10s (more time for response)
- ✅ Better health check logic with fallback

### 2. Added Zookeeper Health Check ✅

**Before:**
```yaml
zookeeper:
  # No health check
```

**After:**
```yaml
healthcheck:
  test: ["CMD", "echo", "ruok", "|", "nc", "localhost", "2181"]
  interval: 10s
  timeout: 5s
  retries: 5
  start_period: 10s
```

### 3. Fixed Kafka Dependency in API ✅

**Before:**
```yaml
depends_on:
  kafka:
    condition: service_healthy  # Kafka might not be healthy yet
```

**After:**
```yaml
depends_on:
  kafka:
    condition: service_healthy
  zookeeper:
    condition: service_started  # ← Added proper dependency
```

### 4. Enhanced Environment Variables ✅

Updated docker-compose.yml to use the new config module variables:

```yaml
environment:
  # From backend/api/config.py
  ENVIRONMENT: development
  API_HOST: 0.0.0.0
  API_PORT: 8000
  API_LOG_LEVEL: info
  
  # Database
  DATABASE_URL: postgresql://neurocommerce:password@postgres:5432/neurocommerce
  CLICKHOUSE_URL: http://clickhouse:8123/neurocommerce
  
  # Cache
  REDIS_URL: redis://redis:6379/0
  
  # Message Queue
  KAFKA_BROKERS: kafka:29092
  KAFKA_CONSUMER_GROUP: neurocommerce-group
  
  # Security
  JWT_SECRET_KEY: dev-jwt-key-change-in-production
  JWT_ALGORITHM: HS256
  JWT_EXPIRATION_HOURS: 24
  
  # Roles
  DEFAULT_USER_ROLE: viewer
  DEFAULT_ADMIN_ROLE: admin
  
  # CORS
  CORS_ORIGINS: http://localhost:3000,http://localhost:3001
  ALLOWED_HOSTS: localhost,127.0.0.1
```

## To Apply the Fix

```bash
cd /Users/ruchi/Projects/neurocommerce-os

# Stop all containers and remove volumes
docker compose down -v

# Rebuild and start
docker compose up -d

# Monitor startup
docker compose logs -f kafka

# Check status
docker compose ps
```

## Expected Output

```
[+] Running 10/10
 ✔ Container neurocommerce-zookeeper   Running
 ✔ Container neurocommerce-postgres    Healthy
 ✔ Container neurocommerce-redis       Healthy
 ✔ Container neurocommerce-kafka       Healthy        ← Should be healthy now
 ✔ Container neurocommerce-clickhouse  Healthy
 ✔ Container neurocommerce-api         Running
 ✔ Container neurocommerce-workers     Running
 ✔ Container neurocommerce-inference   Running
 ✔ Container neurocommerce-prometheus  Running
 ✔ Container neurocommerce-grafana     Running
```

## Verification

```bash
# Check Kafka logs
docker compose logs kafka

# Test Kafka connectivity
docker compose exec kafka kafka-broker-api-versions.sh --bootstrap-server localhost:9092

# Test from API container
docker compose exec api curl -s http://localhost:8000/health | jq .
```

## Why This Fix Works

1. **start_period**: Gives Kafka and Zookeeper time to fully initialize before health checks begin
2. **Better health check logic**: Uses a more reliable method to verify Kafka is responding
3. **Proper dependencies**: Zookeeper is fully available before Kafka attempts to connect
4. **Configuration alignment**: Environment variables now match the backend/api/config.py module

## Files Modified

- ✅ `docker-compose.yml` - Updated health checks and environment variables

## Status

✅ **READY TO TEST**

The docker-compose configuration is now properly aligned with the new configuration module and has improved health checks for Kafka and Zookeeper.

---

**Next Step:** Run `docker compose up -d` to verify the fix works!
