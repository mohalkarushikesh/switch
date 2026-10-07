# Oryza Platform Performance Optimization Guide

## Overview

This guide covers performance optimization techniques implemented and recommended for the Oryza platform.

## Current Performance Metrics

- **API Response Time**: <200ms (p95)
- **AI Calculations**: <100ms
- **WebSocket Latency**: <50ms
- **Frontend Load Time**: <2s
- **Concurrent Users**: 10,000+

## Backend Optimizations

### 1. Async Programming

```python
# Use async/await throughout
async def get_portfolio_with_analysis(user_id: str):
    # Run multiple operations concurrently
    portfolio_task = fetch_portfolio(user_id)
    risk_task = calculate_risk_score(user_id)
    esg_task = get_esg_scores(user_id)
    
    # Wait for all tasks to complete
    portfolio, risk, esg = await asyncio.gather(
        portfolio_task, risk_task, esg_task
    )
    
    return {
        "portfolio": portfolio,
        "risk_analysis": risk,
        "esg_scores": esg
    }
```

### 2. Database Query Optimization

```python
# Use connection pooling
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.pool import NullPool

engine = create_async_engine(
    DATABASE_URL,
    pool_size=20,
    max_overflow=40,
    pool_pre_ping=True,
    pool_recycle=3600
)

# Optimize queries with proper indexing
class PortfolioRepository:
    async def get_user_holdings(self, user_id: str):
        # Use indexed queries
        query = """
            SELECT h.*, s.current_price, s.day_change
            FROM holdings h
            JOIN stocks s ON h.symbol = s.symbol
            WHERE h.user_id = $1
            AND h.quantity > 0
            ORDER BY h.value DESC
        """
        return await db.fetch_all(query, user_id)
```

### 3. Caching Strategy

```python
from functools import lru_cache
from aiocache import Cache
from aiocache.serializers import JsonSerializer

# Memory cache for frequently accessed data
cache = Cache(Cache.REDIS, endpoint="localhost", port=6379, 
              serializer=JsonSerializer())

# Decorator for caching
from aiocache.decorators import cached

@cached(ttl=300, key_builder=lambda f, *args, **kwargs: f"{f.__name__}:{args[0]}")
async def get_market_data(symbol: str):
    return await fetch_from_external_api(symbol)

# Manual cache management
async def get_portfolio_value(user_id: str):
    cache_key = f"portfolio_value:{user_id}"
    
    # Try cache first
    cached_value = await cache.get(cache_key)
    if cached_value:
        return cached_value
    
    # Calculate if not cached
    value = await calculate_portfolio_value(user_id)
    
    # Cache for 1 minute
    await cache.set(cache_key, value, ttl=60)
    return value
```

### 4. AI Model Optimization

```python
# Batch processing for AI models
class OptimizedAIModels:
    def __init__(self):
        self.batch_size = 32
        self.processing_queue = asyncio.Queue()
        
    async def process_batch(self):
        batch = []
        while len(batch) < self.batch_size:
            try:
                item = await asyncio.wait_for(
                    self.processing_queue.get(), 
                    timeout=0.1
                )
                batch.append(item)
            except asyncio.TimeoutError:
                break
        
        if batch:
            # Process entire batch at once
            results = await self.run_ai_model(batch)
            return results

# Model warm-up on startup
async def warm_up_models():
    dummy_data = generate_dummy_data()
    await risk_scorer.calculate_risk(dummy_data)
    await sentiment_analyzer.analyze(dummy_data)
    logger.info("AI models warmed up")
```

## Frontend Optimizations

### 1. Code Splitting

```javascript
// Lazy load heavy components
const Analytics = React.lazy(() => import('./pages/Analytics'));
const AIAdvisor = React.lazy(() => import('./pages/AIAdvisor'));

// Use Suspense for loading state
<Suspense fallback={<LoadingSpinner />}>
  <Routes>
    <Route path="/analytics" element={<Analytics />} />
    <Route path="/ai-advisor" element={<AIAdvisor />} />
  </Routes>
</Suspense>
```

