"""
Setup test environment for Oryza
Creates SQLite database and generates mock data
"""
import json
import sqlite3
from pathlib import Path
from datetime import datetime, timedelta
import random
from decimal import Decimal

# Import test configuration
from test_config import DATABASE_URL, MOCK_DATA_DIR, MOCK_DATA_SOURCES

def setup_sqlite_database():
    """Create SQLite database with necessary tables"""
    print("Setting up SQLite database...")
    
    # Extract database path from URL
    db_path = DATABASE_URL.replace("sqlite:///", "")
    
    # Create connection
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            username TEXT UNIQUE NOT NULL,
            full_name TEXT,
            is_active BOOLEAN DEFAULT 1,
            is_verified BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Create portfolios table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS portfolios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            total_value DECIMAL(15,2),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)
    
    # Create transactions table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            portfolio_id INTEGER,
            type TEXT NOT NULL,
            symbol TEXT,
            quantity DECIMAL(15,8),
            price DECIMAL(15,2),
            total_amount DECIMAL(15,2),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (portfolio_id) REFERENCES portfolios(id)
        )
    """)
    
    # Create watchlists table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS watchlists (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            symbols TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)
    
    # Insert test users
    test_users = [
        ("test@oryza.com", "testuser", "Test User"),
        ("investor@oryza.com", "investor", "Investor User"),
        ("trader@oryza.com", "trader", "Trader User")
    ]
    
    cursor.executemany(
        "INSERT OR IGNORE INTO users (email, username, full_name, is_active, is_verified) VALUES (?, ?, ?, 1, 1)",
        test_users
    )
    
    conn.commit()
    conn.close()
    
    print(f"✅ SQLite database created at: {db_path}")

def generate_mock_stock_prices():
    """Generate mock stock price data"""
    print("Generating mock stock prices...")
    
    stocks = {
        "AAPL": {"name": "Apple Inc.", "price": 175.43, "change": 2.15},
        "MSFT": {"name": "Microsoft Corp.", "price": 378.92, "change": -1.23},
        "GOOGL": {"name": "Alphabet Inc.", "price": 141.80, "change": 0.87},
        "TSLA": {"name": "Tesla Inc.", "price": 242.64, "change": 5.32},
        "AMZN": {"name": "Amazon.com Inc.", "price": 146.57, "change": -0.45},
        "NVDA": {"name": "NVIDIA Corp.", "price": 495.22, "change": 3.78},
        "META": {"name": "Meta Platforms", "price": 338.10, "change": 1.92},
        "BRK.B": {"name": "Berkshire Hathaway", "price": 367.45, "change": 0.23}
    }
    
    # Generate historical data
    for symbol, info in stocks.items():
        history = []
        current_price = info["price"]
        
        for i in range(30):  # 30 days of history
            date = (datetime.now() - timedelta(days=30-i)).isoformat()
            # Random walk
            change = random.uniform(-5, 5)
            price = current_price * (1 + change/100)
            
            history.append({
                "date": date,
                "open": price - random.uniform(0, 2),
                "high": price + random.uniform(0, 3),
                "low": price - random.uniform(0, 3),
                "close": price,
                "volume": random.randint(1000000, 50000000)
            })
            
            current_price = price
            
        stocks[symbol]["history"] = history
    
    # Save to file
    with open(MOCK_DATA_SOURCES["stock_prices"], "w") as f:
        json.dump(stocks, f, indent=2)
    
    print(f"✅ Mock stock prices saved to: {MOCK_DATA_SOURCES['stock_prices']}")

def generate_mock_news():
    """Generate mock news data"""
    print("Generating mock news feed...")
    
    news_items = [
        {
            "id": 1,
            "title": "Fed Signals Possible Rate Cut in Coming Months",
            "summary": "Federal Reserve officials hint at potential interest rate reduction amid cooling inflation.",
            "source": "Financial Times",
            "timestamp": datetime.now().isoformat(),
            "sentiment": "positive",
            "relevance_score": 0.85,
            "symbols": ["SPY", "DIA", "QQQ"]
        },
        {
            "id": 2,
            "title": "Tech Giants Report Strong Q4 Earnings",
            "summary": "Major technology companies exceed analyst expectations in latest quarterly reports.",
            "source": "Reuters",
            "timestamp": (datetime.now() - timedelta(hours=2)).isoformat(),
            "sentiment": "positive",
            "relevance_score": 0.92,
            "symbols": ["AAPL", "MSFT", "GOOGL", "META"]
        },
        {
            "id": 3,
            "title": "Oil Prices Surge on Supply Concerns",
            "summary": "Crude oil prices jump 3% following reports of production cuts.",
            "source": "Bloomberg",
            "timestamp": (datetime.now() - timedelta(hours=4)).isoformat(),
            "sentiment": "negative",
            "relevance_score": 0.78,
            "symbols": ["XOM", "CVX", "USO"]
        },
        {
            "id": 4,
            "title": "Cryptocurrency Market Shows Signs of Recovery",
            "summary": "Bitcoin and Ethereum gain momentum as institutional interest returns.",
            "source": "CoinDesk",
            "timestamp": (datetime.now() - timedelta(hours=6)).isoformat(),
            "sentiment": "positive",
            "relevance_score": 0.75,
            "symbols": ["BTC-USD", "ETH-USD"]
        },
        {
            "id": 5,
            "title": "Global Supply Chain Disruptions Ease",
            "summary": "Shipping costs decline as port congestion improves worldwide.",
            "source": "Wall Street Journal",
            "timestamp": (datetime.now() - timedelta(hours=8)).isoformat(),
            "sentiment": "positive",
            "relevance_score": 0.80,
            "symbols": ["FDX", "UPS", "AMZN"]
        }
    ]
    
    # Save to file
    with open(MOCK_DATA_SOURCES["news_feed"], "w") as f:
        json.dump(news_items, f, indent=2)
    
    print(f"✅ Mock news feed saved to: {MOCK_DATA_SOURCES['news_feed']}")

def generate_mock_market_data():
    """Generate mock market data"""
    print("Generating mock market data...")
    
    market_data = {
        "indices": {
            "SP500": {"value": 4783.45, "change": 0.52, "change_percent": 0.011},
            "NASDAQ": {"value": 15123.67, "change": -0.18, "change_percent": -0.001},
            "DOW": {"value": 37863.80, "change": 0.33, "change_percent": 0.009},
            "RUSSELL": {"value": 2024.55, "change": 0.71, "change_percent": 0.035}
        },
        "sectors": {
            "Technology": {"change": 1.23},
            "Healthcare": {"change": -0.45},
            "Finance": {"change": 0.67},
            "Energy": {"change": 2.15},
            "Consumer": {"change": 0.33}
        },
        "market_status": "closed",
        "last_update": datetime.now().isoformat()
    }
    
    # Save to file
    with open(MOCK_DATA_SOURCES["market_data"], "w") as f:
        json.dump(market_data, f, indent=2)
    
    print(f"✅ Mock market data saved to: {MOCK_DATA_SOURCES['market_data']}")

def generate_mock_user_profiles():
    """Generate mock user profiles"""
    print("Generating mock user profiles...")
    
    profiles = {
        "1": {
            "user_id": 1,
            "risk_profile": "moderate",
            "investment_goals": ["retirement", "wealth_growth"],
            "preferred_sectors": ["technology", "healthcare"],
            "portfolio_value": 50000.00,
            "monthly_investment": 1000.00,
            "experience_level": "intermediate"
        },
        "2": {
            "user_id": 2,
            "risk_profile": "conservative",
            "investment_goals": ["capital_preservation", "income"],
            "preferred_sectors": ["utilities", "consumer_staples"],
            "portfolio_value": 100000.00,
            "monthly_investment": 2000.00,
            "experience_level": "beginner"
        },
        "3": {
            "user_id": 3,
            "risk_profile": "aggressive",
            "investment_goals": ["growth", "speculation"],
            "preferred_sectors": ["technology", "cryptocurrency"],
            "portfolio_value": 25000.00,
            "monthly_investment": 500.00,
            "experience_level": "advanced"
        }
    }
    
    # Save to file
    with open(MOCK_DATA_SOURCES["user_profiles"], "w") as f:
        json.dump(profiles, f, indent=2)
    
    print(f"✅ Mock user profiles saved to: {MOCK_DATA_SOURCES['user_profiles']}")

def main():
    """Set up the complete test environment"""
    print("🚀 Setting up Oryza test environment...")
    print("=" * 50)
    
    # Create mock data directory
    MOCK_DATA_DIR.mkdir(exist_ok=True)
    
    # Setup database
    setup_sqlite_database()
    
    # Generate mock data
    generate_mock_stock_prices()
    generate_mock_news()
    generate_mock_market_data()
    generate_mock_user_profiles()
    
    print("=" * 50)
    print("✅ Test environment setup complete!")
    print("\nYou can now run the services with:")
    print("  python backend/test_runner.py")
    
if __name__ == "__main__":
    main() 