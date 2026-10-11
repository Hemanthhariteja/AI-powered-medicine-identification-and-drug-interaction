# Quick Start Guide

Get the Medicine AI System running in under 5 minutes!

## Prerequisites
- Python 3.11+ installed
- 2GB free RAM
- (Optional) Docker Desktop for containerized deployment

## Option 1: Local Development (5 minutes)

### Step 1: Setup Environment
```powershell
# Navigate to project directory
cd medicine_ai_system

# Create virtual environment
python -m venv .venv

# Activate environment
.\.venv\Scripts\Activate.ps1

# Install dependencies (takes 2-3 minutes)
pip install -r requirements.txt
```

### Step 2: Generate Sample Data
```powershell
# Create sample pill images
python generate_samples.py
```
**Output**: Creates 5 sample images per drug class (aspirin, ibuprofen, acetaminophen, metformin)

### Step 3: Run Application
```powershell
# Start Flask development server
python run.py
```

### Step 4: Access Application
Open browser to: **http://localhost:5000**

**Try these features:**
- 📸 **Identify Pills**: Upload image on home page
- 💊 **Add Medications**: Type drug name and click Add
- ⚠️ **Check Interactions**: Click "Check Interactions" button
- 🔍 **Search Drugs**: Use search bar for real-time filtering

## Option 2: Docker Deployment (3 minutes)

### Step 1: Build Container
```powershell
# Build Docker image
docker-compose build
```

### Step 2: Run Container
```powershell
# Start application
docker-compose up -d

# Check status
docker-compose ps
```

### Step 3: Access Application
Open browser to: **http://localhost:5000**

### Stop Application
```powershell
docker-compose down
```

## Optional: Train Custom Model

**Note**: Training requires actual pill images (not just colored samples).

```powershell
# Add real images to data/pills_dataset/<drug_name>/
# Then train:
python train_model.py --epochs 10

# Model saved to: models/trained_models/pill_mobilenetv2.keras
```

## What's Included

### Sample Dataset
- 20 placeholder images (5 per drug class)
- Classes: Aspirin, Ibuprofen, Acetaminophen, Metformin
- Located in: `data/pills_dataset/`

### Pre-configured Features
- ✅ Flask web server with API endpoints
- ✅ Bootstrap 5 responsive UI
- ✅ Drag-and-drop file upload
- ✅ NIH RxNav API integration (live drug interactions)
- ✅ Session-based medication tracking
- ✅ Confidence threshold validation
- ✅ Error handling and input validation

## Troubleshooting

### "No module named 'flask'"
```powershell
# Ensure virtual environment is activated
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### Port 5000 already in use
```powershell
# Change port in run.py:
# app.run(debug=True, port=5001)
```

### "No trained model found" warning
This is expected! The system uses placeholder predictions until you train a real model with `python train_model.py`.

## Next Steps

1. **Add Real Data**: Replace sample images with actual pill photos
2. **Train Model**: Run `python train_model.py` with ≥50 images per class
3. **Configure API**: Copy `.env.example` to `.env` and customize
4. **Deploy**: Follow `DEPLOYMENT.md` for production setup

## API Examples

### Identify Pill (cURL)
```bash
curl -X POST http://localhost:5000/api/identify-pill \
  -F "file=@pill_image.jpg"
```

### Check Interactions (cURL)
```bash
curl -X POST http://localhost:5000/api/check-interactions \
  -H "Content-Type: application/json" \
  -d '{"medications": ["Aspirin", "Ibuprofen"]}'
```

### Search Drugs
```bash
curl "http://localhost:5000/api/search-drugs?q=ibu"
```

## Documentation

- **Full Documentation**: `README.md`
- **Deployment Guide**: `DEPLOYMENT.md`
- **Configuration**: `config.py` and `.env.example`

## Support

- 📖 Check `README.md` for detailed features
- 🐛 Found a bug? Check `tests/` for test examples
- 🚀 Ready for production? See `DEPLOYMENT.md`

---

**Estimated Setup Time**: 5 minutes  
**System Requirements**: Python 3.11+, 2GB RAM  
**Production Ready**: Follow DEPLOYMENT.md for security hardening