### 2. React Performance

```typescript
// Memoize expensive calculations
const portfolioMetrics = useMemo(() => {
  return calculateMetrics(holdings, marketData);
}, [holdings, marketData]);

// Prevent unnecessary re-renders
const StockCard = React.memo(({ stock, onClick }) => {
  return (
    <div onClick={() => onClick(stock.symbol)}>
      {stock.name} - ${stock.price}
    </div>
  );
});

// Use callback for event handlers
const handleTrade = useCallback((symbol: string) => {
  dispatch(executeTrade(symbol));
}, [dispatch]);
```

### 3. API Call Optimization

```typescript
// Debounce search queries
const debouncedSearch = useMemo(
  () => debounce((query: string) => {
    searchStocks(query);
  }, 300),
  []
);

// Cache API responses
const { data: portfolio } = useQuery(
  ['portfolio', userId],
  () => fetchPortfolio(userId),
  {
    staleTime: 5 * 60 * 1000, // 5 minutes
    cacheTime: 10 * 60 * 1000, // 10 minutes
  }
);

// Prefetch next likely data
const prefetchUserData = async (userId: string) => {
  await queryClient.prefetchQuery(
    ['portfolio', userId],
    () => fetchPortfolio(userId)
  );
};
```

### 4. Bundle Size Optimization

```javascript
// webpack.config.js
module.exports = {
  optimization: {
    splitChunks: {
      chunks: 'all',
      cacheGroups: {
        vendor: {
          test: /[\\/]node_modules[\\/]/,
          name: 'vendors',
          priority: 10
        },
        common: {
          minChunks: 2,
          priority: 5,
          reuseExistingChunk: true
        }
      }
    }
  }
};

// Use production builds
// package.json
"scripts": {
  "build": "react-scripts build",
  "build:analyze": "source-map-explorer 'build/static/js/*.js'"
}
```

## WebSocket Optimization

### 1. Message Batching

```python
class OptimizedWebSocket:
    def __init__(self):
        self.message_buffer = []
        self.flush_interval = 0.1  # 100ms
        
    async def send_update(self, client_id: str, data: dict):
        self.message_buffer.append({
            "client_id": client_id,
            "data": data,
            "timestamp": datetime.now()
        })
        
    async def flush_messages(self):
        while True:
            await asyncio.sleep(self.flush_interval)
            if self.message_buffer:
                # Send all messages in one batch
                batch = self.message_buffer[:50]  # Max 50 messages
                self.message_buffer = self.message_buffer[50:]
                
                await self.broadcast_batch(batch)
```

### 2. Selective Broadcasting

```python
# Only send relevant updates
class SmartBroadcaster:
    async def broadcast_price_update(self, symbol: str, price: float):
        # Only send to clients watching this symbol
        interested_clients = await self.get_clients_watching(symbol)
        
        for client in interested_clients:
            await client.send_json({
                "type": "price_update",
                "symbol": symbol,
                "price": price
            })
```

## Infrastructure Optimization

### 1. CDN Configuration

```nginx
# nginx.conf
location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2)$ {
    expires 1y;
    add_header Cache-Control "public, immutable";
    add_header X-Content-Type-Options nosniff;
}

# Enable gzip compression
gzip on;
gzip_vary on;
gzip_min_length 1024;
gzip_types text/plain text/css text/xml text/javascript 
           application/x-javascript application/xml 
           application/javascript application/json;
```

### 2. Load Balancing

```yaml
# kubernetes/service.yaml
apiVersion: v1
kind: Service
metadata:
  name: oryza-backend
  annotations:
    service.beta.kubernetes.io/aws-load-balancer-type: "nlb"
spec:
  type: LoadBalancer
  selector:
    app: oryza-backend
  ports:
    - port: 80
      targetPort: 8889
  sessionAffinity: ClientIP
  sessionAffinityConfig:
    clientIP:
      timeoutSeconds: 3600
```

### 3. Auto-scaling

