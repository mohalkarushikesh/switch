# Oryza Platform - Testing Guide

This guide provides step-by-step instructions for testing the Oryza financial platform in a resource-constrained environment using SQLite and mock data.

## 📋 Prerequisites

- Python 3.11 or higher
- Windows PowerShell or Command Prompt
- All Python dependencies installed (via `pip install -r requirements.txt`)

## 🚀 Quick Start

### Step 1: Navigate to Backend Directory

```powershell
cd C:\Users\2327238\Documents\devlopment\ai\projects\Oryza\backend
```

### Step 2: Set Up Test Environment

Run the setup script to create the test database and mock data:

```powershell
python setup_test_environment.py
```

This command will:
- ✅ Create a SQLite database (`test_oryza.db`)
- ✅ Generate mock stock price data
- ✅ Create sample news feed data
- ✅ Generate market overview data
- ✅ Create test user profiles
- ✅ Insert test users into the database

Expected output:
```
🚀 Setting up Oryza test environment...
==================================================
Setting up SQLite database...
✅ SQLite database created at: backend/test_oryza.db
✅ Mock stock prices saved
✅ Mock news feed saved
✅ Mock market data saved
✅ Mock user profiles saved
==================================================
✅ Test environment setup complete!
```

### Step 3: Verify Setup with Simple Test API

Run the simple test API to verify everything is working:

```powershell
python simple_test_api.py
```

The API will start on port 8888. You should see:
```
==================================================
🚀 Starting Oryza Test API
==================================================
📁 Mock data directory: backend\mock_data
🌐 API will be available at: http://localhost:8888
📊 Test endpoints:
   - GET /          - Status check
   - GET /stocks    - Mock stock data
   - GET /news      - Mock news data
   - GET /market    - Mock market data
   - GET /test-db   - Database connection test
==================================================
```

#### Test the Endpoints

Open your browser and test these URLs:

1. **Status Check**: http://localhost:8888/
   - Should return: `{"message": "Oryza Test API is running!", "status": "success", "mock_data_available": true}`

2. **Stock Data**: http://localhost:8888/stocks
   - Returns list of mock stocks with prices

3. **News Feed**: http://localhost:8888/news
   - Returns latest mock news articles

4. **Market Overview**: http://localhost:8888/market
   - Returns market indices and sector performance

5. **Database Test**: http://localhost:8888/test-db
   - Verifies SQLite connection and shows tables

Press `Ctrl+C` to stop the server.

### Step 4: List Available Services

Check all implemented services:

```powershell
python test_runner.py --list
```

This will display all 21 services:
- Advisory Engine (Port 8000)
- News Sentiment (Port 8001)
- Emotion Tracker (Port 8002)
- ... and 18 more services

### Step 5: Run Integration Test

Run a minimal integration test:

```powershell
python test_runner.py --test
```

Expected output:
```
🧪 Running minimal test setup...
✅ Database tables: ['users', 'portfolios', 'transactions', 'watchlists']
✅ Test users: 3
✅ Mock data found: stock_prices
✅ Mock data found: news_feed
✅ Mock data found: market_data
✅ Mock data found: user_profiles
✅ Basic test passed!
```

## 🚀 Starting the Main Application

### Option 1: Main Application with Web Dashboard (Recommended)

After verifying the test environment works, you can start the main application:

```powershell
python main_app_test.py
```

This launches:
- **Web Dashboard** on http://localhost:8080/ - Central interface for all services
- **Test API** on http://localhost:8888/ - Backend API with mock data

Expected output:
```
============================================================
🏗️  Oryza Platform - Test Environment
============================================================

📋 Available Services:
  - Simple Test API: http://localhost:8888
    Basic API with mock data
  - Web Dashboard: http://localhost:8080
    Main web interface

🚀 Starting services...

✅ Simple Test API started (PID: 12345)
✅ Web Dashboard started (PID: 12346)

============================================================
✅ All test services started!
============================================================

📌 Main Dashboard: http://localhost:8080/
📌 Service URLs:
  - Web Interface: http://localhost:8080/
  - Test API: http://localhost:8888/
  - API Docs: http://localhost:8888/docs

⚡ Press Ctrl+C to stop all services
============================================================
```

### Option 2: Individual Services

Alternatively, run services individually:

1. **Simple Test API only:**
   ```powershell
   python simple_test_api.py
   ```

2. **Web Interface only:**
   ```powershell
   python web_interface.py
   ```

## 🌐 Web Dashboard Features

Once the main application is running, open http://localhost:8080/ in your browser to access:

### Dashboard Overview
- **Platform Metrics**: Number of services, users, stocks, and database info
- **Service Status**: Real-time status of all available services
- **Quick Links**: Direct access to all service endpoints

### Available Services in Dashboard

1. **📊 Test API**
   - Status: Active
   - Endpoints: Main API and interactive documentation
   - Access: http://localhost:8888/

