# 🚀 Starting the Full Oryza Application

This guide will help you start the complete Oryza platform with all components.

## 📋 Prerequisites Check

1. **Required Software:**
   - Node.js (v16+)
   - Python (3.11+)
   - Docker Desktop (for full microservices)
   - PostgreSQL (or use Docker)
   - Redis (or use Docker)

## 🏗️ Quick Start (Development Mode)

### Step 1: Start Infrastructure Services

**Option A: Using Docker (Recommended)**
```bash
# From project root
docker-compose up -d postgres redis mongodb
```

**Option B: Manual Start**
- Start PostgreSQL on port 5432
- Start Redis on port 6379
- Start MongoDB on port 27017

### Step 2: Start Backend Services

Open **Terminal 1** (Backend):
```bash
cd backend

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies if not done
pip install -r requirements.txt

# Start the API Gateway (main backend)
cd services/api-gateway
uvicorn src.main:app --host 0.0.0.0 --port 8080 --reload
```

### Step 3: Start Frontend

Open **Terminal 2** (Frontend):
```bash
cd frontend

# Install dependencies (if not done)
npm install

# Start React development server
npm start
```

### Step 4: Start Additional Services (Optional)

Open **Terminal 3** (Services):
```bash
cd backend/services

# Start specific services as needed:
# Advisory Engine
cd advisory-engine
uvicorn src.main:app --port 8000 --reload

# News Sentiment (in new terminal)
cd ../news-sentiment  
uvicorn src.main:app --port 8001 --reload

# Add more services as needed...
```

## 🐳 Full Production-Like Setup (Docker Compose)

### One Command Start:
```bash
# From project root
docker-compose up
```

This starts:
- ✅ All 21+ microservices
- ✅ PostgreSQL, Redis, MongoDB
- ✅ API Gateway
- ✅ Frontend
- ✅ Nginx reverse proxy

## 🌐 Access Points

Once everything is running:

### Main Application:
- **Frontend UI**: http://localhost:3000
- **API Gateway**: http://localhost:8080
- **API Docs**: http://localhost:8080/docs

### Individual Services (if running separately):
- **Advisory Engine**: http://localhost:8000
- **News Sentiment**: http://localhost:8001
- **Emotion Tracker**: http://localhost:8002
- **Screening Engine**: http://localhost:8003
- (and so on...)

## 🔧 Troubleshooting

### Frontend Issues:

**Error: 'react-scripts' is not recognized**
```bash
cd frontend
rm -rf node_modules package-lock.json
npm cache clean --force
npm install
npm start
```

**Error: Port 3000 already in use**
```bash
# Windows:
netstat -ano | findstr :3000
taskkill /F /PID <PID>

# Or use different port:
PORT=3001 npm start
```

### Backend Issues:

**Error: Cannot connect to PostgreSQL**
```bash
# Check if PostgreSQL is running
# Update DATABASE_URL in .env file
```

**Error: Module not found**
```bash
cd backend
pip install -r requirements.txt
```

## 📁 Environment Configuration

Create `.env` file in project root:
```env
# Database
DATABASE_URL=postgresql://oryza_user:oryza_pass@localhost:5432/oryza_db

# Redis
REDIS_URL=redis://localhost:6379

# MongoDB
MONGODB_URL=mongodb://localhost:27017/oryza

# API Keys (add your own)
ALPHA_VANTAGE_API_KEY=your_key
NEWS_API_KEY=your_key

# Frontend
REACT_APP_API_URL=http://localhost:8080/api/v1
```

## 🚦 Startup Order

1. **Infrastructure** (PostgreSQL, Redis, MongoDB)
2. **API Gateway** (Port 8080)
3. **Core Services** (Advisory, News, etc.)
4. **Frontend** (Port 3000)

## 💡 Quick Commands Summary

```bash
# Terminal 1: Infrastructure
docker-compose up -d postgres redis mongodb

# Terminal 2: Backend
cd backend/services/api-gateway
uvicorn src.main:app --port 8080 --reload

# Terminal 3: Frontend
cd frontend
npm install && npm start

# Terminal 4: Additional Services (optional)
cd backend/services/advisory-engine
uvicorn src.main:app --port 8000 --reload
```

## ✅ Verify Everything is Running

1. Frontend loads at http://localhost:3000
2. API Gateway responds at http://localhost:8080/health
3. Database connections are successful
4. No error messages in console

---

**Note**: For development with limited resources, you can use the test environment setup in `TESTING_GUIDE.md` which uses SQLite and mock data. 