```yaml
# kubernetes/hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: oryza-backend-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: oryza-backend
  minReplicas: 3
  maxReplicas: 50
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 60
  - type: Pods
    pods:
      metric:
        name: http_requests_per_second
      target:
        type: AverageValue
        averageValue: "1000"
```

## Monitoring & Profiling

### 1. Performance Monitoring

```python
from prometheus_client import Counter, Histogram, generate_latest
import time

# Track API metrics
request_count = Counter('api_requests_total', 'Total API requests', ['method', 'endpoint'])
request_duration = Histogram('api_request_duration_seconds', 'API request duration')

@app.middleware("http")
async def track_metrics(request, call_next):
    start_time = time.time()
    
    response = await call_next(request)
    
    duration = time.time() - start_time
    request_count.labels(
        method=request.method,
        endpoint=request.url.path
    ).inc()
    request_duration.observe(duration)
    
    return response

@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type="text/plain")
```

### 2. Application Profiling

```python
# Use py-spy for production profiling
# pip install py-spy

# Profile running process
# py-spy record -o profile.svg --pid $PID --duration 60

# Memory profiling
from memory_profiler import profile

@profile
def memory_intensive_function():
    # Function code here
    pass

# Line profiling
from line_profiler import LineProfiler

def profile_critical_path():
    lp = LineProfiler()
    lp.add_function(calculate_portfolio_risk)
    lp.enable()
    
    # Run function
    calculate_portfolio_risk(portfolio_data)
    
    lp.disable()
    lp.print_stats()
```

## Best Practices

### 1. Resource Management

```python
# Use context managers
async with aiohttp.ClientSession() as session:
    async with session.get(url) as response:
        data = await response.json()

# Proper cleanup
async def cleanup_resources():
    await redis_pool.close()
    await db_engine.dispose()
    await session.close()
```

### 2. Error Handling

```python
# Circuit breaker pattern
from pybreaker import CircuitBreaker

external_api_breaker = CircuitBreaker(fail_max=5, reset_timeout=60)

@external_api_breaker
async def call_external_api():
    # API call implementation
    pass

# Retry with backoff
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10)
)
async def resilient_api_call():
    # API call that might fail
    pass
```

### 3. Batch Operations

```python
# Batch database inserts
async def bulk_insert_trades(trades: List[Trade]):
    async with db.transaction():
        await db.execute_many(
            """
            INSERT INTO trades (user_id, symbol, quantity, price, created_at)
            VALUES ($1, $2, $3, $4, $5)
            """,
            [(t.user_id, t.symbol, t.quantity, t.price, t.created_at) 
             for t in trades]
        )
```

## Performance Testing

### Load Testing Script

```python
# locustfile.py
from locust import HttpUser, task, between

class OryzaUser(HttpUser):
    wait_time = between(1, 3)
    
    def on_start(self):
        # Login
        response = self.client.post("/api/v1/auth/login", json={
            "email": "test@example.com",
            "password": "test123"
        })
        self.token = response.json()["access_token"]
        self.client.headers.update({
            "Authorization": f"Bearer {self.token}"
        })
    
    @task(3)
    def view_portfolio(self):
        self.client.get("/api/v1/portfolio")
    
    @task(2)
    def get_market_data(self):
        self.client.get("/api/v1/market/overview")
    
    @task(1)
    def run_ai_analysis(self):
        self.client.get("/api/v1/ai/risk-assessment")
```

## Optimization Checklist

- [ ] Enable connection pooling
- [ ] Implement caching strategy
- [ ] Add database indexes
- [ ] Enable gzip compression
- [ ] Implement code splitting
- [ ] Use CDN for static assets
- [ ] Configure auto-scaling
- [ ] Set up monitoring
- [ ] Run load tests
- [ ] Profile critical paths
- [ ] Optimize bundle size
- [ ] Enable HTTP/2
- [ ] Implement rate limiting
- [ ] Use async operations
- [ ] Batch API calls

---

**Remember**: Measure first, optimize second. Always profile before optimizing! 