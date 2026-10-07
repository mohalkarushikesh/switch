"""
Backtesting Engine for Investment Strategies
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime, timedelta
import random
from dataclasses import dataclass

@dataclass
class Trade:
    """Represents a single trade"""
    entry_date: datetime
    exit_date: Optional[datetime]
    symbol: str
    quantity: int
    entry_price: float
    exit_price: Optional[float]
    trade_type: str  # 'buy' or 'sell'
    status: str  # 'open' or 'closed'
    pnl: Optional[float] = None
    pnl_percentage: Optional[float] = None

class BacktestingEngine:
    """
    Engine for backtesting investment strategies
    """
    
    def __init__(self):
        self.is_initialized = False
        self.historical_data = {}
        self.commission_rate = 0.001  # 0.1% commission
        
        # Performance metrics
        self.metrics = {
            "total_return": 0,
            "annualized_return": 0,
            "sharpe_ratio": 0,
            "max_drawdown": 0,
            "win_rate": 0,
            "profit_factor": 0,
            "total_trades": 0
        }
        
    async def initialize(self):
        """Initialize the backtesting engine"""
        # In production, load historical data
        await self._load_historical_data()
        self.is_initialized = True
        
    async def _load_historical_data(self):
        """Load historical price data for backtesting"""
        # Simulate loading historical data
        # In production, this would connect to a real data source
        
        symbols = ["RELIANCE", "TCS", "HDFC", "INFY", "ICICI"]
        
        for symbol in symbols:
            # Generate synthetic price data
            dates = pd.date_range(start='2020-01-01', end='2024-01-01', freq='D')
            base_price = random.uniform(1000, 3000)
            
            prices = []
            for i in range(len(dates)):
                # Random walk with trend
                change = np.random.normal(0.0005, 0.02)  # 0.05% daily return with 2% volatility
                base_price *= (1 + change)
                prices.append({
                    'date': dates[i],
                    'open': base_price * random.uniform(0.98, 1.02),
                    'high': base_price * random.uniform(1.0, 1.03),
                    'low': base_price * random.uniform(0.97, 1.0),
                    'close': base_price,
                    'volume': random.randint(1000000, 5000000)
                })
            
            self.historical_data[symbol] = pd.DataFrame(prices)
            self.historical_data[symbol].set_index('date', inplace=True)
    
    async def run_backtest(
        self,
        strategy: Dict[str, Any],
        start_date: str,
        end_date: str,
        initial_capital: float = 1000000
    ) -> Dict[str, Any]:
        """
        Run a backtest for a given strategy
        """
        # Parse strategy
        strategy_type = strategy.get("type", "moving_average")
        parameters = strategy.get("parameters", {})
        symbols = strategy.get("symbols", ["RELIANCE", "TCS"])
        
        # Initialize portfolio
        portfolio = {
            "cash": initial_capital,
            "positions": {},
            "value": initial_capital,
            "trades": [],
            "daily_values": []
        }
        
        # Convert dates
        start_dt = pd.to_datetime(start_date)
        end_dt = pd.to_datetime(end_date)
        
        # Get strategy function
        strategy_func = self._get_strategy_function(strategy_type)
        
        # Run backtest day by day
        current_date = start_dt
        
        while current_date <= end_dt:
            # Get signals for each symbol
            for symbol in symbols:
                if symbol in self.historical_data:
                    signal = await strategy_func(
                        symbol, 
                        current_date, 
                        parameters, 
                        portfolio,
                        self.historical_data[symbol]
                    )
                    
                    # Execute trades based on signal
                    if signal:
                        await self._execute_trade(
                            portfolio, 
                            symbol, 
                            signal, 
                            current_date
                        )
            
            # Update portfolio value
            portfolio_value = await self._calculate_portfolio_value(
                portfolio, 
                current_date
            )
            portfolio["value"] = portfolio_value
            portfolio["daily_values"].append({
                "date": current_date,
                "value": portfolio_value
            })
            
            # Move to next day
            current_date += timedelta(days=1)
        
        # Calculate performance metrics
        performance = await self._calculate_performance_metrics(
            portfolio, 
            initial_capital
        )
        
        # Analyze trades
        trade_analysis = await self._analyze_trades(portfolio["trades"])
        
        return {
            "strategy": strategy,
            "period": {
                "start": start_date,
                "end": end_date
            },
            "initial_capital": initial_capital,
            "final_value": portfolio["value"],
            "performance": performance,
            "trade_analysis": trade_analysis,
            "trades": self._format_trades(portfolio["trades"]),
            "equity_curve": portfolio["daily_values"]
        }
    
    def _get_strategy_function(self, strategy_type: str) -> Callable:
        """Get the strategy function based on type"""
        strategies = {
            "moving_average": self._moving_average_strategy,
            "momentum": self._momentum_strategy,
            "mean_reversion": self._mean_reversion_strategy,
            "breakout": self._breakout_strategy
        }
        
        return strategies.get(strategy_type, self._moving_average_strategy)
    
    async def _moving_average_strategy(
        self,
        symbol: str,
        date: datetime,
        parameters: Dict[str, Any],
        portfolio: Dict[str, Any],
        price_data: pd.DataFrame
    ) -> Optional[Dict[str, Any]]:
        """
        Simple moving average crossover strategy
        """
        short_period = parameters.get("short_period", 10)
        long_period = parameters.get("long_period", 30)
        
        # Get price data up to current date
        historical = price_data[price_data.index <= date]
        
        if len(historical) < long_period:
            return None
        
        # Calculate moving averages
        short_ma = historical['close'].rolling(window=short_period).mean().iloc[-1]
        long_ma = historical['close'].rolling(window=long_period).mean().iloc[-1]
        current_price = historical['close'].iloc[-1]
        
        # Check current position
        current_position = portfolio["positions"].get(symbol, 0)
        
        # Generate signal
        if short_ma > long_ma and current_position == 0:
            # Buy signal
            return {
                "action": "buy",
                "quantity": int(portfolio["cash"] * 0.2 / current_price),  # Use 20% of cash
                "price": current_price,
                "reason": f"MA crossover: {short_period}MA > {long_period}MA"
            }
        elif short_ma < long_ma and current_position > 0:
            # Sell signal
            return {
                "action": "sell",
                "quantity": current_position,
                "price": current_price,
                "reason": f"MA crossover: {short_period}MA < {long_period}MA"
            }
        
        return None
    
    async def _momentum_strategy(
        self,
        symbol: str,
        date: datetime,
        parameters: Dict[str, Any],
        portfolio: Dict[str, Any],
        price_data: pd.DataFrame
    ) -> Optional[Dict[str, Any]]:
        """
        Momentum-based strategy
        """
        lookback_period = parameters.get("lookback_period", 20)
        
        historical = price_data[price_data.index <= date]
        
        if len(historical) < lookback_period:
            return None
        
        # Calculate momentum
        returns = historical['close'].pct_change(lookback_period).iloc[-1]
        current_price = historical['close'].iloc[-1]
        current_position = portfolio["positions"].get(symbol, 0)
        
        # Strong positive momentum
        if returns > 0.1 and current_position == 0:
            return {
                "action": "buy",
                "quantity": int(portfolio["cash"] * 0.25 / current_price),
                "price": current_price,
                "reason": f"Strong momentum: {returns:.2%} return over {lookback_period} days"
            }
        # Momentum reversal
        elif returns < -0.05 and current_position > 0:
            return {
                "action": "sell",
                "quantity": current_position,
                "price": current_price,
                "reason": f"Momentum reversal: {returns:.2%} return"
            }
        
        return None
    
    async def _mean_reversion_strategy(
        self,
        symbol: str,
        date: datetime,
        parameters: Dict[str, Any],
        portfolio: Dict[str, Any],
        price_data: pd.DataFrame
    ) -> Optional[Dict[str, Any]]:
        """
        Mean reversion strategy using Bollinger Bands
        """
        period = parameters.get("period", 20)
        std_dev = parameters.get("std_dev", 2)
        
        historical = price_data[price_data.index <= date]
        
        if len(historical) < period:
            return None
        
        # Calculate Bollinger Bands
        sma = historical['close'].rolling(window=period).mean()
        std = historical['close'].rolling(window=period).std()
        
        upper_band = sma + (std * std_dev)
        lower_band = sma - (std * std_dev)
        
        current_price = historical['close'].iloc[-1]
        current_position = portfolio["positions"].get(symbol, 0)
        
        # Price below lower band - potential buy
        if current_price < lower_band.iloc[-1] and current_position == 0:
            return {
                "action": "buy",
                "quantity": int(portfolio["cash"] * 0.15 / current_price),
                "price": current_price,
                "reason": f"Price below lower Bollinger Band"
            }
        # Price above upper band - potential sell
        elif current_price > upper_band.iloc[-1] and current_position > 0:
            return {
                "action": "sell",
                "quantity": current_position,
                "price": current_price,
                "reason": f"Price above upper Bollinger Band"
            }
        
        return None
    
    async def _breakout_strategy(
        self,
        symbol: str,
        date: datetime,
        parameters: Dict[str, Any],
        portfolio: Dict[str, Any],
        price_data: pd.DataFrame
    ) -> Optional[Dict[str, Any]]:
        """
        Breakout strategy based on price channels
        """
        lookback = parameters.get("lookback", 20)
        
        historical = price_data[price_data.index <= date]
        
        if len(historical) < lookback:
            return None
        
        # Calculate recent high and low
        recent_high = historical['high'].rolling(window=lookback).max().iloc[-1]
        recent_low = historical['low'].rolling(window=lookback).min().iloc[-1]
        current_price = historical['close'].iloc[-1]
        current_position = portfolio["positions"].get(symbol, 0)
        
        # Breakout above recent high
        if current_price > recent_high * 1.01 and current_position == 0:
            return {
                "action": "buy",
                "quantity": int(portfolio["cash"] * 0.2 / current_price),
                "price": current_price,
                "reason": f"Breakout above {lookback}-day high"
            }
        # Breakdown below recent low
        elif current_price < recent_low * 0.99 and current_position > 0:
            return {
                "action": "sell",
                "quantity": current_position,
                "price": current_price,
                "reason": f"Breakdown below {lookback}-day low"
            }
        
        return None
    
    async def _execute_trade(
        self,
        portfolio: Dict[str, Any],
        symbol: str,
        signal: Dict[str, Any],
        date: datetime
    ):
        """Execute a trade based on signal"""
        action = signal["action"]
        quantity = signal["quantity"]
        price = signal["price"]
        
        if quantity <= 0:
            return
        
        # Calculate commission
        trade_value = quantity * price
        commission = trade_value * self.commission_rate
        
        if action == "buy":
            # Check if we have enough cash
            total_cost = trade_value + commission
            if total_cost <= portfolio["cash"]:
                portfolio["cash"] -= total_cost
                portfolio["positions"][symbol] = portfolio["positions"].get(symbol, 0) + quantity
                
                # Record trade
                trade = Trade(
                    entry_date=date,
                    exit_date=None,
                    symbol=symbol,
                    quantity=quantity,
                    entry_price=price,
                    exit_price=None,
                    trade_type="buy",
                    status="open"
                )
                portfolio["trades"].append(trade)
        
        elif action == "sell":
            # Check if we have the position
            if portfolio["positions"].get(symbol, 0) >= quantity:
                portfolio["positions"][symbol] -= quantity
                portfolio["cash"] += trade_value - commission
                
                # Find and close the corresponding buy trade
                for trade in reversed(portfolio["trades"]):
                    if (trade.symbol == symbol and 
                        trade.status == "open" and 
                        trade.trade_type == "buy"):
                        trade.exit_date = date
                        trade.exit_price = price
                        trade.status = "closed"
                        trade.pnl = (price - trade.entry_price) * trade.quantity - commission * 2
                        trade.pnl_percentage = ((price - trade.entry_price) / trade.entry_price) * 100
                        break
    
    async def _calculate_portfolio_value(
        self,
        portfolio: Dict[str, Any],
        date: datetime
    ) -> float:
        """Calculate total portfolio value"""
        total_value = portfolio["cash"]
        
        for symbol, quantity in portfolio["positions"].items():
            if symbol in self.historical_data:
                price_data = self.historical_data[symbol]
                current_prices = price_data[price_data.index <= date]
                if not current_prices.empty:
                    current_price = current_prices['close'].iloc[-1]
                    total_value += quantity * current_price
        
        return total_value
    
    async def _calculate_performance_metrics(
        self,
        portfolio: Dict[str, Any],
        initial_capital: float
    ) -> Dict[str, Any]:
        """Calculate various performance metrics"""
        if not portfolio["daily_values"]:
            return self.metrics
        
        # Convert to pandas series for easier calculation
        values = pd.DataFrame(portfolio["daily_values"])
        values['returns'] = values['value'].pct_change()
        
        # Total return
        total_return = (portfolio["value"] - initial_capital) / initial_capital
        
        # Annualized return
        days = len(values)
        years = days / 365
        annualized_return = (1 + total_return) ** (1 / years) - 1 if years > 0 else 0
        
        # Sharpe ratio (assuming risk-free rate of 4%)
        if len(values) > 1:
            daily_returns = values['returns'].dropna()
            sharpe_ratio = (daily_returns.mean() * 252 - 0.04) / (daily_returns.std() * np.sqrt(252)) if daily_returns.std() > 0 else 0
        else:
            sharpe_ratio = 0
        
        # Maximum drawdown
        rolling_max = values['value'].expanding().max()
        drawdown = (values['value'] - rolling_max) / rolling_max
        max_drawdown = drawdown.min()
        
        return {
            "total_return": round(total_return * 100, 2),
            "annualized_return": round(annualized_return * 100, 2),
            "sharpe_ratio": round(sharpe_ratio, 2),
            "max_drawdown": round(max_drawdown * 100, 2),
            "volatility": round(daily_returns.std() * np.sqrt(252) * 100, 2) if len(values) > 1 else 0
        }
    
    async def _analyze_trades(self, trades: List[Trade]) -> Dict[str, Any]:
        """Analyze trading performance"""
        if not trades:
            return {
                "total_trades": 0,
                "winning_trades": 0,
                "losing_trades": 0,
                "win_rate": 0,
                "avg_win": 0,
                "avg_loss": 0,
                "profit_factor": 0
            }
        
        closed_trades = [t for t in trades if t.status == "closed"]
        
        if not closed_trades:
            return {
                "total_trades": 0,
                "winning_trades": 0,
                "losing_trades": 0,
                "win_rate": 0,
                "avg_win": 0,
                "avg_loss": 0,
                "profit_factor": 0
            }
        
        winning_trades = [t for t in closed_trades if t.pnl > 0]
        losing_trades = [t for t in closed_trades if t.pnl <= 0]
        
        total_profit = sum(t.pnl for t in winning_trades) if winning_trades else 0
        total_loss = abs(sum(t.pnl for t in losing_trades)) if losing_trades else 0
        
        return {
            "total_trades": len(closed_trades),
            "winning_trades": len(winning_trades),
            "losing_trades": len(losing_trades),
            "win_rate": round(len(winning_trades) / len(closed_trades) * 100, 2) if closed_trades else 0,
            "avg_win": round(total_profit / len(winning_trades), 2) if winning_trades else 0,
            "avg_loss": round(total_loss / len(losing_trades), 2) if losing_trades else 0,
            "profit_factor": round(total_profit / total_loss, 2) if total_loss > 0 else 0,
            "largest_win": round(max(t.pnl for t in winning_trades), 2) if winning_trades else 0,
            "largest_loss": round(min(t.pnl for t in losing_trades), 2) if losing_trades else 0
        }
    
    def _format_trades(self, trades: List[Trade]) -> List[Dict[str, Any]]:
        """Format trades for output"""
        formatted_trades = []
        
        for trade in trades:
            if trade.status == "closed":
                formatted_trades.append({
                    "symbol": trade.symbol,
                    "entry_date": trade.entry_date.strftime("%Y-%m-%d"),
                    "exit_date": trade.exit_date.strftime("%Y-%m-%d") if trade.exit_date else None,
                    "quantity": trade.quantity,
                    "entry_price": round(trade.entry_price, 2),
                    "exit_price": round(trade.exit_price, 2) if trade.exit_price else None,
                    "pnl": round(trade.pnl, 2) if trade.pnl else None,
                    "pnl_percentage": round(trade.pnl_percentage, 2) if trade.pnl_percentage else None,
                    "status": trade.status
                })
        
        return formatted_trades[:50]  # Return last 50 trades 