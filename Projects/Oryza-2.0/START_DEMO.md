# Oryza Investment Platform - Demo Setup Guide

## Quick Start (For Demo/Presentation)

### Option 1: Docker Compose (Recommended) 🐳

Start the entire system with one command:

```bash
docker-compose -f docker-compose.demo.yml up --build
```

Wait for all services to start (about 2-3 minutes), then access:
- **Frontend**: http://localhost:3000
- **API Docs**: http://localhost:8080/docs
- **Database UI**: http://localhost:8090 (username: oryza_user, password: oryza_secure_pass_2024)

### Option 2: Manual Start (If Docker fails)

#### 1. Start Databases (Docker)
```bash
cd backend
docker-compose -f docker-compose.db.yml up -d
```

#### 2. Start Backend Services (separate terminals)

**Terminal 1 - Auth Service:**
```bash
cd backend/services/auth-service
pip install -r requirements.txt
python -m src.main
```

**Terminal 2 - WebSocket Service:**
```bash
cd backend/services/websocket-service
pip install -r requirements.txt
python -m src.main
```

**Terminal 3 - Portfolio Service:**
```bash
cd backend/services/portfolio-service
pip install -r requirements.txt
python -m src.main
```

**Terminal 4 - Market Service:**
```bash
cd backend/services/market-service
pip install -r requirements.txt
python -m src.main
```

**Terminal 5 - Trading Service:**
```bash
cd backend/services/trading-service
pip install -r requirements.txt
python -m src.main
```

**Terminal 6 - API Gateway:**
```bash
cd backend/services/api-gateway
pip install -r requirements.txt
python -m src.main_gateway
```

#### 3. Start Frontend
```bash
cd frontend
npm install
npm start
```

## Demo Credentials

- **Email**: test@example.com  **Password**: test123
- **Email**: test@oryza.com    **Password**: test@123

## Features to Showcase

### 1. Authentication & Security
- User registration with email verification
- JWT-based authentication
- Two-factor authentication support
- Session management

### 2. Portfolio Management
- Real-time portfolio valuation
- Holdings breakdown with P&L
- Asset allocation visualization
- Transaction history

### 3. Trading Interface
- Live order book
- Market/Limit orders
- Order history with export
- Real-time price updates

### 4. Market Data
- Live price streaming (simulated)
- Market indices (NIFTY, SENSEX)
- Top gainers/losers
- Interactive charts

### 5. Financial Goals
- Goal tracking with progress
- Milestone management
- Visual progress indicators

### 6. Analytics Dashboard
- Performance metrics
- Risk analysis
- Sector allocation
- Export reports

### 7. Real-time Features
- WebSocket for live updates
- Price alerts
- Push notifications
- Market news feed

## Architecture Highlights

### Microservices Architecture
- **API Gateway**: Central entry point with authentication
- **Auth Service**: JWT tokens, 2FA, session management
- **Portfolio Service**: Holdings and performance tracking
- **Market Service**: Real-time price feeds
- **Trading Service**: Order execution
- **WebSocket Service**: Real-time bidirectional communication

### Technology Stack
- **Frontend**: React, TypeScript, Redux, Tailwind CSS
- **Backend**: FastAPI, Python 3.11, Async
- **Databases**: PostgreSQL, Redis, MongoDB, TimescaleDB
- **Real-time**: WebSockets with Redis pub/sub
- **Containerization**: Docker & Docker Compose

### Security Features
- JWT authentication with refresh tokens
- Password hashing with bcrypt
- Rate limiting on API endpoints
- CORS configuration
- Input validation with Pydantic

## Demo Flow

1. **Registration/Login**
   - Show registration process
   - Login with demo credentials
   - Highlight JWT tokens in browser DevTools

2. **Dashboard Overview**
   - Portfolio summary with live updates
   - Market indices updating in real-time
   - Top movers section

3. **Trading**
   - Place a buy order
   - Show order execution
   - View order history
   - Export trading data

4. **Portfolio Analytics**
   - Holdings breakdown
   - Performance charts
   - Asset allocation
   - Risk metrics

5. **Real-time Updates**
   - Open multiple browser tabs
   - Show price updates across tabs
   - Demonstrate WebSocket connection

6. **Responsive Design**
   - Show mobile responsiveness
   - Dark mode toggle (if implemented)

## Troubleshooting

### Port Conflicts
If ports are already in use:
- Frontend (3000): `kill -9 $(lsof -ti:3000)`
- API Gateway (8080): `kill -9 $(lsof -ti:8080)`
- Other services: Check ports 8001-8005

### Database Connection Issues
- Ensure Docker is running
- Check database logs: `docker logs oryza-postgres`
- Verify connection strings in services

### Frontend Not Loading
- Clear browser cache
- Check console for errors
- Ensure API Gateway is running

## Performance Notes

- The system uses mock data for demo purposes
- Prices update every 5 seconds
- WebSocket connections support 10,000+ concurrent users
- Horizontal scaling supported via Redis pub/sub

## Next Steps (Post-Demo)

1. Integrate real market data APIs
2. Implement real broker connections
3. Add machine learning models
4. Deploy to cloud (AWS/GCP)
5. Mobile app development
6. Advanced features (options trading, crypto) 