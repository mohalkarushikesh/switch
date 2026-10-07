"""
Test configuration for Oryza platform
Following restrictions from restricted_tools_and_services.md
"""
import os
from pathlib import Path

# Base directory
BASE_DIR = Path(__file__).parent

# 🚫 PostgreSQL/MongoDB disabled due to resource limitations
# 🛠️ Using SQLite for local testing
DATABASE_URL = f"sqlite:///{BASE_DIR}/test_oryza.db"

# 🚫 Redis disabled for testing
# 🛠️ Using in-memory cache
REDIS_URL = None
USE_MEMORY_CACHE = True

# 🚫 External APIs disabled
# 🛠️ Using local mock data
USE_MOCK_DATA = True
MOCK_DATA_DIR = BASE_DIR / "mock_data"

# Create mock data directory if it doesn't exist
MOCK_DATA_DIR.mkdir(exist_ok=True)

# Test environment settings
APP_ENV = "test"
DEBUG = True
SECRET_KEY = "test-secret-key-not-for-production"

# Service ports (for local testing)
SERVICE_PORTS = {
    "advisory-engine": 8000,
    "news-sentiment": 8001,
    "emotion-tracker": 8002,
    "screening-engine": 8003,
    "goal-planner": 8004,
    "execution-agent": 8005,
    "compliance-monitor": 8006,
    "multi-agent-optimizer": 8007,
    "esg-advisor": 8008,
    "wealth-concierge": 8009,
    "agent-orchestrator": 8010,
    "behavioral-predictor": 8011,
    "notification-service": 8012,
    "tax-optimizer": 8013,
    "education-hub": 8014,
    "risk-profiler": 8015,
    "market-maker": 8016,
    "fraud-detector": 8017,
    "backtesting-engine": 8018,
    "payment-gateway": 8019
}

# 🚫 External financial APIs disabled
# 🛠️ Mock data sources
MOCK_DATA_SOURCES = {
    "stock_prices": MOCK_DATA_DIR / "stock_prices.json",
    "news_feed": MOCK_DATA_DIR / "news_feed.json",
    "market_data": MOCK_DATA_DIR / "market_data.json",
    "user_profiles": MOCK_DATA_DIR / "user_profiles.json"
}

# 🚫 ML models disabled
# 🛠️ Using simple scoring algorithms
USE_SIMPLE_ML = True
DISABLE_HEAVY_MODELS = True

print(f"Test configuration loaded. Using SQLite database at: {DATABASE_URL}")
print(f"Mock data directory: {MOCK_DATA_DIR}") 