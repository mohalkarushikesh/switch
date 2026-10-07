# Oryza Platform Deployment Guide

## Overview

This guide covers deployment options from development to production scale.

## Development Deployment

### Quick Start (Local)

```bash
# Clone repository
git clone https://github.com/yourusername/oryza.git
cd oryza

# Start everything with one command
./start_oryza.bat  # Windows
./start_oryza.sh   # Linux/Mac

# Access at:
# Frontend: http://localhost:3000
# Backend: http://localhost:8889
```

### Docker Development

```bash
# Build and run with Docker Compose
docker-compose -f docker-compose.dev.yml up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

## Production Deployment

### 1. AWS Deployment

#### Prerequisites
- AWS Account
- AWS CLI configured
- Docker installed
- Domain name (optional)

#### Infrastructure Setup

```bash
# Create VPC and networking
aws cloudformation create-stack \
  --stack-name oryza-network \
  --template-body file://infrastructure/aws/network.yaml

# Create RDS database
aws rds create-db-instance \
  --db-instance-identifier oryza-db \
  --db-instance-class db.t3.medium \
  --engine postgres \
  --master-username admin \
  --master-user-password $DB_PASSWORD \
  --allocated-storage 100

# Create ElastiCache Redis
aws elasticache create-cache-cluster \
  --cache-cluster-id oryza-cache \
  --cache-node-type cache.t3.micro \
  --engine redis \
  --num-cache-nodes 1
```

#### Application Deployment

```bash
# Build and push Docker images
docker build -t oryza-backend backend/
docker tag oryza-backend:latest $AWS_ACCOUNT.dkr.ecr.region.amazonaws.com/oryza-backend:latest
docker push $AWS_ACCOUNT.dkr.ecr.region.amazonaws.com/oryza-backend:latest

# Deploy with ECS
aws ecs create-cluster --cluster-name oryza-cluster

# Create task definition
aws ecs register-task-definition \
  --cli-input-json file://infrastructure/aws/task-definition.json

# Create service
aws ecs create-service \
  --cluster oryza-cluster \
  --service-name oryza-backend \
  --task-definition oryza-backend:1 \
  --desired-count 3 \
  --launch-type FARGATE
```

#### Load Balancer Setup

```bash
# Create Application Load Balancer
aws elbv2 create-load-balancer \
  --name oryza-alb \
  --subnets subnet-xxx subnet-yyy \
  --security-groups sg-xxx

# Create target group
aws elbv2 create-target-group \
  --name oryza-targets \
  --protocol HTTP \
  --port 8889 \
  --vpc-id vpc-xxx \
  --health-check-path /api/v1/health
```

### 2. Google Cloud Platform

```bash
# Set up project
gcloud config set project oryza-platform

# Enable required APIs
gcloud services enable \
  compute.googleapis.com \
  container.googleapis.com \
  cloudsql.googleapis.com

# Create GKE cluster
gcloud container clusters create oryza-cluster \
  --num-nodes=3 \
  --zone=us-central1-a \
  --machine-type=n1-standard-2

# Deploy application
kubectl apply -f infrastructure/k8s/
```

### 3. Azure Deployment

```bash
# Create resource group
az group create --name oryza-rg --location eastus

# Create AKS cluster
az aks create \
  --resource-group oryza-rg \
  --name oryza-aks \
  --node-count 3 \
  --enable-addons monitoring

# Get credentials
az aks get-credentials --resource-group oryza-rg --name oryza-aks

# Deploy
kubectl apply -f infrastructure/k8s/
```

### 4. DigitalOcean (Budget-Friendly)

```bash
# Create Kubernetes cluster
doctl kubernetes cluster create oryza-k8s \
  --region nyc1 \
  --node-pool "name=worker;size=s-2vcpu-4gb;count=3"

# Create managed database
doctl databases create oryza-db \
  --engine pg \
  --region nyc1 \
  --size db-s-1vcpu-1gb

# Deploy application
kubectl apply -f infrastructure/k8s/
```

## Environment Configuration

### Production Environment Variables

```bash
# Create .env.production
NODE_ENV=production
APP_NAME=Oryza

# API Configuration
API_HOST=0.0.0.0
API_PORT=8889
SECRET_KEY=$(openssl rand -hex 32)

# Database
DATABASE_URL=postgresql://user:pass@db.oryza.ai:5432/oryza
REDIS_URL=redis://cache.oryza.ai:6379

# External Services
BROKER_API_KEY=xxx
NEWS_API_KEY=xxx
SMTP_HOST=smtp.sendgrid.net
SMTP_USER=apikey
SMTP_PASSWORD=xxx

# Security
CORS_ORIGINS=https://oryza.ai,https://app.oryza.ai
ENABLE_HTTPS=true
RATE_LIMIT_PER_MINUTE=120

# AI Services
ENABLE_GPU=true
AI_MODELS_PATH=/models
MAX_CONCURRENT_AI_TASKS=50
```

## SSL/TLS Configuration

### Let's Encrypt with Certbot

```bash
# Install certbot
sudo apt-get install certbot python3-certbot-nginx

# Get certificate
sudo certbot --nginx -d oryza.ai -d www.oryza.ai -d api.oryza.ai

