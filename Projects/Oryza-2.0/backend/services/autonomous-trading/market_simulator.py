"""
Market Data Simulator
Generates realistic market data for autonomous trading demonstration
"""

import random
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import math

class MarketSimulator:
    def __init__(self):
        self.stocks = {
            "RELIANCE": {"base_price": 2456.50, "volatility": 0.02, "trend": 0.0001},
            "TCS": {"base_price": 3480.75, "volatility": 0.015, "trend": 0.0002},
            "INFY": {"base_price": 1485.30, "volatility": 0.018, "trend": -0.0001},
            "HDFC": {"base_price": 1625.40, "volatility": 0.016, "trend": 0.00015},
            "ITC": {"base_price": 435.20, "volatility": 0.012, "trend": 0.0001},
            "WIPRO": {"base_price": 425.60, "volatility": 0.02, "trend": -0.00005},
            "BHARTIARTL": {"base_price": 845.35, "volatility": 0.019, "trend": 0.0002},
            "HCLTECH": {"base_price": 1156.80, "volatility": 0.017, "trend": 0.00018},
            "SBIN": {"base_price": 567.90, "volatility": 0.021, "trend": 0.00012},
        }
        
        self.current_prices = {symbol: data["base_price"] for symbol, data in self.stocks.items()}
        self.price_history = {symbol: [data["base_price"]] for symbol, data in self.stocks.items()}
        self.volumes = {symbol: random.randint(1000000, 5000000) for symbol in self.stocks.items()}
        
        # Earnings calendar
        self.earnings_calendar = {
            "RELIANCE": datetime.now() + timedelta(days=random.randint(5, 30)),
            "TCS": datetime.now() + timedelta(days=random.randint(5, 30)),
            "INFY": datetime.now() + timedelta(days=random.randint(5, 30)),
        }
        
        # Technical indicators
        self.technical_data = {}
        self.breakout_levels = {}
        self.support_resistance = {}
        
        self.is_market_open = True
        self.last_update = datetime.now()
        
    async def start_simulation(self):
        """Start the market simulation"""
        while True:
            if self.is_market_open:
                await self.update_prices()
                await self.check_patterns()
                await self.simulate_news_events()
            await asyncio.sleep(1)  # Update every second
            
    async def update_prices(self):
        """Update stock prices with realistic movements"""
        for symbol, stock_data in self.stocks.items():
            current_price = self.current_prices[symbol]
            volatility = stock_data["volatility"]
            trend = stock_data["trend"]
            
            # Generate price movement
            random_walk = random.gauss(0, volatility)
            trend_component = trend * current_price
            
            # Add intraday patterns
            time_of_day = datetime.now().hour + datetime.now().minute / 60
            intraday_pattern = 0
            
            # Opening volatility (9-10 AM)
            if 9 <= time_of_day < 10:
                intraday_pattern = random.gauss(0, volatility * 2)
            # Lunch time low volatility (12-1 PM)
            elif 12 <= time_of_day < 13:
                intraday_pattern = random.gauss(0, volatility * 0.5)
            # Closing volatility (3-3:30 PM)
            elif 15 <= time_of_day < 15.5:
                intraday_pattern = random.gauss(0, volatility * 1.5)
                
            # Calculate new price
            price_change = (random_walk + trend_component + intraday_pattern) * current_price
            new_price = max(current_price * 0.8, current_price + price_change)  # Limit to 20% drop
            
            self.current_prices[symbol] = new_price
            self.price_history[symbol].append(new_price)
            
            # Keep only last 1000 prices
            if len(self.price_history[symbol]) > 1000:
                self.price_history[symbol] = self.price_history[symbol][-1000:]
                
            # Update volume
            self.volumes[symbol] = int(self.volumes[symbol] * random.uniform(0.8, 1.2))
            
            # Update technical indicators
            await self.calculate_technicals(symbol)
            
    async def calculate_technicals(self, symbol: str):
        """Calculate technical indicators"""
        prices = self.price_history[symbol]
        if len(prices) < 20:
            return
            
        # RSI Calculation
        gains = []
        losses = []
        for i in range(1, min(14, len(prices))):
            diff = prices[i] - prices[i-1]
            if diff > 0:
                gains.append(diff)
                losses.append(0)
            else:
                gains.append(0)
                losses.append(abs(diff))
                
        avg_gain = sum(gains) / len(gains) if gains else 0
        avg_loss = sum(losses) / len(losses) if losses else 0
        
        rs = avg_gain / avg_loss if avg_loss > 0 else 100
        rsi = 100 - (100 / (1 + rs))
        
        # Moving Averages
        ma_20 = sum(prices[-20:]) / 20 if len(prices) >= 20 else prices[-1]
        ma_50 = sum(prices[-50:]) / 50 if len(prices) >= 50 else prices[-1]
        
        # Support and Resistance
        recent_high = max(prices[-50:]) if len(prices) >= 50 else max(prices)
        recent_low = min(prices[-50:]) if len(prices) >= 50 else min(prices)
        
        self.technical_data[symbol] = {
            "rsi": rsi,
            "ma_20": ma_20,
            "ma_50": ma_50,
            "price": self.current_prices[symbol],
            "volume": self.volumes[symbol],
            "high_52w": recent_high,
            "low_52w": recent_low,
            "support": recent_low * 1.02,  # 2% above low
            "resistance": recent_high * 0.98,  # 2% below high
        }
        
        # Check for breakout levels
        if self.current_prices[symbol] > recent_high * 0.99:
            self.breakout_levels[symbol] = {
                "type": "resistance_breakout",
                "level": recent_high,
                "strength": "strong" if self.volumes[symbol] > self.volumes[symbol] * 1.5 else "moderate"
            }
        elif self.current_prices[symbol] < recent_low * 1.01:
            self.breakout_levels[symbol] = {
                "type": "support_breakdown", 
                "level": recent_low,
                "strength": "strong" if self.volumes[symbol] > self.volumes[symbol] * 1.5 else "moderate"
            }
            
    async def check_patterns(self):
        """Check for trading patterns"""
        for symbol in self.stocks:
            if symbol not in self.technical_data:
                continue
                
            tech = self.technical_data[symbol]
            
            # MACD-like crossover
            if len(self.price_history[symbol]) >= 50:
                if tech["ma_20"] > tech["ma_50"] and self.price_history[symbol][-2] < self.price_history[symbol][-1]:
                    # Bullish crossover
                    self.technical_data[symbol]["macd_signal"] = "bullish_cross"
                elif tech["ma_20"] < tech["ma_50"] and self.price_history[symbol][-2] > self.price_history[symbol][-1]:
                    # Bearish crossover
                    self.technical_data[symbol]["macd_signal"] = "bearish_cross"
                else:
                    self.technical_data[symbol]["macd_signal"] = "neutral"
                    
    async def simulate_news_events(self):
        """Simulate news and earnings events"""
        # Random news events (1% chance per minute)
        for symbol in self.stocks:
            if random.random() < 0.01:
                event_type = random.choice(["positive_news", "negative_news", "neutral_news"])
                impact = 0
                
                if event_type == "positive_news":
                    impact = random.uniform(0.01, 0.03)  # 1-3% positive
                elif event_type == "negative_news":
                    impact = random.uniform(-0.03, -0.01)  # 1-3% negative
                    
                self.current_prices[symbol] *= (1 + impact)
                
            # Check earnings
            if symbol in self.earnings_calendar:
                if datetime.now() >= self.earnings_calendar[symbol]:
                    # Earnings event!
                    earnings_surprise = random.choice(["beat", "miss", "meet"])
                    if earnings_surprise == "beat":
                        self.current_prices[symbol] *= random.uniform(1.03, 1.08)  # 3-8% jump
                    elif earnings_surprise == "miss":
                        self.current_prices[symbol] *= random.uniform(0.92, 0.97)  # 3-8% drop
                        
                    # Set next earnings date
                    self.earnings_calendar[symbol] = datetime.now() + timedelta(days=90)
                    
    def get_market_data(self, symbol: str) -> Dict[str, Any]:
        """Get current market data for a symbol"""
        if symbol not in self.stocks:
            return None
            
        tech = self.technical_data.get(symbol, {})
        breakout = self.breakout_levels.get(symbol, None)
        
        return {
            "symbol": symbol,
            "price": self.current_prices[symbol],
            "change": self.current_prices[symbol] - self.stocks[symbol]["base_price"],
            "change_percent": ((self.current_prices[symbol] / self.stocks[symbol]["base_price"]) - 1) * 100,
            "volume": self.volumes[symbol],
            "timestamp": datetime.now().isoformat(),
            "technical": {
                "rsi": tech.get("rsi", 50),
                "ma_20": tech.get("ma_20", self.current_prices[symbol]),
                "ma_50": tech.get("ma_50", self.current_prices[symbol]),
                "macd_signal": tech.get("macd_signal", "neutral"),
                "support": tech.get("support", self.current_prices[symbol] * 0.95),
                "resistance": tech.get("resistance", self.current_prices[symbol] * 1.05),
            },
            "breakout": breakout,
            "next_earnings": self.earnings_calendar.get(symbol, None),
        }
        
    def get_all_market_data(self) -> Dict[str, Any]:
        """Get market data for all symbols"""
        return {symbol: self.get_market_data(symbol) for symbol in self.stocks} 