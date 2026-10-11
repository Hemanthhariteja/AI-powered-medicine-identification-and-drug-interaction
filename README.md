# Medicine AI System

An AI-powered medicine identification and drug interaction checking platform using TensorFlow/Keras MobileNetV2 and NIH RxNav API integration.

## Features

### 🔬 Core Capabilities
- **Pill Identification**: Upload pill images for AI-powered identification using MobileNetV2 transfer learning
- **Drug Interaction Checking**: Real-time interaction analysis via NIH RxNav API with local fallback
- **Medication Management**: Track personal medications with interactive web interface
- **Severity Analysis**: Automatic severity classification (major/moderate/minor) with contraindication detection
- **Confidence Scoring**: Configurable thresholds for pill identification accuracy

### 🏗️ Technical Features
- Flask blueprint architecture with RESTful API
- TensorFlow 2.17 with Keras for deep learning
- Bootstrap 5 responsive UI with drag-and-drop upload
- LRU-cached API client for performance
- Comprehensive input validation and error handling
- Docker containerization for easy deployment
- SQLAlchemy ORM with SQLite database

## Project Structure

```
medicine_ai_system/
├── src/
│   ├── app.py                      # Flask application factory
│   ├── routes.py                   # Frontend & API blueprints
│   ├── models/
│   │   ├── pill_model.py          # SQLAlchemy ORM models
│   │   ├── model_training.py      # MobileNetV2 training pipeline
│   │   └── pill_predictor.py      # Inference wrapper
│   ├── utils/
│   │   ├── data_loader.py         # Dataset preparation
│   │   ├── metrics.py             # Model evaluation
│   │   ├── image_processing.py    # Image preprocessing
│   │   ├── interaction_checker.py # Drug interaction analysis
│   │   ├── api_client.py          # NIH RxNav integration
│   │   ├── response_format.py     # Severity scoring logic
│   │   ├── validators.py          # Input validation
│   │   └── database.py            # Database initialization
│   ├── templates/                  # Jinja2 HTML templates
│   └── static/
│       ├── css/style.css          # Custom styles
│       └── js/app.js              # Frontend interactivity
├── data/
│   ├── pills_dataset/             # Training images (aspirin, ibuprofen, etc.)
│   ├── sample_interactions.json   # Local interaction fallback
│   └── sample_data.csv            # Pill metadata
├── models/trained_models/         # Saved .keras models and labels
├── tests/                         # Pytest test suite
├── Dockerfile                     # Multi-stage Docker build
├── docker-compose.yml             # Local deployment config
├── .env.example                   # Environment variable template
└── requirements.txt               # Python dependencies
```

## Quick Start

### Local Development

```powershell
# 1. Create virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# 2. Install dependencies
pip install -r requirements.txt

# 3. Generate sample dataset (or add your own images)
python generate_samples.py

# 4. Configure environment (optional)
copy .env.example .env
# Edit .env with your settings

# 5. Run development server
python run.py

# 6. Visit http://localhost:5000
```

### Docker Deployment

```powershell
# Build and run with Docker Compose
docker-compose up --build

# Or build manually
docker build -t medicine-ai:latest .
docker run -p 5000:5000 -v ${PWD}/data:/app/data -v ${PWD}/models:/app/models medicine-ai:latest
```

## Dataset Setup

### Option 1: Use Sample Images (Testing)
```powershell
# Generate colored placeholder images
python generate_samples.py
```

### Option 2: Real Dataset (Production)
Organize images by drug class in `data/pills_dataset/`:

```
data/pills_dataset/
├── aspirin/
│   ├── img_001.jpg
│   ├── img_002.jpg
│   └── ...
├── ibuprofen/
│   ├── img_001.jpg
│   └── ...
├── acetaminophen/
│   └── ...
└── metformin/
    └── ...
```

**Requirements:**
- JPEG/PNG format
- Recommended: 224x224px or larger
- Minimum 20 images per class
- Varied lighting, angles, backgrounds

## Model Training

### Basic Training
```powershell
# Train with default settings (10 epochs total: 5 frozen + 5 fine-tuning)
python train_model.py

# Custom training
python train_model.py --epochs 20 --output custom_model.keras
```

