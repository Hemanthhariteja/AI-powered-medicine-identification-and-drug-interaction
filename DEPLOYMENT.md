# Deployment Guide

This guide covers production deployment of the Medicine AI System across various environments.

## Table of Contents
1. [Pre-Deployment Checklist](#pre-deployment-checklist)
2. [Local Docker Deployment](#local-docker-deployment)
3. [Cloud Platform Deployment](#cloud-platform-deployment)
4. [Production Configuration](#production-configuration)
5. [Monitoring & Maintenance](#monitoring--maintenance)
6. [Troubleshooting](#troubleshooting)

## Pre-Deployment Checklist

### Security Requirements
- [ ] **SECRET_KEY**: Generate cryptographically secure key
  ```powershell
  python -c "import secrets; print(secrets.token_hex(32))"
  ```
- [ ] **Environment Variables**: Never commit `.env` to version control
- [ ] **HTTPS**: Ensure TLS/SSL certificates are configured
- [ ] **Database Credentials**: Use strong passwords, rotate regularly
- [ ] **API Keys**: Secure any external API credentials
- [ ] **CORS**: Configure appropriate Cross-Origin settings

### Application Requirements
- [ ] **Model Training**: Train model on production-quality dataset
- [ ] **Model Validation**: Verify >80% accuracy on test set
- [ ] **Dependencies**: Lock versions in `requirements.txt`
- [ ] **Database Migrations**: Test schema changes
- [ ] **Static Assets**: Optimize images, minify CSS/JS
- [ ] **Error Pages**: Customize 404/500 templates

### Infrastructure Requirements
- [ ] **Compute Resources**: Minimum 2GB RAM, 2 vCPU
- [ ] **Storage**: 10GB for models, database, logs
- [ ] **Network**: Port 5000 accessible (or behind reverse proxy)
- [ ] **Backup Strategy**: Automated database and model backups
- [ ] **Monitoring**: Health checks, alerting configured

## Local Docker Deployment

### Using Docker Compose (Recommended)

**1. Configure environment:**
```powershell
# Copy template
Copy-Item .env.example .env

# Edit .env with production values
notepad .env
```

**2. Build and run:**
```powershell
# Build image
docker-compose build

# Run in detached mode
docker-compose up -d

# View logs
docker-compose logs -f

# Check health
curl http://localhost:5000
```

**3. Access application:**
- Web interface: http://localhost:5000
- API endpoints: http://localhost:5000/api/*

**4. Stop deployment:**
```powershell
docker-compose down

# Remove volumes as well
docker-compose down -v
```

### Manual Docker Build

```powershell
# Build image
docker build -t medicine-ai:latest .

# Run container
docker run -d `
  --name medicine-ai-app `
  -p 5000:5000 `
  -e FLASK_ENV=production `
  -e SECRET_KEY=your-secret-key-here `
  -e MIN_CONFIDENCE_THRESHOLD=0.6 `
  -v ${PWD}/data:/app/data `
  -v ${PWD}/models:/app/models `
  -v medicine-ai-uploads:/app/uploaded_images `
  medicine-ai:latest

# View logs
docker logs -f medicine-ai-app

# Stop container
docker stop medicine-ai-app
docker rm medicine-ai-app
```

## Cloud Platform Deployment

### AWS Deployment

#### Option 1: ECS Fargate (Recommended)

**1. Push image to ECR:**
```bash
# Create ECR repository
aws ecr create-repository --repository-name medicine-ai

# Get login token
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-east-1.amazonaws.com

# Tag and push
docker tag medicine-ai:latest <account-id>.dkr.ecr.us-east-1.amazonaws.com/medicine-ai:latest
docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/medicine-ai:latest
```

**2. Create ECS task definition (`task-definition.json`):**
```json
{
  "family": "medicine-ai-task",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "512",
  "memory": "1024",
  "containerDefinitions": [
    {
      "name": "medicine-ai",
      "image": "<account-id>.dkr.ecr.us-east-1.amazonaws.com/medicine-ai:latest",
      "portMappings": [{"containerPort": 5000, "protocol": "tcp"}],
      "environment": [
        {"name": "FLASK_ENV", "value": "production"},
        {"name": "MIN_CONFIDENCE_THRESHOLD", "value": "0.6"}
      ],
      "secrets": [
        {"name": "SECRET_KEY", "valueFrom": "arn:aws:secretsmanager:..."}
      ],
      "mountPoints": [
        {
          "sourceVolume": "models",
          "containerPath": "/app/models"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/medicine-ai",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ],
  "volumes": [
    {
      "name": "models",
      "efsVolumeConfiguration": {
        "fileSystemId": "fs-xxxxx",
        "rootDirectory": "/models"
      }
    }
  ]
}
```

**3. Create ECS service:**
```bash
# Register task definition
aws ecs register-task-definition --cli-input-json file://task-definition.json

# Create service
aws ecs create-service \
  --cluster medicine-ai-cluster \
  --service-name medicine-ai-service \
  --task-definition medicine-ai-task \
  --desired-count 2 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-xxx],securityGroups=[sg-xxx],assignPublicIp=ENABLED}"
```

**4. Configure Application Load Balancer:**
- Create ALB targeting port 5000
- Configure health check: `/` endpoint
- Set up HTTPS listener with ACM certificate
- Update security groups for ECS tasks

#### Option 2: Elastic Beanstalk

```bash
# Install EB CLI
pip install awsebcli

# Initialize
eb init -p docker medicine-ai-app --region us-east-1

# Create environment
eb create medicine-ai-prod --instance-type t3.medium

# Deploy
eb deploy

# Configure environment variables
eb setenv FLASK_ENV=production SECRET_KEY=your-key MIN_CONFIDENCE_THRESHOLD=0.6

# View logs
eb logs
```

**Infrastructure as Code (CloudFormation):**
See `aws-cloudformation-template.yaml` for complete stack definition.

### Azure Deployment

#### Option 1: Azure Container Instances

**1. Push to Azure Container Registry:**
```bash
# Create ACR
az acr create --resource-group medicine-ai-rg --name medicineaiacr --sku Basic

# Login
az acr login --name medicineaiacr

# Tag and push
docker tag medicine-ai:latest medicineaiacr.azurecr.io/medicine-ai:latest
docker push medicineaiacr.azurecr.io/medicine-ai:latest
```

**2. Deploy container instance:**
```bash
# Create container instance
az container create \
  --resource-group medicine-ai-rg \
  --name medicine-ai-instance \
  --image medicineaiacr.azurecr.io/medicine-ai:latest \
  --cpu 1 \
  --memory 2 \
  --registry-login-server medicineaiacr.azurecr.io \
  --registry-username <username> \
  --registry-password <password> \
  --dns-name-label medicine-ai-app \
  --ports 5000 \
  --environment-variables FLASK_ENV=production MIN_CONFIDENCE_THRESHOLD=0.6 \
  --secure-environment-variables SECRET_KEY=your-secret-key

# Get FQDN
az container show --resource-group medicine-ai-rg --name medicine-ai-instance --query ipAddress.fqdn
```

#### Option 2: Azure App Service

```bash
# Create App Service plan
az appservice plan create --name medicine-ai-plan --resource-group medicine-ai-rg --is-linux --sku B1

# Create web app
az webapp create --resource-group medicine-ai-rg --plan medicine-ai-plan --name medicine-ai-webapp --deployment-container-image-name medicineaiacr.azurecr.io/medicine-ai:latest

# Configure environment
az webapp config appsettings set --resource-group medicine-ai-rg --name medicine-ai-webapp --settings \
  FLASK_ENV=production \
  SECRET_KEY=your-secret-key \
  MIN_CONFIDENCE_THRESHOLD=0.6

# Enable continuous deployment
az webapp deployment container config --enable-cd true --name medicine-ai-webapp --resource-group medicine-ai-rg
```

### Google Cloud Deployment

#### Option 1: Cloud Run (Recommended for Stateless)

```bash
# Enable APIs
gcloud services enable run.googleapis.com containerregistry.googleapis.com

# Build and push to Container Registry
gcloud builds submit --tag gcr.io/PROJECT_ID/medicine-ai

# Deploy to Cloud Run
gcloud run deploy medicine-ai \
  --image gcr.io/PROJECT_ID/medicine-ai \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 2Gi \
  --cpu 1 \
  --set-env-vars FLASK_ENV=production,MIN_CONFIDENCE_THRESHOLD=0.6 \
  --set-secrets SECRET_KEY=medicine-ai-secret:latest

# Get service URL
gcloud run services describe medicine-ai --region us-central1 --format='value(status.url)'
```

#### Option 2: Google Kubernetes Engine (GKE)

**1. Create GKE cluster:**
```bash
gcloud container clusters create medicine-ai-cluster \
  --num-nodes=3 \
  --machine-type=n1-standard-2 \
  --region=us-central1

# Get credentials
gcloud container clusters get-credentials medicine-ai-cluster --region us-central1
```

**2. Deploy application (`k8s-deployment.yaml`):**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: medicine-ai
spec:
  replicas: 3
  selector:
    matchLabels:
      app: medicine-ai
  template:
    metadata:
      labels:
        app: medicine-ai
    spec:
      containers:
      - name: medicine-ai
        image: gcr.io/PROJECT_ID/medicine-ai:latest
        ports:
        - containerPort: 5000
        env:
        - name: FLASK_ENV
          value: "production"
        - name: MIN_CONFIDENCE_THRESHOLD
          value: "0.6"
        - name: SECRET_KEY
          valueFrom:
            secretKeyRef:
              name: medicine-ai-secrets
              key: secret-key
        resources:
          requests:
            memory: "1Gi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "1000m"
        livenessProbe:
          httpGet:
            path: /
            port: 5000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /
            port: 5000
          initialDelaySeconds: 5
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: medicine-ai-service
spec:
  type: LoadBalancer
  selector:
    app: medicine-ai
  ports:
  - protocol: TCP
    port: 80
    targetPort: 5000
```

**3. Apply configuration:**
```bash
# Create secret
kubectl create secret generic medicine-ai-secrets --from-literal=secret-key=your-secret-key

# Deploy
kubectl apply -f k8s-deployment.yaml

# Get external IP
kubectl get service medicine-ai-service
```

## Production Configuration

### Database Setup (PostgreSQL)

**1. Update configuration:**
```python
# config.py - ProductionConfig
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://user:pass@host:5432/medicine_db')
```

**2. Install PostgreSQL adapter:**
```powershell
pip install psycopg2-binary
```

**3. Initialize database:**
```powershell
# Set environment variable
$env:DATABASE_URL = "postgresql://user:pass@host:5432/medicine_db"

# Run migrations (if using Alembic)
alembic upgrade head

# Or initialize directly
python -c "from src.utils.database import init_db; init_db()"
```

### Reverse Proxy (Nginx)

**nginx.conf:**
```nginx
upstream medicine_ai {
    server localhost:5000;
}

server {
    listen 80;
    server_name medicine-ai.example.com;
    
    # Redirect to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name medicine-ai.example.com;
    
    ssl_certificate /etc/letsencrypt/live/medicine-ai.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/medicine-ai.example.com/privkey.pem;
    
    client_max_body_size 10M;
    
    location / {
        proxy_pass http://medicine_ai;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    location /static {
        alias /app/src/static;
        expires 30d;
    }
}
```

### WSGI Server (Gunicorn)

**1. Install Gunicorn:**
```powershell
pip install gunicorn
```

**2. Update Dockerfile CMD:**
```dockerfile
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "--timeout", "120", "run:app"]
```

**3. Create gunicorn config (`gunicorn_config.py`):**
```python
import multiprocessing

bind = "0.0.0.0:5000"
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "sync"
timeout = 120
keepalive = 5
max_requests = 1000
max_requests_jitter = 50

accesslog = "-"
errorlog = "-"
loglevel = "info"
```

## Monitoring & Maintenance

### Health Checks

**Built-in endpoint:**
```python
# Already configured in Dockerfile HEALTHCHECK
# GET / returns 200 if app is running
```

**External monitoring tools:**
- **Uptime Robot**: Free tier available
- **Pingdom**: Comprehensive monitoring
- **New Relic**: APM and infrastructure monitoring
- **Datadog**: Full-stack observability

### Logging

**Application logs:**
```python
# Add to app.py
import logging
from logging.handlers import RotatingFileHandler

if not app.debug:
    file_handler = RotatingFileHandler('logs/medicine_ai.log', maxBytes=10240000, backupCount=10)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)
    app.logger.info('Medicine AI startup')
```

**Centralized logging:**
- **CloudWatch Logs** (AWS)
- **Azure Monitor** (Azure)
- **Cloud Logging** (GCP)
- **Papertrail** (Platform-agnostic)

### Metrics Collection

**Prometheus integration:**
```python
# Install prometheus_flask_exporter
pip install prometheus-flask-exporter

# Add to app.py
from prometheus_flask_exporter import PrometheusMetrics

metrics = PrometheusMetrics(app)
metrics.info('app_info', 'Application info', version='1.0.0')
```

### Backup Strategy

**Database backups:**
```bash
# PostgreSQL dump (daily cron job)
0 2 * * * pg_dump -U user medicine_db > /backups/medicine_db_$(date +\%Y\%m\%d).sql

# Retention: Keep 7 daily, 4 weekly, 12 monthly
```

**Model backups:**
```bash
# Sync to S3/Azure Blob/GCS (after training)
aws s3 sync ./models/trained_models/ s3://medicine-ai-models/$(date +\%Y\%m\%d)/
```

### Update Strategy

**Rolling updates (Kubernetes):**
```bash
# Update image
kubectl set image deployment/medicine-ai medicine-ai=gcr.io/PROJECT_ID/medicine-ai:v2.0

# Monitor rollout
kubectl rollout status deployment/medicine-ai

# Rollback if needed
kubectl rollout undo deployment/medicine-ai
```

**Blue-green deployment (Docker Compose):**
```bash
# Deploy new version as "green"
docker-compose -f docker-compose.green.yml up -d

# Test green deployment
curl http://localhost:5001

# Switch load balancer to green
# Update nginx upstream

# Stop old "blue" deployment
docker-compose down
```

## Troubleshooting

### Container Won't Start

**Check logs:**
```bash
docker logs medicine-ai-app
```

**Common issues:**
- Missing environment variables: Verify `.env` file
- Port already in use: Change port mapping `-p 5001:5000`
- Volume mount issues: Check directory permissions

### High Memory Usage

**Identify cause:**
```bash
docker stats medicine-ai-app
```

**Solutions:**
- Reduce model size or use quantization
- Decrease number of Gunicorn workers
- Enable model unloading after inference
- Increase container memory limit

### Slow Response Times

**Profile application:**
```python
# Add flask-profiler
pip install flask_profiler

# Add to app.py
app.config["flask_profiler"] = {
    "enabled": True,
    "storage": {"engine": "sqlite"},
    "basicAuth": {"enabled": True, "username": "admin", "password": "admin"}
}
```

**Common bottlenecks:**
- Model loading on every request: Implement singleton pattern
- No API caching: Verify LRU cache is working
- Database connection pooling: Configure SQLAlchemy pool settings
- Unoptimized images: Resize before upload

### Database Connection Errors

**Check connection:**
```python
# Test database connectivity
python -c "from src.utils.database import init_db; init_db(); print('Connected')"
```

**Solutions:**
- Verify `DATABASE_URL` is correct
- Check network connectivity to database server
- Ensure database user has necessary permissions
- Increase connection pool size in SQLAlchemy

### SSL/TLS Certificate Issues

**Obtain Let's Encrypt certificate:**
```bash
# Install certbot
sudo apt-get install certbot python3-certbot-nginx

# Obtain certificate
sudo certbot --nginx -d medicine-ai.example.com

# Auto-renewal (already configured by certbot)
sudo certbot renew --dry-run
```

## Support & Resources

- **Documentation**: README.md and inline code comments
- **Issue Tracker**: GitHub Issues
- **Community**: Stack Overflow tag `medicine-ai`
- **Security**: Email security@example.com for vulnerabilities

---

**Last Updated**: 2025
**Version**: 1.0
