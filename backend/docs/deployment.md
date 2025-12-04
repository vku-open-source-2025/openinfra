# OpenInfra Deployment Guide

## Overview

This guide covers deploying the OpenInfra Urban Infrastructure Asset Management System from local development to production on Google Cloud Platform (GCP). The deployment strategy supports both Docker Compose (development/staging) and Kubernetes (production).

---

## Table of Contents

1. [Local Development Setup](#local-development-setup)
2. [Docker Deployment](#docker-deployment)
3. [Kubernetes Deployment (Production)](#kubernetes-deployment-production)
4. [Database Setup](#database-setup)
5. [Monitoring & Observability](#monitoring--observability)
6. [CI/CD Pipeline](#cicd-pipeline)
7. [Security Hardening](#security-hardening)
8. [Backup & Disaster Recovery](#backup--disaster-recovery)

---

## Local Development Setup

### Prerequisites

- Python 3.11+
- Node.js 18+
- Docker & Docker Compose
- Git

### Step 1: Clone Repository

```bash
git clone https://github.com/your-org/openinfra.git
cd openinfra
```

### Step 2: Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env

# Edit .env with your configuration
nano .env
```

**Environment Variables** (`.env`):
```bash
# Application
PROJECT_NAME=OpenInfra
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=debug

# Database
MONGODB_URL=mongodb://localhost:27017
DATABASE_NAME=openinfra_dev

# Redis
REDIS_URL=redis://localhost:6379/0

# Security
SECRET_KEY=your-secret-key-change-this-in-production
JWT_SECRET_KEY=your-jwt-secret-key
JWT_ALGORITHM=HS256
JWT_EXPIRATION_MINUTES=60

# External Services
OSM_NOMINATIM_URL=https://nominatim.openstreetmap.org
SENDGRID_API_KEY=your-sendgrid-key
TWILIO_ACCOUNT_SID=your-twilio-sid
TWILIO_AUTH_TOKEN=your-twilio-token

# Storage
STORAGE_BACKEND=local  # or 'minio' for production
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_BUCKET_NAME=openinfra-assets
MINIO_USE_SSL=false
MINIO_REGION=us-east-1

# MQTT
MQTT_BROKER_HOST=localhost
MQTT_BROKER_PORT=1883
MQTT_USERNAME=openinfra
MQTT_PASSWORD=secure-password

# Celery
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2
```

### Step 3: Start Services with Docker Compose

```bash
# From project root
cd infra
docker-compose up -d
```

This starts:
- MongoDB (port 27017)
- Redis (port 6379)
- MQTT Broker (port 1883)

### Step 4: Run Database Migrations

```bash
cd backend
python migrations/init_db.py
python migrations/seed_dev_data.py
```

### Step 5: Start Backend

```bash
# Terminal 1: FastAPI server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2: Celery worker
celery -A app.celery_app worker --loglevel=info

# Terminal 3: Celery beat (scheduler)
celery -A app.celery_app beat --loglevel=info
```

### Step 6: Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

### Access Points

- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Frontend**: http://localhost:5173

---

## Docker Deployment

### Production Docker Compose

For small deployments or staging environments.

**docker-compose.prod.yml**:
```yaml
version: '3.8'

services:
  mongodb:
    image: mongo:7.0
    restart: always
    environment:
      MONGO_INITDB_ROOT_USERNAME: ${MONGO_ROOT_USER}
      MONGO_INITDB_ROOT_PASSWORD: ${MONGO_ROOT_PASSWORD}
    volumes:
      - mongodb_data:/data/db
      - mongodb_config:/data/configdb
    ports:
      - "27017:27017"
    networks:
      - openinfra-network

  redis:
    image: redis:7.0-alpine
    restart: always
    command: redis-server --requirepass ${REDIS_PASSWORD}
    volumes:
      - redis_data:/data
    ports:
      - "6379:6379"
    networks:
      - openinfra-network

  mqtt-broker:
    image: eclipse-mosquitto:2.0
    restart: always
    volumes:
      - ./mosquitto/mosquitto.conf:/mosquitto/config/mosquitto.conf
      - ./mosquitto/data:/mosquitto/data
      - ./mosquitto/log:/mosquitto/log
    ports:
      - "1883:1883"
      - "9001:9001"
    networks:
      - openinfra-network

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    restart: always
    environment:
      - ENVIRONMENT=production
      - MONGODB_URL=mongodb://${MONGO_ROOT_USER}:${MONGO_ROOT_PASSWORD}@mongodb:27017
      - REDIS_URL=redis://:${REDIS_PASSWORD}@redis:6379/0
      - MQTT_BROKER_HOST=mqtt-broker
    depends_on:
      - mongodb
      - redis
      - mqtt-broker
    ports:
      - "8000:8000"
    networks:
      - openinfra-network
    volumes:
      - ./backend/logs:/app/logs

  celery-worker:
    build:
      context: ./backend
      dockerfile: Dockerfile
    restart: always
    command: celery -A app.celery_app worker --loglevel=info
    environment:
      - ENVIRONMENT=production
      - MONGODB_URL=mongodb://${MONGO_ROOT_USER}:${MONGO_ROOT_PASSWORD}@mongodb:27017
      - REDIS_URL=redis://:${REDIS_PASSWORD}@redis:6379/0
      - CELERY_BROKER_URL=redis://:${REDIS_PASSWORD}@redis:6379/1
    depends_on:
      - mongodb
      - redis
      - mqtt-broker
    networks:
      - openinfra-network

  celery-beat:
    build:
      context: ./backend
      dockerfile: Dockerfile
    restart: always
    command: celery -A app.celery_app beat --loglevel=info
    environment:
      - ENVIRONMENT=production
      - MONGODB_URL=mongodb://${MONGO_ROOT_USER}:${MONGO_ROOT_PASSWORD}@mongodb:27017
      - REDIS_URL=redis://:${REDIS_PASSWORD}@redis:6379/0
      - CELERY_BROKER_URL=redis://:${REDIS_PASSWORD}@redis:6379/1
    depends_on:
      - mongodb
      - redis
    networks:
      - openinfra-network

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    restart: always
    ports:
      - "3000:80"
    networks:
      - openinfra-network

  nginx:
    image: nginx:alpine
    restart: always
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf
      - ./nginx/ssl:/etc/nginx/ssl
    ports:
      - "80:80"
      - "443:443"
    depends_on:
      - backend
      - frontend
    networks:
      - openinfra-network

volumes:
  mongodb_data:
  mongodb_config:
  redis_data:

networks:
  openinfra-network:
    driver: bridge
```

### Optimized Dockerfile (Multi-stage Build)

**backend/Dockerfile**:
```dockerfile
# Stage 1: Build stage
FROM python:3.11-slim as builder

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Stage 2: Production stage
FROM python:3.11-slim

WORKDIR /app

# Install runtime dependencies only
RUN apt-get update && apt-get install -y \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Copy Python dependencies from builder
COPY --from=builder /root/.local /root/.local

# Make sure scripts in .local are usable
ENV PATH=/root/.local/bin:$PATH

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app

USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')"

# Run application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

### Deploy with Docker Compose

```bash
# Copy environment file
cp .env.example .env.prod

# Edit production environment variables
nano .env.prod

# Start services
docker-compose -f docker-compose.prod.yml --env-file .env.prod up -d

# View logs
docker-compose -f docker-compose.prod.yml logs -f backend

# Scale workers
docker-compose -f docker-compose.prod.yml up -d --scale celery-worker=3
```

---

## Kubernetes Deployment (Production)

### Prerequisites

- GKE cluster (Google Kubernetes Engine)
- kubectl configured
- Helm 3.x
- Google Cloud SDK

### Step 1: Create GKE Cluster

```bash
# Set variables
export PROJECT_ID=your-gcp-project-id
export CLUSTER_NAME=openinfra-production
export REGION=us-central1
export ZONE=us-central1-a

# Enable APIs
gcloud services enable container.googleapis.com
gcloud services enable compute.googleapis.com

# Create cluster
gcloud container clusters create $CLUSTER_NAME \
  --region $REGION \
  --num-nodes 3 \
  --machine-type n1-standard-2 \
  --enable-autoscaling \
  --min-nodes 3 \
  --max-nodes 10 \
  --enable-autorepair \
  --enable-autoupgrade \
  --enable-ip-alias \
  --network "default" \
  --subnetwork "default" \
  --enable-stackdriver-kubernetes

# Get credentials
gcloud container clusters get-credentials $CLUSTER_NAME --region $REGION
```

### Step 2: Setup MongoDB Atlas (Managed)

For production, use MongoDB Atlas instead of self-hosting.

1. Create MongoDB Atlas account
2. Create cluster (M10 or higher for production)
3. Enable geospatial indexes
4. Get connection string
5. Whitelist GKE cluster IPs

**Alternative**: Self-hosted MongoDB with persistent volumes

### Step 3: Kubernetes Manifests

**k8s/namespace.yaml**:
```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: openinfra
```

**k8s/configmap.yaml**:
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: openinfra-config
  namespace: openinfra
data:
  PROJECT_NAME: "OpenInfra"
  ENVIRONMENT: "production"
  LOG_LEVEL: "info"
  DATABASE_NAME: "openinfra_prod"
```

**k8s/secrets.yaml** (use sealed-secrets or external secrets in production):
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: openinfra-secrets
  namespace: openinfra
type: Opaque
stringData:
  MONGODB_URL: "mongodb+srv://user:password@cluster.mongodb.net/openinfra_prod"
  REDIS_PASSWORD: "your-redis-password"
  SECRET_KEY: "your-app-secret-key"
  JWT_SECRET_KEY: "your-jwt-secret"
  SENDGRID_API_KEY: "your-sendgrid-key"
  MINIO_ACCESS_KEY: "minioadmin"
  MINIO_SECRET_KEY: "minioadmin"
  MINIO_ENDPOINT: "minio:9000"
  MINIO_BUCKET_NAME: "openinfra-assets"
```

**k8s/redis-deployment.yaml**:
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: redis
  namespace: openinfra
spec:
  replicas: 1
  selector:
    matchLabels:
      app: redis
  template:
    metadata:
      labels:
        app: redis
    spec:
      containers:
      - name: redis
        image: redis:7.0-alpine
        args:
        - redis-server
        - --requirepass
        - $(REDIS_PASSWORD)
        env:
        - name: REDIS_PASSWORD
          valueFrom:
            secretKeyRef:
              name: openinfra-secrets
              key: REDIS_PASSWORD
        ports:
        - containerPort: 6379
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          exec:
            command:
            - redis-cli
            - ping
          initialDelaySeconds: 30
          periodSeconds: 10
---
apiVersion: v1
kind: Service
metadata:
  name: redis
  namespace: openinfra
spec:
  selector:
    app: redis
  ports:
  - port: 6379
    targetPort: 6379
```

**k8s/backend-deployment.yaml**:
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: backend
  namespace: openinfra
spec:
  replicas: 3
  selector:
    matchLabels:
      app: backend
  template:
    metadata:
      labels:
        app: backend
    spec:
      containers:
      - name: backend
        image: gcr.io/${PROJECT_ID}/openinfra-backend:latest
        ports:
        - containerPort: 8000
        env:
        - name: ENVIRONMENT
          value: "production"
        - name: MONGODB_URL
          valueFrom:
            secretKeyRef:
              name: openinfra-secrets
              key: MONGODB_URL
        - name: REDIS_URL
          value: "redis://:$(REDIS_PASSWORD)@redis:6379/0"
        - name: SECRET_KEY
          valueFrom:
            secretKeyRef:
              name: openinfra-secrets
              key: SECRET_KEY
        envFrom:
        - configMapRef:
            name: openinfra-config
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "1Gi"
            cpu: "1000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health/ready
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: backend
  namespace: openinfra
spec:
  selector:
    app: backend
  ports:
  - port: 8000
    targetPort: 8000
  type: ClusterIP
```

**k8s/celery-worker-deployment.yaml**:
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: celery-worker
  namespace: openinfra
spec:
  replicas: 3
  selector:
    matchLabels:
      app: celery-worker
  template:
    metadata:
      labels:
        app: celery-worker
    spec:
      containers:
      - name: celery-worker
        image: gcr.io/${PROJECT_ID}/openinfra-backend:latest
        command: ["celery", "-A", "app.celery_app", "worker", "--loglevel=info"]
        env:
        - name: ENVIRONMENT
          value: "production"
        - name: MONGODB_URL
          valueFrom:
            secretKeyRef:
              name: openinfra-secrets
              key: MONGODB_URL
        - name: CELERY_BROKER_URL
          value: "redis://:$(REDIS_PASSWORD)@redis:6379/1"
        envFrom:
        - configMapRef:
            name: openinfra-config
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "1Gi"
            cpu: "1000m"
```

**k8s/ingress.yaml** (with TLS):
```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: openinfra-ingress
  namespace: openinfra
  annotations:
    kubernetes.io/ingress.class: "nginx"
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    nginx.ingress.kubernetes.io/rate-limit: "100"
spec:
  tls:
  - hosts:
    - api.openinfra.example.com
    - openinfra.example.com
    secretName: openinfra-tls
  rules:
  - host: api.openinfra.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: backend
            port:
              number: 8000
  - host: openinfra.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: frontend
            port:
              number: 80
```

**k8s/hpa.yaml** (Horizontal Pod Autoscaler):
```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: backend-hpa
  namespace: openinfra
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: backend
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
---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: celery-worker-hpa
  namespace: openinfra
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: celery-worker
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

### Step 4: Deploy to Kubernetes

```bash
# Create namespace
kubectl apply -f k8s/namespace.yaml

# Apply configs and secrets
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/secrets.yaml

# Deploy services
kubectl apply -f k8s/redis-deployment.yaml
kubectl apply -f k8s/backend-deployment.yaml
kubectl apply -f k8s/celery-worker-deployment.yaml
kubectl apply -f k8s/frontend-deployment.yaml

# Deploy ingress
kubectl apply -f k8s/ingress.yaml

# Apply HPA
kubectl apply -f k8s/hpa.yaml

# Check status
kubectl get pods -n openinfra
kubectl get svc -n openinfra
kubectl get ingress -n openinfra
```

### Step 5: Setup cert-manager for TLS

```bash
# Install cert-manager
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.0/cert-manager.yaml

# Create Let's Encrypt issuer
cat <<EOF | kubectl apply -f -
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: admin@example.com
    privateKeySecretRef:
      name: letsencrypt-prod
    solvers:
    - http01:
        ingress:
          class: nginx
EOF
```

---

## Database Setup

### MongoDB Production Setup

**Indexes to Create**:
```javascript
// Connect to MongoDB
mongosh "mongodb+srv://cluster.mongodb.net/openinfra_prod" -u admin

// Switch to database
use openinfra_prod

// Create indexes
db.assets.createIndex({ "geometry": "2dsphere" })
db.assets.createIndex({ "asset_code": 1 }, { unique: true })
db.assets.createIndex({ "feature_type": 1 })
db.assets.createIndex({ "status": 1 })
db.assets.createIndex({ "created_at": -1 })

db.maintenance_records.createIndex({ "work_order_number": 1 }, { unique: true })
db.maintenance_records.createIndex({ "asset_id": 1 })
db.maintenance_records.createIndex({ "status": 1, "scheduled_date": 1 })

db.incidents.createIndex({ "incident_number": 1 }, { unique: true })
db.incidents.createIndex({ "location.geometry": "2dsphere" })
db.incidents.createIndex({ "status": 1, "severity": 1 })

db.iot_sensors.createIndex({ "sensor_code": 1 }, { unique: true })
db.iot_sensors.createIndex({ "asset_id": 1 })

// Time-series collection for sensor data
db.createCollection("sensor_data", {
  timeseries: {
    timeField: "timestamp",
    metaField: "sensor_id",
    granularity: "minutes"
  },
  expireAfterSeconds: 31536000  // 1 year
})

db.sensor_data.createIndex({ "sensor_id": 1, "timestamp": -1 })

db.alerts.createIndex({ "status": 1, "severity": 1, "triggered_at": -1 })
db.audit_logs.createIndex({ "timestamp": -1 })
db.audit_logs.createIndex({ "timestamp": 1 }, { expireAfterSeconds: 31536000 })

db.notifications.createIndex({ "user_id": 1, "created_at": -1 })
db.notifications.createIndex({ "expires_at": 1 }, { expireAfterSeconds: 0 })
```

---

## Monitoring & Observability

### Prometheus + Grafana Setup

**prometheus/values.yaml** (Helm):
```yaml
server:
  persistentVolume:
    enabled: true
    size: 50Gi

alertmanager:
  enabled: true

nodeExporter:
  enabled: true

kubeStateMetrics:
  enabled: true
```

```bash
# Install Prometheus
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm install prometheus prometheus-community/kube-prometheus-stack \
  -n monitoring --create-namespace \
  -f prometheus/values.yaml

# Install Grafana
helm install grafana grafana/grafana \
  -n monitoring \
  --set persistence.enabled=true \
  --set adminPassword=admin123
```

### Application Metrics

Add Prometheus metrics to FastAPI:

```python
# app/middleware/prometheus_middleware.py
from prometheus_client import Counter, Histogram, generate_latest
from starlette.middleware.base import BaseHTTPMiddleware

REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"]
)

REQUEST_DURATION = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration",
    ["method", "endpoint"]
)

class PrometheusMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        with REQUEST_DURATION.labels(
            method=request.method,
            endpoint=request.url.path
        ).time():
            response = await call_next(request)
            REQUEST_COUNT.labels(
                method=request.method,
                endpoint=request.url.path,
                status=response.status_code
            ).inc()
        return response

# app/main.py
from prometheus_client import make_asgi_app

metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)
app.add_middleware(PrometheusMiddleware)
```

### Logging with ELK Stack

**elasticsearch/values.yaml**:
```yaml
replicas: 3
minimumMasterNodes: 2
resources:
  requests:
    cpu: "1000m"
    memory: "2Gi"
  limits:
    cpu: "2000m"
    memory: "4Gi"
volumeClaimTemplate:
  resources:
    requests:
      storage: 100Gi
```

```bash
# Install ELK stack
helm repo add elastic https://helm.elastic.co
helm install elasticsearch elastic/elasticsearch -f elasticsearch/values.yaml -n logging --create-namespace
helm install kibana elastic/kibana -n logging
helm install filebeat elastic/filebeat -n logging
```

---

## CI/CD Pipeline

**.github/workflows/deploy.yml**:
```yaml
name: Build and Deploy

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

env:
  PROJECT_ID: ${{ secrets.GCP_PROJECT_ID }}
  GKE_CLUSTER: openinfra-production
  GKE_REGION: us-central1
  IMAGE: openinfra-backend

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements.txt
          pip install pytest pytest-cov

      - name: Run tests
        run: |
          cd backend
          pytest --cov=app --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v3

  build-and-push:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v3

      - name: Set up Google Cloud SDK
        uses: google-github-actions/setup-gcloud@v1
        with:
          service_account_key: ${{ secrets.GCP_SA_KEY }}
          project_id: ${{ secrets.GCP_PROJECT_ID }}

      - name: Configure Docker
        run: gcloud auth configure-docker

      - name: Build Docker image
        run: |
          cd backend
          docker build -t gcr.io/$PROJECT_ID/$IMAGE:$GITHUB_SHA \
                       -t gcr.io/$PROJECT_ID/$IMAGE:latest .

      - name: Push Docker image
        run: |
          docker push gcr.io/$PROJECT_ID/$IMAGE:$GITHUB_SHA
          docker push gcr.io/$PROJECT_ID/$IMAGE:latest

  deploy:
    needs: build-and-push
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Google Cloud SDK
        uses: google-github-actions/setup-gcloud@v1
        with:
          service_account_key: ${{ secrets.GCP_SA_KEY }}
          project_id: ${{ secrets.GCP_PROJECT_ID }}

      - name: Get GKE credentials
        run: |
          gcloud container clusters get-credentials $GKE_CLUSTER --region $GKE_REGION

      - name: Deploy to GKE
        run: |
          kubectl set image deployment/backend \
            backend=gcr.io/$PROJECT_ID/$IMAGE:$GITHUB_SHA \
            -n openinfra

          kubectl rollout status deployment/backend -n openinfra
```

---

## Security Hardening

### 1. Network Policies

**k8s/network-policy.yaml**:
```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: backend-network-policy
  namespace: openinfra
spec:
  podSelector:
    matchLabels:
      app: backend
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          app: nginx-ingress
    ports:
    - protocol: TCP
      port: 8000
  egress:
  - to:
    - podSelector:
        matchLabels:
          app: redis
    ports:
    - protocol: TCP
      port: 6379
  - to:
    - podSelector:
        matchLabels:
          app: mongodb
    ports:
    - protocol: TCP
      port: 27017
```

### 2. Pod Security Standards

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: openinfra
  labels:
    pod-security.kubernetes.io/enforce: restricted
    pod-security.kubernetes.io/audit: restricted
    pod-security.kubernetes.io/warn: restricted
```

### 3. Secrets Management with Google Secret Manager

```python
# app/core/secrets.py
from google.cloud import secretmanager

def get_secret(secret_id: str) -> str:
    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/{PROJECT_ID}/secrets/{secret_id}/versions/latest"
    response = client.access_secret_version(request={"name": name})
    return response.payload.data.decode("UTF-8")

# Usage
MONGODB_URL = get_secret("mongodb-url")
JWT_SECRET = get_secret("jwt-secret")
```

---

## Backup & Disaster Recovery

### MongoDB Atlas Backup

MongoDB Atlas provides automatic backups:
- Point-in-time recovery
- Snapshot retention: 7 days
- Backup frequency: Continuous

### Application Data Backup

**backup-cronjob.yaml**:
```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: mongodb-backup
  namespace: openinfra
spec:
  schedule: "0 2 * * *"  # Daily at 2 AM
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: backup
            image: mongo:7.0
            command:
            - /bin/sh
            - -c
            - |
              mongodump --uri="$MONGODB_URL" --gzip --archive=/backup/backup-$(date +%Y%m%d).gz
              gsutil cp /backup/backup-$(date +%Y%m%d).gz gs://openinfra-backups/
            env:
            - name: MONGODB_URL
              valueFrom:
                secretKeyRef:
                  name: openinfra-secrets
                  key: MONGODB_URL
            volumeMounts:
            - name: backup
              mountPath: /backup
          volumes:
          - name: backup
            emptyDir: {}
          restartPolicy: OnFailure
```

### Disaster Recovery Plan

1. **RTO (Recovery Time Objective)**: 4 hours
2. **RPO (Recovery Point Objective)**: 24 hours

**Recovery Steps**:
```bash
# 1. Restore MongoDB from backup
mongorestore --uri="mongodb+srv://cluster.mongodb.net" --gzip --archive=backup.gz

# 2. Redeploy application
kubectl apply -f k8s/

# 3. Verify services
kubectl get pods -n openinfra
curl https://api.openinfra.example.com/health

# 4. Run smoke tests
pytest tests/smoke/
```

---

## Conclusion

This deployment guide covers:
- ✅ Local development setup
- ✅ Docker Compose deployment
- ✅ Production Kubernetes deployment on GKE
- ✅ Database setup and indexing
- ✅ Monitoring with Prometheus/Grafana
- ✅ Logging with ELK stack
- ✅ CI/CD with GitHub Actions
- ✅ Security hardening
- ✅ Backup and disaster recovery

**Production Checklist**:
- [ ] MongoDB Atlas cluster provisioned
- [ ] GKE cluster created and configured
- [ ] Secrets stored in Secret Manager
- [ ] TLS certificates configured
- [ ] Monitoring dashboards set up
- [ ] Backup jobs scheduled
- [ ] Load testing completed
- [ ] Security audit passed
- [ ] Documentation reviewed

**Next Steps**: Follow the project plan phases to implement features incrementally.