### Training Pipeline
1. **Data Loading**: Stratified 70/15/15 train/val/test split via `data_loader.py`
2. **Augmentation**: Random flip, rotation (±0.2), zoom (±0.2), brightness (±0.2)
3. **Base Model**: MobileNetV2 (ImageNet weights, frozen initially)
4. **Phase 1**: Train classification head (5 epochs @ 1e-3 learning rate)
5. **Phase 2**: Fine-tune top layers (5 epochs @ 1e-4 learning rate)
6. **Output**: 
   - `models/trained_models/pill_mobilenetv2.keras`
   - `models/trained_models/pill_mobilenetv2_labels.json`

### Evaluation Metrics
- Accuracy, Precision, Recall, F1-Score
- Confusion matrix visualization
- Per-class performance report

## Configuration

### Environment Variables (.env)
```bash
# Flask settings
FLASK_ENV=development              # development | testing | production
SECRET_KEY=your-secret-key-here    # Change in production!
DATABASE_URL=sqlite:///medicine.db

# ML settings
MIN_CONFIDENCE_THRESHOLD=0.5       # 0.0-1.0 (production: 0.6)
MAX_FILE_SIZE_MB=10

# API settings
RXNAV_API_TIMEOUT=10               # seconds
ENABLE_API_FALLBACK=true

# Session settings
PERMANENT_SESSION_LIFETIME=3600    # seconds (1 hour)
```

### Configuration Classes (`config.py`)
- **DevelopmentConfig**: Debug mode, SQLite, min confidence 0.5
- **TestingConfig**: Testing flag enabled, in-memory database
- **ProductionConfig**: Stricter thresholds (0.6), secure cookies, HTTPS-only

## API Reference

### Frontend Routes
- `GET /` - Home page with upload and medication list
- `GET /identify` - Pill identification interface
- `GET /medications` - Medication management page
- `GET /interactions` - Interaction checker interface

### API Endpoints

#### Identify Pill
```http
POST /api/identify-pill
Content-Type: multipart/form-data

file: <image_file>
```
**Response:**
```json
{
  "success": true,
  "drug_name": "Aspirin",
  "confidence": 0.87,
  "acceptable": true,
  "warning": null,
  "top_predictions": [
    {"label": "Aspirin", "confidence": 0.87},
    {"label": "Acetaminophen", "confidence": 0.09}
  ]
}
```

#### Add Medication
```http
POST /api/add-medication
Content-Type: application/json

{
  "name": "Ibuprofen"
}
```

#### Check Interactions
```http
POST /api/check-interactions
Content-Type: application/json

{
  "medications": ["Aspirin", "Ibuprofen"]
}
```
**Response:**
```json
{
  "interactions": [
    {
      "drug_a": "Aspirin",
      "drug_b": "Ibuprofen",
      "severity": "moderate",
      "description": "May increase risk of bleeding",
      "contraindicated": false,
      "suggestions": ["Monitor for bleeding", "Consider spacing doses"]
    }
  ]
}
```

#### Search Drugs
```http
GET /api/search-drugs?q=ibu
```

## Drug Interaction System

