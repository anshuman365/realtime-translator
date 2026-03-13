# Quick Start Guide

Get your Real-Time Translator running in under 10 minutes!

## 🚀 Deploy to Render (Fastest - Recommended)

### Prerequisites
- GitHub account
- Render account (https://render.com - free tier available)

### Steps

1. **Upload to GitHub**
   ```bash
   cd realtime-translator
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin <your-github-repo>
   git push -u origin main
   ```

2. **Deploy on Render**
   - Go to https://dashboard.render.com
   - Click "New" → "Blueprint"
   - Select your repository
   - Render will detect `render.yaml` automatically
   - Set environment variables:
     - `ADMIN_PASSWORD`: Create a strong password
     - `SECRET_KEY`: Generate with `openssl rand -hex 32`
   - Click "Apply"

3. **Wait for Deployment** (10-15 minutes first time)
   - Models will download automatically
   - Monitor progress in Render logs

4. **Access Your App**
   - URL: `https://your-app-name.onrender.com`
   - Admin: `https://your-app-name.onrender.com/admin`

**Done!** 🎉

---

## 💻 Local Development

### Prerequisites
- Python 3.9+
- Node.js 16+
- 8GB+ RAM
- 2GB+ disk space (for models)

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Setup environment
cp .env.example .env
# Edit .env with your settings

# Download models (takes 5-10 minutes)
cd ..
chmod +x scripts/download_models.sh
./scripts/download_models.sh

# Initialize database
cd backend
python -c "from app.utils.database import init_db; import asyncio; asyncio.run(init_db())"

# Run server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Backend will be available at http://localhost:8000

### Frontend Setup

Open a new terminal:

```bash
cd frontend

# Install dependencies
npm install

# Setup environment
cp .env.example .env
# Edit if needed (defaults are fine for local dev)

# Run development server
npm start
```

Frontend will open at http://localhost:3000

### Test the Application

1. **Main App**: http://localhost:3000
   - Select languages (e.g., English → Hindi)
   - Click "Start Translation"
   - Allow microphone access
   - Start speaking!

2. **Admin Panel**: http://localhost:3000/admin
   - Login: admin / changeme123
   - View metrics and logs

---

## 🐳 Docker Deployment (Alternative)

### Prerequisites
- Docker
- Docker Compose

### Steps

```bash
# Build and start services
docker-compose up --build

# Wait for models to download (5-10 minutes)
# Watch logs: docker-compose logs -f

# Access application
# Main: http://localhost:3000
# API: http://localhost:8000
# Admin: http://localhost:3000/admin
```

To stop:
```bash
docker-compose down
```

---

## ⚙️ Configuration

### Admin Credentials (Backend)

Edit `backend/.env`:
```env
ADMIN_USERNAME=admin
ADMIN_PASSWORD=your-secure-password
SECRET_KEY=generate-with-openssl-rand-hex-32
```

### Supported Languages

Default configuration includes:
- English ↔ Hindi
- English ↔ Spanish
- English ↔ French
- English ↔ German

To add more languages, see README.md section "Adding New Language Pairs"

### Performance Tuning

Edit `backend/app/config.py`:
```python
# Reduce chunk size for lower latency
AUDIO_CHUNK_DURATION_MS = 150  # Default: 200

# Increase for more concurrent users
MAX_CONCURRENT_SESSIONS = 50  # Default: 20
```

---

## 🔧 Troubleshooting

### Models Not Downloading

**Error**: `Model not found`

**Fix**:
```bash
# Manually run download script
cd scripts
chmod +x download_models.sh
./download_models.sh
```

### Microphone Not Working

**Error**: `Permission denied`

**Fix**:
- Ensure HTTPS in production (browsers require secure context)
- For local dev, use `http://localhost` (not IP address)
- Check browser permissions

### High Latency (>2 seconds)

**Causes**:
- Slow CPU
- Limited RAM
- Network issues

**Fixes**:
1. Use smaller models (edit `config.py`)
2. Increase allocated RAM
3. Upgrade server instance
4. Enable GPU (if available)

### WebSocket Disconnects

**Causes**:
- Server timeout
- Network instability
- Resource exhaustion

**Fixes**:
1. Check server logs for errors
2. Increase timeout settings
3. Upgrade server resources
4. Check firewall/proxy settings

---

## 📊 Testing

### Check Backend Health
```bash
curl http://localhost:8000/api/health
# Should return: {"status":"healthy","version":"1.0.0"}
```

### Check Available Languages
```bash
curl http://localhost:8000/api/languages
# Should return list of supported language pairs
```

### Test Admin Login
```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"changeme123"}'
# Should return JWT token
```

---

## 📚 Next Steps

1. **Read Full Documentation**: `README.md`
2. **Deployment Guide**: `DEPLOYMENT.md`
3. **Customize Languages**: See README section on adding languages
4. **Production Deployment**: Follow DEPLOYMENT.md for Render
5. **Monitor Performance**: Use admin panel metrics

---

## 🆘 Getting Help

- **Check Logs**: Look for error messages
- **Review Documentation**: README.md has detailed info
- **Common Issues**: See Troubleshooting section above
- **GitHub Issues**: Create issue with logs and description

---

**Happy Translating!** 🌍🗣️
