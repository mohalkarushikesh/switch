"""
Data Manager - Handles historical market data
"""
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime, date, timedelta
import logging
from decimal import Decimal
import random
import pandas as pd

from .models import MarketData, DataFrequency


class DataManager:
    """
    Manages historical market data for backtesting
    """
    
    def __init__(self):
        self.logger = logging.getLogger("data_manager")
        
        # Data storage
        self.market_data = {}  # symbol -> List[MarketData]
        self.symbol_info = {}  # symbol -> info
        
        # Data cache
        self.data_cache = {}  # (symbol, start, end, freq) -> data
        
    async def initialize(self):
        """Initialize data manager"""
        self.logger.info("Initializing Data Manager")
        
        # In production:
        # - Connect to data providers
        # - Load historical data
        # - Set up data feeds
        
        # Generate sample data
        await self._generate_sample_data()
        
    async def _generate_sample_data(self):
        """Generate sample market data for testing"""
        symbols = [
            {"symbol": "AAPL", "name": "Apple Inc.", "asset_class": "equity", "base_price": 150},
            {"symbol": "MSFT", "name": "Microsoft Corp.", "asset_class": "equity", "base_price": 300},
            {"symbol": "GOOGL", "name": "Alphabet Inc.", "asset_class": "equity", "base_price": 100},
            {"symbol": "TSLA", "name": "Tesla Inc.", "asset_class": "equity", "base_price": 200},
            {"symbol": "NVDA", "name": "NVIDIA Corp.", "asset_class": "equity", "base_price": 400},
            {"symbol": "AMD", "name": "AMD Inc.", "asset_class": "equity", "base_price": 100},
            {"symbol": "SPY", "name": "S&P 500 ETF", "asset_class": "etf", "base_price": 400},
            {"symbol": "QQQ", "name": "Nasdaq 100 ETF", "asset_class": "etf", "base_price": 350},
            {"symbol": "BTC-USD", "name": "Bitcoin", "asset_class": "crypto", "base_price": 40000},
            {"symbol": "ETH-USD", "name": "Ethereum", "asset_class": "crypto", "base_price": 2500}
        ]
        
        # Generate 2 years of daily data for each symbol
        end_date = date.today()
        start_date = end_date - timedelta(days=730)
        
        for symbol_info in symbols:
            symbol = symbol_info["symbol"]
            self.symbol_info[symbol] = symbol_info
            
            # Generate price data
            data_points = []
            current_date = start_date
            price = Decimal(str(symbol_info["base_price"]))
            
            while current_date <= end_date:
                # Skip weekends for stocks/ETFs
                if symbol_info["asset_class"] in ["equity", "etf"] and current_date.weekday() >= 5:
                    current_date += timedelta(days=1)
                    continue
                    
                # Generate OHLCV data with some randomness
                daily_volatility = random.uniform(0.01, 0.03)  # 1-3% daily volatility
                
                # Random walk for price movement
                price_change = price * Decimal(str(random.gauss(0, daily_volatility)))
                price = max(price + price_change, Decimal("1"))  # Ensure positive price
                
                # Generate OHLC
                open_price = price
                high_price = price * Decimal(str(1 + random.uniform(0, daily_volatility)))
                low_price = price * Decimal(str(1 - random.uniform(0, daily_volatility)))
                close_price = price * Decimal(str(1 + random.uniform(-daily_volatility/2, daily_volatility/2)))
                
                # Ensure high >= low
                if high_price < low_price:
                    high_price, low_price = low_price, high_price
                    
                # Ensure close is within high/low
                close_price = max(low_price, min(high_price, close_price))
                
                # Generate volume
                base_volume = 1000000 if symbol_info["asset_class"] == "equity" else 100000
                volume = Decimal(str(random.randint(int(base_volume * 0.5), int(base_volume * 1.5))))
                
                market_data = MarketData(
                    symbol=symbol,
                    timestamp=datetime.combine(current_date, datetime.min.time()),
                    open=open_price,
                    high=high_price,
                    low=low_price,
                    close=close_price,
                    volume=volume,
                    vwap=(high_price + low_price + close_price) / 3
                )
                
                data_points.append(market_data)
                
                # Update price for next day
                price = close_price
                current_date += timedelta(days=1)
                
            self.market_data[symbol] = data_points
            
        self.logger.info(f"Generated sample data for {len(symbols)} symbols")
        
    async def get_market_data(
        self,
        symbols: List[str],
        start_date: date,
        end_date: date,
        frequency: DataFrequency
    ) -> Dict[date, Dict[str, Any]]:
        """Get market data for backtesting"""
        # Check cache
        cache_key = (tuple(symbols), start_date, end_date, frequency)
        if cache_key in self.data_cache:
            return self.data_cache[cache_key]
            
        # Prepare data
        result = {}
        
        # For each date in range
        current_date = start_date
        while current_date <= end_date:
            date_data = {}
            
            for symbol in symbols:
                if symbol not in self.market_data:
                    self.logger.warning(f"No data available for symbol: {symbol}")
                    continue
                    
                # Find data point for this date
                symbol_data = self.market_data[symbol]
                
                for data_point in symbol_data:
                    if data_point.timestamp.date() == current_date:
                        date_data[symbol] = {
                            "open": data_point.open,
                            "high": data_point.high,
                            "low": data_point.low,
                            "close": data_point.close,
                            "volume": data_point.volume,
                            "vwap": data_point.vwap
                        }
                        break
                        
            if date_data:  # Only add if we have data for at least one symbol
                result[current_date] = date_data
                
            current_date += timedelta(days=1)
            
        # Cache result
        self.data_cache[cache_key] = result
        
        return result
        
    async def get_available_symbols(
        self,
        asset_class: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get list of available symbols"""
        symbols = []
        
        for symbol, info in self.symbol_info.items():
            if asset_class and info["asset_class"] != asset_class:
                continue
                
            # Get date range
            if symbol in self.market_data and self.market_data[symbol]:
                first_date = self.market_data[symbol][0].timestamp.date()
                last_date = self.market_data[symbol][-1].timestamp.date()
            else:
                first_date = last_date = None
                
            symbols.append({
                "symbol": symbol,
                "name": info["name"],
                "asset_class": info["asset_class"],
                "first_date": first_date.isoformat() if first_date else None,
                "last_date": last_date.isoformat() if last_date else None,
                "data_points": len(self.market_data.get(symbol, []))
            })
            
        return symbols
        
    async def get_symbol_date_range(self, symbol: str) -> Dict[str, Any]:
        """Get available date range for a symbol"""
        if symbol not in self.market_data or not self.market_data[symbol]:
            return {
                "symbol": symbol,
                "first_date": None,
                "last_date": None,
                "trading_days": 0
            }
            
        data = self.market_data[symbol]
        
        return {
            "symbol": symbol,
            "first_date": data[0].timestamp.date().isoformat(),
            "last_date": data[-1].timestamp.date().isoformat(),
            "trading_days": len(data)
        }
        
    async def upload_data(
        self,
        symbol: str,
        data: List[MarketData]
    ) -> bool:
        """Upload custom market data"""
        try:
            # Validate data
            if not data:
                return False
                
            # Sort by timestamp
            data.sort(key=lambda x: x.timestamp)
            
            # Store data
            self.market_data[symbol] = data
            
            # Update symbol info if not exists
            if symbol not in self.symbol_info:
                self.symbol_info[symbol] = {
                    "symbol": symbol,
                    "name": symbol,
                    "asset_class": "custom"
                }
                
            # Clear cache
            self.data_cache.clear()
            
            self.logger.info(f"Uploaded {len(data)} data points for {symbol}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error uploading data: {str(e)}")
            return False
            
    async def get_latest_price(self, symbol: str) -> Optional[Decimal]:
        """Get latest price for a symbol"""
        if symbol not in self.market_data or not self.market_data[symbol]:
            return None
            
        return self.market_data[symbol][-1].close
        
    async def resample_data(
        self,
        data: List[MarketData],
        target_frequency: DataFrequency
    ) -> List[MarketData]:
        """Resample data to different frequency"""
        # In production, implement proper resampling logic
        # For now, return original data
        return data
        
    async def calculate_returns(
        self,
        symbol: str,
        start_date: date,
        end_date: date
    ) -> pd.Series:
        """Calculate returns for a symbol"""
        # Get data
        data = await self.get_market_data([symbol], start_date, end_date, DataFrequency.DAILY)
        
        # Extract prices
        prices = []
        dates = []
        
        for date, date_data in sorted(data.items()):
            if symbol in date_data:
                prices.append(float(date_data[symbol]["close"]))
                dates.append(date)
                
        if len(prices) < 2:
            return pd.Series()
            
        # Calculate returns
        returns = pd.Series(prices, index=dates).pct_change().dropna()
        
        return returns
        
    async def get_benchmark_data(
        self,
        benchmark: str = "SPY"
    ) -> Dict[date, Decimal]:
        """Get benchmark data for comparison"""
        if benchmark not in self.market_data:
            self.logger.warning(f"Benchmark {benchmark} not available")
            return {}
            
        result = {}
        
        for data_point in self.market_data[benchmark]:
            result[data_point.timestamp.date()] = data_point.close
            
        return result 