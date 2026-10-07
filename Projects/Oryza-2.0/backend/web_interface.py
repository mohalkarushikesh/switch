"""
Oryza Web Interface - Main Dashboard
Simple web interface for the test environment
"""
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import json
from pathlib import Path

app = FastAPI(title="Oryza Platform", version="1.0.0-test")

# Templates would normally be in a templates directory
# For simplicity, we'll return HTML directly

@app.get("/", response_class=HTMLResponse)
async def dashboard():
    """Main dashboard"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Oryza Financial Platform</title>
        <style>
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                margin: 0;
                padding: 0;
                background: #f5f5f7;
            }
            .header {
                background: #1d1d1f;
                color: white;
                padding: 20px;
                text-align: center;
            }
            .container {
                max-width: 1200px;
                margin: 0 auto;
                padding: 20px;
            }
            .services-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                gap: 20px;
                margin-top: 20px;
            }
            .service-card {
                background: white;
                border-radius: 10px;
                padding: 20px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                transition: transform 0.2s;
            }
            .service-card:hover {
                transform: translateY(-5px);
                box-shadow: 0 5px 20px rgba(0,0,0,0.15);
            }
            .service-card h3 {
                margin-top: 0;
                color: #1d1d1f;
            }
            .service-card p {
                color: #666;
                margin: 10px 0;
            }
            .service-link {
                display: inline-block;
                margin-top: 10px;
                padding: 8px 16px;
                background: #007aff;
                color: white;
                text-decoration: none;
                border-radius: 5px;
                font-size: 14px;
            }
            .service-link:hover {
                background: #0051d5;
            }
            .status {
                display: inline-block;
                padding: 4px 8px;
                border-radius: 4px;
                font-size: 12px;
                font-weight: bold;
            }
            .status.active {
                background: #34c759;
                color: white;
            }
            .status.test {
                background: #ff9500;
                color: white;
            }
            .metrics {
                display: grid;
                grid-template-columns: repeat(4, 1fr);
                gap: 20px;
                margin: 20px 0;
            }
            .metric-card {
                background: white;
                padding: 20px;
                border-radius: 10px;
                text-align: center;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }
            .metric-value {
                font-size: 32px;
                font-weight: bold;
                color: #007aff;
            }
            .metric-label {
                color: #666;
                margin-top: 5px;
            }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🏦 Oryza Financial Platform</h1>
            <p>AI-Powered Wealth Management & Trading Platform (Test Environment)</p>
        </div>
        
        <div class="container">
            <div class="metrics">
                <div class="metric-card">
                    <div class="metric-value">21+</div>
                    <div class="metric-label">Services</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">3</div>
                    <div class="metric-label">Test Users</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">8</div>
                    <div class="metric-label">Mock Stocks</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">SQLite</div>
                    <div class="metric-label">Database</div>
                </div>
            </div>
            
            <h2>Available Services</h2>
            
            <div class="services-grid">
                <div class="service-card">
                    <h3>📊 Test API</h3>
                    <span class="status active">Active</span>
                    <p>Core API with mock stock data, news feed, and market overview</p>
                    <a href="http://localhost:8889/" class="service-link" target="_blank">Open API</a>
                    <a href="http://localhost:8889/docs" class="service-link" target="_blank">API Docs</a>
                </div>
                
                <div class="service-card">
                    <h3>💹 Stock Prices</h3>
                    <span class="status active">Active</span>
                    <p>Real-time mock stock prices for AAPL, MSFT, GOOGL, and more</p>
                    <a href="http://localhost:8889/stocks" class="service-link" target="_blank">View Stocks</a>
                </div>
                
                <div class="service-card">
                    <h3>📰 News Sentiment</h3>
                    <span class="status active">Active</span>
                    <p>Financial news with sentiment analysis</p>
                    <a href="http://localhost:8889/news" class="service-link" target="_blank">View News</a>
                </div>
                
                <div class="service-card">
                    <h3>📈 Market Overview</h3>
                    <span class="status active">Active</span>
                    <p>Market indices and sector performance</p>
                    <a href="http://localhost:8889/market" class="service-link" target="_blank">View Market</a>
                </div>
                
                <div class="service-card">
                    <h3>🗄️ Database Status</h3>
                    <span class="status active">Active</span>
                    <p>SQLite database with test users and portfolios</p>
                    <a href="http://localhost:8889/test-db" class="service-link" target="_blank">Check DB</a>
                </div>
                
                <div class="service-card">
                    <h3>🤖 Advisory Engine</h3>
                    <span class="status test">Test Mode</span>
                    <p>Investment recommendations and portfolio analysis</p>
                    <a href="#" class="service-link">Coming Soon</a>
                </div>
            </div>
            
            <div style="margin-top: 40px; padding: 20px; background: #fff3cd; border-radius: 10px;">
                <h3>⚠️ Test Environment Notice</h3>
                <p>This is running in test mode with:</p>
                <ul>
                    <li>SQLite database instead of PostgreSQL</li>
                    <li>Mock data instead of live market feeds</li>
                    <li>In-memory cache instead of Redis</li>
                    <li>Simplified ML models</li>
                </ul>
                <p>For production deployment, the full service architecture with all 21+ microservices would be available.</p>
            </div>
        </div>
        
        <script>
            // Auto-refresh metrics every 5 seconds
            setInterval(() => {
                // In a real app, this would fetch live data
                console.log('Checking service status...');
            }, 5000);
        </script>
    </body>
    </html>
    """

@app.get("/api/status")
async def get_status():
    """Get platform status"""
    return {
        "platform": "Oryza Financial",
        "environment": "test",
        "services": {
            "test_api": {"status": "active", "port": 8889},
            "web_interface": {"status": "active", "port": 8080}
        },
        "database": "SQLite",
        "mock_data": True
    }

if __name__ == "__main__":
    import uvicorn
    print("\nStarting Oryza Web Interface...")
    print("Dashboard will be available at: http://localhost:8080")
    print("="*50 + "\n")
    uvicorn.run(app, host="0.0.0.0", port=8080) 