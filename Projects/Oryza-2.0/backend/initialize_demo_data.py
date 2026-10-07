"""
Initialize Demo Data for Oryza Platform
This script sets up sample data for demonstrating AI features
"""
import json
import random
from datetime import datetime, timedelta
from pathlib import Path

# Create mock_data directory if it doesn't exist
mock_data_dir = Path(__file__).parent / "mock_data"
mock_data_dir.mkdir(exist_ok=True)

# Sample companies for demo
companies = [
    {"symbol": "RELIANCE", "name": "Reliance Industries", "sector": "Energy"},
    {"symbol": "TCS", "name": "Tata Consultancy Services", "sector": "Technology"},
    {"symbol": "HDFC", "name": "HDFC Bank", "sector": "Banking"},
    {"symbol": "INFY", "name": "Infosys", "sector": "Technology"},
    {"symbol": "ITC", "name": "ITC Limited", "sector": "Consumer Goods"},
    {"symbol": "WIPRO", "name": "Wipro", "sector": "Technology"},
    {"symbol": "BHARTIARTL", "name": "Bharti Airtel", "sector": "Telecom"},
    {"symbol": "ADANIGREEN", "name": "Adani Green Energy", "sector": "Renewable Energy"},
    {"symbol": "HCLTECH", "name": "HCL Technologies", "sector": "Technology"},
    {"symbol": "MARUTI", "name": "Maruti Suzuki", "sector": "Automobile"}
]

# Generate market data
def generate_market_data():
    indices = {
        "NIFTY50": {
            "value": 19845.50,
            "change": 125.30,
            "changePercent": 0.63,
            "volume": 2345678901,
            "dayHigh": 19895.20,
            "dayLow": 19725.80
        },
        "SENSEX": {
            "value": 65782.30,
            "change": 412.45,
            "changePercent": 0.63,
            "volume": 1876543210,
            "dayHigh": 65950.10,
            "dayLow": 65450.50
        }
    }
    
    top_gainers = []
    top_losers = []
    
    for i, company in enumerate(companies[:5]):
        change_percent = random.uniform(2, 5)
        base_price = random.uniform(500, 5000)
        top_gainers.append({
            "symbol": company["symbol"],
            "name": company["name"],
            "price": base_price,
            "change": base_price * change_percent / 100,
            "changePercent": change_percent,
            "volume": random.randint(1000000, 10000000)
        })
    
    for i, company in enumerate(companies[5:]):
        change_percent = random.uniform(-5, -2)
        base_price = random.uniform(500, 5000)
        top_losers.append({
            "symbol": company["symbol"],
            "name": company["name"],
            "price": base_price,
            "change": base_price * change_percent / 100,
            "changePercent": change_percent,
            "volume": random.randint(1000000, 10000000)
        })
    
    return {
        "indices": indices,
        "topGainers": top_gainers,
        "topLosers": top_losers,
        "lastUpdated": datetime.now().isoformat()
    }

# Generate stock prices
def generate_stock_prices():
    stocks = {}
    for company in companies:
        base_price = random.uniform(500, 5000)
        stocks[company["symbol"]] = {
            "symbol": company["symbol"],
            "name": company["name"],
            "sector": company["sector"],
            "currentPrice": base_price,
            "dayChange": random.uniform(-100, 100),
            "dayChangePercent": random.uniform(-3, 3),
            "dayHigh": base_price * 1.02,
            "dayLow": base_price * 0.98,
            "volume": random.randint(1000000, 50000000),
            "marketCap": base_price * random.randint(1000000, 10000000),
            "pe": random.uniform(15, 35),
            "eps": random.uniform(20, 200),
            "fiftyTwoWeekHigh": base_price * 1.3,
            "fiftyTwoWeekLow": base_price * 0.7
        }
    return stocks