### API Integration
- **Primary**: NIH RxNav REST API (https://rxnav.nlm.nih.gov/REST)
- **Fallback**: Local `data/sample_interactions.json`
- **Caching**: LRU cache (1024 entries) for performance
- **Timeout**: Configurable (default 10s)

### Severity Classification
- **Major**: Significant risk, may require intervention
- **Moderate**: Monitor closely, may need dosage adjustment
- **Minor**: Usually safe, minimal clinical significance

### Contraindication Detection
Automatic flagging of drug pairs that should not be combined.

## Testing

### Run All Tests
```powershell
# Run with pytest
pytest -v

# With coverage
pytest --cov=src --cov-report=html
```

### Test Categories
- **Unit Tests**: `tests/test_models.py`, `tests/test_app.py`
- **Integration Tests**: `tests/test_integration.py` (complete user flow)
- **Model Tests**: Training pipeline, predictor, data loader

## Deployment

### Production Checklist

#### Security
- [ ] Generate strong `SECRET_KEY` (use `secrets.token_hex(32)`)
- [ ] Set `FLASK_ENV=production`
- [ ] Enable HTTPS (set `SESSION_COOKIE_SECURE=true`)
- [ ] Review CORS settings if using separate frontend
- [ ] Limit file upload size (`MAX_FILE_SIZE_MB`)

#### Performance
- [ ] Use production WSGI server (Gunicorn/uWSGI instead of Flask dev server)
- [ ] Configure reverse proxy (Nginx) for static files
- [ ] Enable compression (gzip)
- [ ] Set up CDN for static assets

#### Database
- [ ] Migrate from SQLite to PostgreSQL/MySQL for production
- [ ] Configure connection pooling
- [ ] Set up regular backups
- [ ] Add database migrations (Alembic)

#### Monitoring
- [ ] Set up logging to files/external service
- [ ] Configure error tracking (Sentry)
- [ ] Add health check endpoint monitoring
- [ ] Set up uptime monitoring

#### Model Management
- [ ] Version trained models with timestamps
- [ ] Implement model rollback mechanism
- [ ] Schedule retraining pipeline
- [ ] Monitor prediction confidence drift

### Docker Production

#### Build Optimization
```bash
# Multi-stage build reduces image size
docker build -t medicine-ai:v1.0 --target production .

# Push to registry
docker tag medicine-ai:v1.0 your-registry/medicine-ai:v1.0
docker push your-registry/medicine-ai:v1.0
```

#### Kubernetes Deployment (Example)
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: medicine-ai
spec:
  replicas: 3
  template:
    spec:
      containers:
      - name: app
        image: your-registry/medicine-ai:v1.0
        env:
        - name: FLASK_ENV
          value: "production"
        - name: SECRET_KEY
          valueFrom:
            secretKeyRef:
              name: app-secrets
              key: flask-secret
        volumeMounts:
        - name: models
          mountPath: /app/models
      volumes:
      - name: models
        persistentVolumeClaim:
          claimName: medicine-ai-models
```

### Cloud Deployment Options

#### AWS (Elastic Beanstalk / ECS)
- Use `Dockerfile` with ECS Fargate
- Store models in S3, mount via EFS
- Use RDS for PostgreSQL
- CloudWatch for monitoring

#### Azure (App Service / Container Instances)
- Deploy Docker image to Azure Container Registry
- Use Azure Database for PostgreSQL
- Azure Blob Storage for models
- Application Insights for monitoring

#### Google Cloud (Cloud Run / GKE)
- Deploy container to Cloud Run
- Use Cloud SQL for database
- Cloud Storage for models
- Cloud Logging for monitoring

## Troubleshooting

### Common Issues

**"No module named 'PIL'"**
```powershell
pip install Pillow
```

**"No trained model found"**
- Run `python train_model.py` to train a model
- Or use the placeholder predictor (returns random results)

**"RxNav API timeout"**
- Check internet connection
- Increase `RXNAV_API_TIMEOUT` in config
- System will fallback to local `sample_interactions.json`

**Low prediction confidence**
- Ensure good quality pill images (clear, well-lit, centered)
- Increase training data (minimum 50 images per class recommended)
- Adjust `MIN_CONFIDENCE_THRESHOLD` if needed

**Docker container exits immediately**
- Check logs: `docker logs <container_id>`
- Ensure data/models directories exist and are mounted
- Verify environment variables in docker-compose.yml

## Performance Notes

- **Model Inference**: ~50-200ms per image (CPU), ~10-50ms (GPU)
- **API Response**: <500ms for interaction checks (with cache)
- **Training Time**: ~10-30 minutes for 10 epochs (depends on dataset size and hardware)
- **Memory Usage**: ~500MB base + ~200MB per loaded model

## Known Limitations

1. **Pill Dataset**: Requires substantial labeled data for production accuracy
2. **Interaction API**: NIH RxNav API has rate limits; local fallback is limited
3. **Multi-pill Images**: Current system assumes single pill per image
4. **Drug Names**: Standardization needed for generic/brand name matching
5. **Real-time**: Not suitable for emergency medical decisions

## Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Add tests for new functionality
4. Ensure all tests pass (`pytest`)
5. Commit changes (`git commit -m 'Add amazing feature'`)
6. Push to branch (`git push origin feature/amazing-feature`)
7. Open Pull Request

## License

This project is provided for educational and instructional purposes. For production medical applications:
- Ensure compliance with HIPAA, GDPR, and local regulations
- Obtain necessary medical software certifications
- Implement proper audit logging and data encryption
- Consult legal counsel before deployment

**Disclaimer**: This system is NOT a substitute for professional medical advice, diagnosis, or treatment. Always consult qualified healthcare professionals.

## Support

For issues, questions, or contributions:
- Open GitHub issue
- Review existing documentation
- Check troubleshooting section above
