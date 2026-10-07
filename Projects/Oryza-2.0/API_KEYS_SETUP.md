# API Keys Setup Guide for Oryza

This guide will help you set up all the necessary API keys to enable real-time data feeds in Oryza.

## Quick Start

1. Copy the environment template below to a `.env` file in your project root
2. Sign up for the required services and get API keys
3. Replace placeholder values with your actual API keys
4. Restart your services

## Required API Keys

### 1. Market Data (Essential)

#### Alpha Vantage (Free tier available)
- **Sign up**: https://www.alphavantage.co/support/#api-key
- **Free tier**: 5 API calls/minute, 500 calls/day
- **Used for**: Real-time stock prices, historical data
```
REACT_APP_ALPHA_VANTAGE_API_KEY=your_key_here
```

#### NewsAPI (Free tier available)
- **Sign up**: https://newsapi.org/register
- **Free tier**: 100 requests/day
- **Used for**: Financial news aggregation
```
REACT_APP_NEWS_API_KEY=your_key_here
```

#### Polygon.io (Better alternative to Alpha Vantage)
- **Sign up**: https://polygon.io/
- **Free tier**: 5 API calls/minute
- **Used for**: Real-time US market data
```
POLYGON_API_KEY=your_key_here
```

### 2. Broker Integration (Choose one to start)

#### Alpaca (Recommended for testing)
- **Sign up**: https://alpaca.markets/
- **Free**: Paper trading account
- **Used for**: US stock trading, real-time data
```
ALPACA_API_KEY=your_key_here
ALPACA_SECRET_KEY=your_secret_here
ALPACA_BASE_URL=https://paper-api.alpaca.markets
```

#### Interactive Brokers
- **Sign up**: https://www.interactivebrokers.com/
- **Requires**: IB Gateway or TWS
- **Used for**: Professional trading, global markets
```
IB_GATEWAY_HOST=localhost
IB_GATEWAY_PORT=7497
IB_CLIENT_ID=1
```

### 3. Indian Market Data

#### NSE/BSE Official APIs
- **Note**: Official APIs require partnership agreements
- **Alternative**: Use Alpha Vantage with .BSE suffix for symbols

### 4. Authentication & Security

Generate secure keys for JWT:
```bash
# Generate secure random keys
node -e "console.log(require('crypto').randomBytes(64).toString('hex'))"
```

```
JWT_SECRET_KEY=your_generated_key_here
JWT_REFRESH_SECRET_KEY=another_generated_key_here
```

## Complete .env Template

Create a `.env` file in your project root:

```env
# ==========================================
# ESSENTIAL - Start with these
# ==========================================

# Market Data
REACT_APP_ALPHA_VANTAGE_API_KEY=demo
REACT_APP_NEWS_API_KEY=your_newsapi_key_here
POLYGON_API_KEY=your_polygon_key_here

# Choose ONE broker to start
# Option 1: Alpaca (Recommended)
ALPACA_API_KEY=your_alpaca_key_here
ALPACA_SECRET_KEY=your_alpaca_secret_here
ALPACA_BASE_URL=https://paper-api.alpaca.markets

# Security (Generate these!)
JWT_SECRET_KEY=generate_64_char_random_string_here
JWT_REFRESH_SECRET_KEY=generate_another_64_char_random_string_here

# ==========================================
# DATABASE (Use Docker defaults or change)
# ==========================================

DATABASE_URL=postgresql://oryza_user:oryza_password@localhost:5432/oryza_db
MONGODB_URL=mongodb://oryza_user:oryza_password@localhost:27017/oryza_db
REDIS_URL=redis://localhost:6379/0

# ==========================================
# OPTIONAL - Add as needed
# ==========================================

# Enhanced Market Data
IEX_CLOUD_API_KEY=your_iex_key_here
CURRENCY_LAYER_API_KEY=your_currency_key_here

# ESG Data
MSCI_API_KEY=your_msci_key_here
SUSTAINALYTICS_API_KEY=your_sustainalytics_key_here

# Social Sentiment
TWITTER_BEARER_TOKEN=your_twitter_token_here
REDDIT_CLIENT_ID=your_reddit_id_here
REDDIT_CLIENT_SECRET=your_reddit_secret_here

# Banking Integration
PLAID_CLIENT_ID=your_plaid_id_here
PLAID_SECRET=your_plaid_secret_here
PLAID_ENV=sandbox

# AI Services
OPENAI_API_KEY=your_openai_key_here

# Notifications
SENDGRID_API_KEY=your_sendgrid_key_here
TWILIO_ACCOUNT_SID=your_twilio_sid_here
TWILIO_AUTH_TOKEN=your_twilio_token_here

# ==========================================
# SERVICE URLS (Don't change for local dev)
# ==========================================

API_GATEWAY_URL=http://localhost:8080
AUTH_SERVICE_URL=http://localhost:8001
WEBSOCKET_SERVICE_URL=http://localhost:8002
MARKET_SERVICE_URL=http://localhost:8005
NEWS_SERVICE_URL=http://localhost:8006

# Environment
NODE_ENV=development
DEBUG=true
```

## Free API Keys for Testing

To get started quickly, you can use these free services:

1. **Alpha Vantage**: 
   - Use API key: `demo` for limited testing
   - Or sign up for free at https://www.alphavantage.co/

2. **NewsAPI**:
   - Sign up required at https://newsapi.org/
   - Free tier: 100 requests/day

3. **Alpaca**:
   - Free paper trading at https://alpaca.markets/
   - Unlimited market data in paper trading mode

## Testing Your Setup

After adding API keys, test them:

```bash
# Test Alpha Vantage
curl "https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol=MSFT&apikey=YOUR_KEY"

# Test NewsAPI  
curl "https://newsapi.org/v2/everything?q=stocks&apiKey=YOUR_KEY"

# Test from frontend
cd frontend
npm start
# Check browser console for API responses
```

## Enabling Real-Time Data

1. **Frontend**: Update `frontend/.env` with REACT_APP_* keys
2. **Backend**: Create `.env` in root with all keys
3. **Services**: Each service folder can have its own `.env`

## Security Best Practices

1. **Never commit .env files** - Already in .gitignore
2. **Use different keys for dev/prod**
3. **Rotate keys regularly**
4. **Use environment-specific keys**
5. **Enable IP restrictions where possible**

## Next Steps

1. Start with essential APIs (Alpha Vantage + NewsAPI)
2. Add broker integration (Alpaca for testing)
3. Gradually add other services as needed
4. Monitor API usage to avoid limits

## Troubleshooting

- **API limit errors**: Check your plan limits
- **Connection errors**: Verify API keys and network
- **Data not updating**: Check WebSocket connections
- **Authentication fails**: Regenerate JWT secrets

Need help? Check service-specific documentation or create an issue. 