# Generate news feed
def generate_news_feed():
    headlines = [
        {
            "id": "news001",
            "title": "RBI Maintains Policy Rate, Markets React Positively",
            "source": "Economic Times",
            "category": "Economy",
            "summary": "The Reserve Bank of India maintained the repo rate at 6.5%, in line with market expectations.",
            "sentiment": "positive",
            "impact": "medium",
            "timestamp": datetime.now().isoformat(),
            "tags": ["RBI", "Interest Rates", "Economy"]
        },
        {
            "id": "news002",
            "title": "TCS Announces Strong Q3 Results, Beats Estimates",
            "source": "Business Standard",
            "category": "Earnings",
            "summary": "TCS reported a 12% YoY growth in net profit, exceeding analyst expectations.",
            "sentiment": "positive",
            "impact": "high",
            "timestamp": (datetime.now() - timedelta(hours=2)).isoformat(),
            "tags": ["TCS", "Earnings", "Technology"]
        },
        {
            "id": "news003",
            "title": "Global Oil Prices Surge on Supply Concerns",
            "source": "Reuters",
            "category": "Commodities",
            "summary": "Crude oil prices jumped 3% amid geopolitical tensions affecting supply chains.",
            "sentiment": "negative",
            "impact": "high",
            "timestamp": (datetime.now() - timedelta(hours=4)).isoformat(),
            "tags": ["Oil", "Energy", "Global Markets"]
        },
        {
            "id": "news004",
            "title": "Adani Green Wins Major Solar Project Contract",
            "source": "Mint",
            "category": "Corporate",
            "summary": "Adani Green Energy secures 2GW solar project, boosting renewable energy capacity.",
            "sentiment": "positive",
            "impact": "medium",
            "timestamp": (datetime.now() - timedelta(hours=6)).isoformat(),
            "tags": ["Adani Green", "Renewable Energy", "ESG"]
        },
        {
            "id": "news005",
            "title": "IT Sector Faces Headwinds from Global Slowdown",
            "source": "Financial Express",
            "category": "Sector Analysis",
            "summary": "Indian IT companies brace for slower growth as global clients cut spending.",
            "sentiment": "negative",
            "impact": "medium",
            "timestamp": (datetime.now() - timedelta(hours=8)).isoformat(),
            "tags": ["IT Sector", "Global Economy", "Technology"]
        }
    ]
    
    return {
        "articles": headlines,
        "totalCount": len(headlines),
        "categories": ["Economy", "Earnings", "Commodities", "Corporate", "Sector Analysis"],
        "lastUpdated": datetime.now().isoformat()
    }

# Generate user profiles
def generate_user_profiles():
    return {
        "portfolio": {
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
                    "gainPercent": 4.53,
                    "sector": "Energy"
                },
                {
                    "symbol": "TCS",
                    "name": "Tata Consultancy Services",
                    "quantity": 30,
                    "avgPrice": 3400.00,
                    "currentPrice": 3567.80,
                    "value": 107034,
                    "gain": 5034,
                    "gainPercent": 4.94,
                    "sector": "Technology"
                },
                {
                    "symbol": "HDFC",
                    "name": "HDFC Bank",
                    "quantity": 80,
                    "avgPrice": 1550.00,
                    "currentPrice": 1654.30,
                    "value": 132344,
                    "gain": 8344,
                    "gainPercent": 6.73,
                    "sector": "Banking"
                },
                {
                    "symbol": "ADANIGREEN",
                    "name": "Adani Green Energy",
                    "quantity": 40,
                    "avgPrice": 950.00,
                    "currentPrice": 1125.50,
                    "value": 45020,
                    "gain": 7020,
                    "gainPercent": 18.47,
                    "sector": "Renewable Energy"
                }
            ],
            "assetAllocation": {
                "equity": 70,
                "debt": 20,
                "commodities": 5,
                "cash": 5
            },
            "sectorAllocation": {
                "Technology": 35,
                "Banking": 25,
                "Energy": 20,
                "Renewable": 10,
                "Others": 10
            }
        },
        "riskProfile": {
            "score": 42.5,
            "category": "Moderate",
            "tolerance": "Medium",
            "investmentHorizon": "5-10 years",
            "lastAssessed": datetime.now().isoformat()
        },
        "goals": [
            {
                "id": "goal001",
                "name": "Retirement Fund",
                "targetAmount": 10000000,
                "currentAmount": 2500000,
                "targetDate": "2045-12-31",
                "monthlyContribution": 50000,
                "progress": 25,
                "feasibility": "on_track",
                "aiConfidence": 0.82
            },
            {
                "id": "goal002",
                "name": "Children's Education",
                "targetAmount": 5000000,
                "currentAmount": 1000000,
                "targetDate": "2035-06-30",
                "monthlyContribution": 25000,
                "progress": 20,
                "feasibility": "needs_adjustment",
                "aiConfidence": 0.75
            }
        ],
        "preferences": {
            "esgInvesting": True,
            "autoRebalancing": True,
            "taxOptimization": True,
            "notifications": {
                "email": True,
                "sms": False,
                "push": True
            }
        }
    }

# Save all data
def save_demo_data():
    print("🚀 Initializing Oryza Demo Data...")
    
    # Generate and save market data
    market_data = generate_market_data()
    with open(mock_data_dir / "market_data.json", "w") as f:
        json.dump(market_data, f, indent=2)
    print("✅ Market data created")
    
    # Generate and save stock prices
    stock_prices = generate_stock_prices()
    with open(mock_data_dir / "stock_prices.json", "w") as f:
        json.dump(stock_prices, f, indent=2)
    print("✅ Stock prices created")
    
    # Generate and save news feed
    news_feed = generate_news_feed()
    with open(mock_data_dir / "news_feed.json", "w") as f:
        json.dump(news_feed, f, indent=2)
    print("✅ News feed created")
    
    # Generate and save user profiles
    user_profiles = generate_user_profiles()
    with open(mock_data_dir / "user_profiles.json", "w") as f:
        json.dump(user_profiles, f, indent=2)
    print("✅ User profiles created")
    
    print("\n✨ Demo data initialization complete!")
    print(f"📁 Data saved in: {mock_data_dir.absolute()}")

if __name__ == "__main__":
    save_demo_data() 