2. **💹 Stock Prices**
   - Mock prices for 8 major stocks (AAPL, MSFT, GOOGL, etc.)
   - Historical data with 30-day history
   - Access: http://localhost:8888/stocks

3. **📰 News Sentiment**
   - 5 sample financial news articles
   - Sentiment analysis (positive/negative/neutral)
   - Access: http://localhost:8888/news

4. **📈 Market Overview**
   - Market indices (S&P 500, NASDAQ, DOW, RUSSELL)
   - Sector performance data
   - Market status information
   - Access: http://localhost:8888/market

5. **🗄️ Database Status**
   - SQLite connection information
   - Table structure and user count
   - Access: http://localhost:8888/test-db

6. **🤖 Advisory Engine**
   - Status: Test Mode (simplified version)
   - Investment recommendations (coming soon in test mode)

## 🧪 Testing Individual Services

To test a specific service in isolation:

```powershell
python test_runner.py <service-name>
```

Example:
```powershell
python test_runner.py advisory-engine
```

**Note**: Services may require additional configuration for SQLite compatibility.

## 📁 Test Environment Structure

```
backend/
├── test_oryza.db           # SQLite database
├── test_config.py          # Test configuration
├── test_runner.py          # Service test runner
├── setup_test_environment.py # Setup script
├── simple_test_api.py      # Simple verification API
├── web_interface.py        # Web dashboard interface
├── main_app_test.py        # Main application launcher
└── mock_data/              # Mock data directory
    ├── stock_prices.json   # Stock price data
    ├── news_feed.json      # News articles
    ├── market_data.json    # Market indices
    └── user_profiles.json  # User profiles
```

## 🔧 Configuration Details

### Test Configuration (`test_config.py`)

- **Database**: SQLite instead of PostgreSQL
- **Cache**: In-memory cache instead of Redis
- **APIs**: All external APIs disabled
- **ML Models**: Simple algorithms instead of heavy models

### Environment Variables

The test runner automatically sets:
- `DATABASE_URL`: Points to SQLite database
- `USE_MOCK_DATA`: Enables mock data mode
- `USE_MEMORY_CACHE`: Uses in-memory cache
- `DISABLE_EXTERNAL_APIS`: Prevents external API calls

## 🚫 Restrictions and Workarounds

Per `restricted_tools_and_services.md`:

| Original | Test Mode Replacement |
|----------|----------------------|
| PostgreSQL | SQLite local database |
| MongoDB | SQLite collections |
| Redis | In-memory cache |
| External APIs | Local JSON mock data |
| ML Models | Simple scoring algorithms |
| Live Market Data | Static mock data files |

## 🐛 Troubleshooting

### Common Issues

1. **Module Import Errors**
   - Some services expect PostgreSQL/MongoDB modules
   - Use the simple test API for basic verification

2. **Port Already in Use**
   - Change the port in the command: `--port 8889`

3. **Mock Data Not Found**
   - Ensure you ran `setup_test_environment.py` first
   - Check that `mock_data/` directory exists

4. **Database Connection Failed**
   - Verify `test_oryza.db` exists in backend directory
   - Check file permissions

### PowerShell Specific Issues

If you encounter syntax errors with `&&`, use semicolon instead:
```powershell
cd backend; python script.py
```

## 📊 Test Data Overview

### Mock Users
- test@oryza.com (Test User)
- investor@oryza.com (Investor User)
- trader@oryza.com (Trader User)

### Mock Stocks
- AAPL (Apple Inc.)
- MSFT (Microsoft Corp.)
- GOOGL (Alphabet Inc.)
- TSLA (Tesla Inc.)
- And 4 more stocks

### Mock News
- 5 sample news articles with sentiment analysis
- Topics: Fed rates, Tech earnings, Oil prices, Crypto, Supply chain

## 🎯 Next Steps

After successful testing:

1. **Explore the Dashboard**: Navigate through all available services via the web interface
2. **Test API Endpoints**: Use the interactive API docs at http://localhost:8888/docs
3. **Monitor Services**: Check service status in real-time through the dashboard
4. **Extend Functionality**: Add more test-compatible services as needed

### For Production Deployment

The full Oryza platform includes:
- ✅ 21+ specialized microservices
- ✅ PostgreSQL for data persistence
- ✅ Redis for caching and real-time features
- ✅ MongoDB for logging
- ✅ External financial API integrations
- ✅ Advanced ML models for predictions
- ✅ WebSocket support for real-time updates
- ✅ Multi-agent AI optimization
- ✅ Comprehensive risk management

The test environment demonstrates the platform's capabilities while working within resource constraints.

## 📝 Notes

- This test setup is designed for resource-constrained environments
- Production deployment would use PostgreSQL, Redis, and real APIs
- All financial data is mock data for testing purposes only
- Services are configured to run on localhost only
- The web dashboard provides a unified interface for all test services

---

**Last Updated**: December 2024
**Version**: 1.0.0 