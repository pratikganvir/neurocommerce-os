# NeuroCommerce OS Deployment Guide

## Prerequisites

- Docker & Docker Compose (local development)
- Kubernetes 1.27+ (production)
- Terraform (AWS)
- PostgreSQL 15+ credentials
- Stripe, SendGrid, Twilio accounts

## Local Development

### 1. Clone Repository

```bash
git clone https://github.com/neurocommerce/neurocommerce-os.git
cd neurocommerce-os
```

### 2. Environment Setup

```bash
cp .env.example .env
# Edit .env with your API keys
```

### 3. Start Services

```bash
docker-compose up -d

# Wait for services to be healthy
docker-compose exec api python -c "from alembic.config import Config; from alembic.command import upgrade; upgrade(Config('alembic.ini'), 'head')"
```

### 4. Verify

```bash
# API health check
curl http://localhost:8000/health

# Dashboard
open http://localhost:3000

# Grafana
open http://localhost:3001  # admin:admin
```

## Production Deployment

### AWS with Kubernetes

#### 1. Create EKS Cluster with Terraform

```bash
cd infrastructure/terraform

# Initialize
terraform init

# Plan
terraform plan -var-file=prod.tfvars

# Deploy
terraform apply -var-file=prod.tfvars

# Get kubeconfig
aws eks update-kubeconfig --region us-east-1 --name neurocommerce-cluster
```

#### 2. Deploy to Kubernetes

```bash
# Create namespace
kubectl create namespace neurocommerce

# Create secrets
kubectl create secret generic postgres-secret \
  --from-literal=url=$DATABASE_URL \
  --from-literal=password=$DB_PASSWORD \
  -n neurocommerce

# Deploy containers
kubectl apply -f infrastructure/k8s/

# Verify
kubectl get pods -n neurocommerce
```

#### 3. Configure DNS and SSL

```bash
# Get LoadBalancer IP
kubectl get svc dashboard -n neurocommerce

# Update Route 53
# Point yourdomain.com to LoadBalancer IP

# Install cert-manager for SSL
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.0/cert-manager.yaml
```

### Helm Deployment

```bash
# Add Helm repo
helm repo add neurocommerce https://charts.neurocommerce.io
helm repo update

# Install
helm install neurocommerce neurocommerce/neurocommerce-os \
  -n neurocommerce \
  -f values.yaml

# Upgrade
helm upgrade neurocommerce neurocommerce/neurocommerce-os -f values.yaml
```

## Database Migrations

```bash
# Run migrations
docker-compose exec api alembic upgrade head

# Rollback
docker-compose exec api alembic downgrade -1
```

## Monitoring

### Prometheus

```
http://localhost:9090
```

Metrics:
- `api_requests_total`
- `api_latency_seconds`
- `agent_decisions_total`
- `conversions_total`
- `event_processing_lag`

### Grafana

```
http://localhost:3001
```

Dashboards:
- Overview
- Agent Performance
- Revenue Impact
- System Health

### ELK Stack (Optional)

```bash
docker-compose -f docker-compose.elk.yml up
```

Access Kibana: http://localhost:5601

## Scaling

### Horizontal Scaling

```bash
# Scale API
kubectl scale deployment api -n neurocommerce --replicas 5

# Scale workers
kubectl scale deployment workers -n neurocommerce --replicas 3

# Scale inference
kubectl scale deployment inference -n neurocommerce --replicas 3
```

### Vertical Scaling (AWS)

```bash
# Increase RDS instance class
aws rds modify-db-instance \
  --db-instance-identifier neurocommerce-postgres \
  --db-instance-class db.t3.large \
  --apply-immediately
```

## Backup & Disaster Recovery

### Database Backups

```bash
# RDS automated backups (7 days retention)
# Configured in Terraform

# Manual backup
aws rds create-db-snapshot \
  --db-instance-identifier neurocommerce-postgres \
  --db-snapshot-identifier neurocommerce-backup-$(date +%s)

# Restore from snapshot
aws rds restore-db-instance-from-db-snapshot \
  --db-instance-identifier neurocommerce-postgres-restored \
  --db-snapshot-identifier neurocommerce-backup-xxx
```

### Event Log Backups

```bash
# Export events to S3
aws s3 sync s3://neurocommerce-events/daily/ \
  s3://neurocommerce-backups/daily/ --copy-props all
```

## Troubleshooting

### API Connection Issues

```bash
# Check API status
curl http://api:8000/health

# Check database connectivity
docker-compose exec api psql $DATABASE_URL -c "SELECT 1"

# Check Kafka connectivity
docker-compose exec api kafka-broker-api-versions.sh --bootstrap-server kafka:9092
```

### High Latency

```bash
# Check API metrics
curl http://localhost:9090/api/v1/query?query=api_latency_seconds

# Check database performance
# PostgreSQL slow query log
docker-compose exec postgres tail -f /var/log/postgresql/postgresql.log
```

### Memory Issues

```bash
# Check container memory usage
docker stats

# Increase limits in docker-compose.yml or K8s deployment
```

## Cost Optimization

1. **Spot Instances**: Use AWS Spot for non-critical workers
2. **Reserved Capacity**: Reserve RDS and Kafka for 1-3 years
3. **Caching**: Increase Redis TTL for frequently accessed data
4. **Log Retention**: Archive old logs to S3 Glacier
5. **Data Tiering**: Move cold data to ClickHouse for analytics

---

For issues or questions, open an issue on GitHub or contact support@neurocommerce.io
