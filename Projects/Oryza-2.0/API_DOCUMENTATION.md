# Oryza API Documentation

## Base URL
```
Development: http://localhost:8889/api/v1
Production: https://api.oryza.ai/v1
```

## Authentication
All protected endpoints require a Bearer token in the Authorization header:
```
Authorization: Bearer <access_token>
```

## API Endpoints

### Authentication

#### POST /auth/login
Login with email and password.

**Request:**
```json
{
  "email": "test@example.com",
  "password": "test123"
}
```

**Response:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "email": "test@example.com",
    "firstName": "Test",
    "lastName": "User"
  }
}
```

#### POST /auth/register
Create a new user account.

**Request:**
```json
{
  "email": "user@example.com",
  "password": "securepassword",
  "firstName": "John",
  "lastName": "Doe"
}
```

#### POST /auth/refresh
Refresh access token.

**Headers:** `Authorization: Bearer <access_token>`

#### GET /auth/me
Get current user details.

**Headers:** `Authorization: Bearer <access_token>`

### Portfolio Management

#### GET /portfolio
Get user's portfolio details.

**Headers:** `Authorization: Bearer <access_token>`

**Response:**
```json
{
  "totalValue": 1250000,
  "totalGain": 125000,
  "totalGainPercent": 11.11,
  "holdings": [
    {
      "symbol": "RELIANCE",
      "name": "Reliance Industries",
      "quantity": 50,
      "avgPrice": 2350.00,
      "currentPrice": 2456.50,
      "value": 122825,
      "gain": 5325,
      "gainPercent": 4.53
    }
  ]
}
```

### AI-Powered Endpoints

#### GET /ai/risk-assessment
Get AI-powered portfolio risk assessment.

**Headers:** `Authorization: Bearer <access_token>`

**Response:**
```json
{
  "overall_risk_score": 42.5,
  "risk_level": "moderate",
  "risk_breakdown": {
    "concentration": 35.2,
    "volatility": 48.3,
    "correlation": 32.1,
    "liquidity": 28.7,
    "market_conditions": 45.0
  },
  "recommendations": [
    "Portfolio is moderately concentrated. Consider diversifying across more assets."
  ]
}
```

#### GET /ai/esg-score/{symbol}
Get ESG score for a specific company.

**Parameters:**
- `symbol` (string): Stock symbol

**Response:**
```json
{
  "company": "RELIANCE",
  "overall_score": 73.8,
  "rating": "AA",
  "breakdown": {
    "environmental": 75.2,
    "social": 71.5,
    "governance": 74.6
  },
  "strengths": ["Strong environmental practices"],
  "weaknesses": ["Room for improvement in sustainability"]
}
```

#### GET /ai/portfolio-esg
Get ESG analysis for entire portfolio.

**Headers:** `Authorization: Bearer <access_token>`

#### POST /ai/sentiment-analysis
Analyze sentiment from news articles.

**Request:**
```json
{
  "articles": [
    {
      "title": "Company announces record profits",
      "content": "...",
      "source": "Economic Times"
    }
  ]
}
```

**Response:**
```json
{
  "overall_sentiment": 0.45,
  "sentiment_label": "positive",
  "confidence": 0.78,
  "market_impact": "medium",
  "impact_score": 0.62
}
```

#### GET /ai/market-mood
Get current market sentiment analysis.

**Response:**
```json
{
  "market_mood": "bullish",
  "mood_score": 0.65,
  "confidence": 0.82,
  "contributing_factors": [
    "Positive earnings reports",
    "Economic growth indicators"
  ]
}
```

#### POST /ai/portfolio-optimization
Get AI-powered portfolio optimization recommendations.

**Headers:** `Authorization: Bearer <access_token>`

**Request:**
```json
{
  "risk_tolerance": "moderate",
  "investment_goals": ["growth", "income"]
}
```

**Response:**
```json
{
  "target_allocation": {
    "stocks": 0.50,
    "bonds": 0.30,
    "commodities": 0.10,
    "alternatives": 0.05,
    "cash": 0.05
  },
  "expected_return": 0.085,
  "sharpe_ratio": 1.2,
  "rebalancing_needed": true
}
```

#### POST /ai/create-goal
Create a financial goal with AI analysis.

**Headers:** `Authorization: Bearer <access_token>`

**Request:**
```json
{
  "goal_type": "retirement",
  "target_amount": 10000000,
  "target_date": "2045-12-31",
  "current_savings": 100000,
  "monthly_contribution": 25000
}
```

#### POST /ai/backtest
Run backtesting for a trading strategy.

**Headers:** `Authorization: Bearer <access_token>`

**Request:**
```json
{
  "strategy": "ma_crossover",
  "symbol": "RELIANCE",
  "start_date": "2023-01-01",
  "end_date": "2024-01-01",
  "initial_capital": 1000000
}
```

**Response:**
```json
{
  "total_return": 23.5,
  "annualized_return": 23.5,
  "sharpe_ratio": 1.35,
  "max_drawdown": -12.3,
  "win_rate": 57.7,
  "total_trades": 142
}
```

#### GET /ai/agent-recommendations
Get multi-agent AI recommendations.

**Headers:** `Authorization: Bearer <access_token>`

**Response:**
```json
{
  "consensus_allocation": {
    "equity": {"allocation": 60, "confidence": 0.85},
    "bonds": {"allocation": 25, "confidence": 0.78}
  },
  "agent_insights": {
    "equity_agent": {
      "recommendation": "overweight",
      "key_sectors": ["technology", "healthcare"]
    }
  }
}
```

### Market Data

#### GET /market/overview
Get market overview with indices and top movers.

**Response:**
```json
{
  "indices": {
    "NIFTY50": {
      "value": 19845.50,
      "change": 125.30,
      "changePercent": 0.63
    }
  },
  "topGainers": [...],
  "topLosers": [...]
}
```

#### GET /market/quote/{symbol}
Get real-time quote for a stock.

**Parameters:**
- `symbol` (string): Stock symbol

### Trading

#### POST /orders
Place a new order.

**Headers:** `Authorization: Bearer <access_token>`

**Request:**
```json
{
  "symbol": "RELIANCE",
  "type": "buy",
  "orderType": "market",
  "quantity": 10,
  "price": 2450.00
}
```

#### GET /orders
Get user's order history.

**Headers:** `Authorization: Bearer <access_token>`

### Goals

#### GET /goals
Get user's financial goals.

**Headers:** `Authorization: Bearer <access_token>`

### Analytics

#### GET /analytics/performance
Get portfolio performance metrics.

**Headers:** `Authorization: Bearer <access_token>`

#### GET /analytics/allocation
Get portfolio allocation analysis.

**Headers:** `Authorization: Bearer <access_token>`

### User Profile

#### GET /profile
Get user profile details.

**Headers:** `Authorization: Bearer <access_token>`

### WebSocket

#### WS /ws
Real-time market updates via WebSocket.

**Connection:**
```javascript
const ws = new WebSocket('ws://localhost:8889/ws');
```

**Message Format:**
```json
{
  "type": "market_update",
  "timestamp": "2024-01-20T10:30:00Z",
  "data": {
    "stocks": [...],
    "indices": [...]
  }
}
```

## Error Responses

All errors follow this format:
```json
{
  "detail": "Error message",
  "status_code": 400
}
```

### Common Error Codes
- `400` - Bad Request
- `401` - Unauthorized
- `403` - Forbidden
- `404` - Not Found
- `422` - Validation Error
- `429` - Too Many Requests
- `500` - Internal Server Error

## Rate Limiting

- Default: 60 requests per minute per IP
- Authenticated users: 120 requests per minute
- AI endpoints: 30 requests per minute

## Best Practices

1. **Always use HTTPS in production**
2. **Store tokens securely** (never in localStorage)
3. **Implement proper error handling**
4. **Use pagination for large datasets**
5. **Cache responses when appropriate**
6. **Handle WebSocket reconnection**

## SDK Examples

### JavaScript/TypeScript
```typescript
import axios from 'axios';

const api = axios.create({
  baseURL: 'http://localhost:8889/api/v1',
  headers: {
    'Content-Type': 'application/json'
  }
});

// Add auth token
api.interceptors.request.use(config => {
  const token = getAuthToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Example: Get portfolio
const getPortfolio = async () => {
  const response = await api.get('/portfolio');
  return response.data;
};
```

### Python
```python
import requests

class OryzeAPI:
    def __init__(self, base_url="http://localhost:8889/api/v1"):
        self.base_url = base_url
        self.session = requests.Session()
    
    def login(self, email, password):
        response = self.session.post(
            f"{self.base_url}/auth/login",
            json={"email": email, "password": password}
        )
        data = response.json()
        self.session.headers.update({
            "Authorization": f"Bearer {data['access_token']}"
        })
        return data
    
    def get_portfolio(self):
        response = self.session.get(f"{self.base_url}/portfolio")
        return response.json()
```

## Changelog

### Version 1.0.0 (Current)
- Initial API release
- 60+ endpoints
- 8 AI models integrated
- Real-time WebSocket support
- Complete authentication system 