# Auto-renewal
sudo certbot renew --dry-run
```

### Nginx Configuration

```nginx
server {
    listen 443 ssl http2;
    server_name api.oryza.ai;

    ssl_certificate /etc/letsencrypt/live/oryza.ai/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/oryza.ai/privkey.pem;

    location / {
        proxy_pass http://backend:8889;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /ws {
        proxy_pass http://backend:8889;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

## Database Migration

### PostgreSQL Setup

```sql
-- Create database
CREATE DATABASE oryza;
CREATE USER oryza_user WITH ENCRYPTED PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE oryza TO oryza_user;

-- Enable extensions
\c oryza
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
```

### Run Migrations

```bash
# Development
cd backend
alembic upgrade head

# Production
docker exec oryza-backend alembic upgrade head
```

## Monitoring & Logging

### 1. Application Monitoring

```yaml
# prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'oryza-backend'
    static_configs:
      - targets: ['backend:8889']
    metrics_path: '/metrics'
```

### 2. Log Aggregation

```yaml
# fluentd.conf
<source>
  @type forward
  port 24224
</source>

<match oryza.**>
  @type elasticsearch
  host elasticsearch
  port 9200
  index_name oryza
</match>
```

### 3. Health Checks

```python
# health_check.py
@app.get("/health")
async def health_check():
    checks = {
        "api": "healthy",
        "database": await check_database(),
        "redis": await check_redis(),
        "ai_models": check_ai_models()
    }
    
    status = all(check == "healthy" for check in checks.values())
    return {
        "status": "healthy" if status else "unhealthy",
        "checks": checks,
        "timestamp": datetime.now().isoformat()
    }
```

## Scaling Strategy

### Horizontal Scaling

```yaml
# kubernetes/hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: oryza-backend-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: oryza-backend
  minReplicas: 3
  maxReplicas: 20
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

### Load Testing

```bash
# Install k6
brew install k6

# Run load test
k6 run tests/load/stress_test.js

# Sample test
import http from 'k6/http';
import { check } from 'k6';

export let options = {
  stages: [
    { duration: '2m', target: 100 },
    { duration: '5m', target: 100 },
    { duration: '2m', target: 200 },
    { duration: '5m', target: 200 },
    { duration: '2m', target: 0 },
  ],
};

export default function() {
  let response = http.get('https://api.oryza.ai/health');
  check(response, {
    'status is 200': (r) => r.status === 200,
  });
}
```

## Backup & Recovery

### Automated Backups

```bash
# backup.sh
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups"

# Database backup
pg_dump $DATABASE_URL > $BACKUP_DIR/oryza_db_$DATE.sql
gzip $BACKUP_DIR/oryza_db_$DATE.sql

# Upload to S3
aws s3 cp $BACKUP_DIR/oryza_db_$DATE.sql.gz s3://oryza-backups/

# Clean old backups (keep 30 days)
find $BACKUP_DIR -name "*.sql.gz" -mtime +30 -delete
```

### Disaster Recovery

```bash
# Restore database
gunzip < oryza_db_backup.sql.gz | psql $DATABASE_URL

# Restore Redis
redis-cli --rdb /backup/redis_backup.rdb
```

## CI/CD Pipeline

### GitHub Actions

```yaml
# .github/workflows/deploy.yml
name: Deploy to Production

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Build and push Docker image
        env:
          DOCKER_REGISTRY: ${{ secrets.DOCKER_REGISTRY }}
        run: |
          docker build -t $DOCKER_REGISTRY/oryza-backend:$GITHUB_SHA backend/
          docker push $DOCKER_REGISTRY/oryza-backend:$GITHUB_SHA
      
      - name: Deploy to Kubernetes
        run: |
          kubectl set image deployment/oryza-backend \
            backend=$DOCKER_REGISTRY/oryza-backend:$GITHUB_SHA
```

## Performance Optimization

### 1. Caching Strategy

```python
from redis import Redis
from functools import lru_cache

redis_client = Redis.from_url(REDIS_URL)

@lru_cache(maxsize=1000)
def get_stock_price(symbol: str):
    # Check Redis cache
    cached = redis_client.get(f"price:{symbol}")
    if cached:
        return json.loads(cached)
    
    # Fetch from API
    price = fetch_price_from_api(symbol)
    
    # Cache for 1 minute
    redis_client.setex(f"price:{symbol}", 60, json.dumps(price))
    return price
```

### 2. Database Optimization

```sql
-- Create indexes
CREATE INDEX idx_holdings_user_id ON holdings(user_id);
CREATE INDEX idx_transactions_created_at ON transactions(created_at);
CREATE INDEX idx_orders_status ON orders(status);

-- Partitioning for large tables
CREATE TABLE transactions_2024_01 PARTITION OF transactions
    FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');
```

## Security Hardening

### 1. Firewall Rules

```bash
# Allow only necessary ports
ufw default deny incoming
ufw default allow outgoing
ufw allow 22/tcp  # SSH
ufw allow 443/tcp # HTTPS
ufw allow 8889/tcp # API (internal only)
ufw enable
```

### 2. Secrets Management

```bash
# Use HashiCorp Vault
vault kv put secret/oryza/prod \
  db_password=xxx \
  jwt_secret=xxx \
  api_keys=xxx
```

## Troubleshooting

### Common Issues

1. **Database Connection Issues**
   ```bash
   # Check connectivity
   psql -h $DB_HOST -U $DB_USER -d oryza -c "SELECT 1"
   ```

2. **Memory Issues**
   ```bash
   # Increase container memory
   docker update --memory 4g oryza-backend
   ```

3. **SSL Certificate Issues**
   ```bash
   # Renew certificate
   certbot renew --force-renewal
   ```

## Deployment Checklist

- [ ] Environment variables configured
- [ ] SSL certificates installed
- [ ] Database migrated
- [ ] Redis connected
- [ ] Health checks passing
- [ ] Monitoring configured
- [ ] Backups scheduled
- [ ] Security scan completed
- [ ] Load testing passed
- [ ] Documentation updated

---

**Note**: Always test deployments in staging before production! 