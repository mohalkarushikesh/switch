"""
Strategy Runner - Executes trading strategies
"""
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime, date, timedelta
import logging
from decimal import Decimal
import numpy as np
import pandas as pd

from .models import (
    Strategy, StrategyType, Signal, SignalType,
    Portfolio, MarketData
)
from .data_manager import DataManager


class StrategyRunner:
    """
    Executes trading strategies and generates signals
    """
    
    def __init__(self, data_manager: DataManager):
        self.logger = logging.getLogger("strategy_runner")
        self.data_manager = data_manager
        
        # Strategy templates
        self.strategy_templates = {}
        
    async def initialize(self):
        """Initialize strategy runner"""
        self.logger.info("Initializing Strategy Runner")
        
        # Create strategy templates
        await self._create_strategy_templates()
        
    async def _create_strategy_templates(self):
        """Create pre-built strategy templates"""
        self.strategy_templates = {
            "sma_crossover": {
                "name": "SMA Crossover",
                "description": "Simple Moving Average crossover strategy",
                "type": StrategyType.TREND_FOLLOWING,
                "parameters": {
                    "fast_period": 20,
                    "slow_period": 50
                },
                "code": """
def generate_signals(data, params):
    fast_ma = data['close'].rolling(params['fast_period']).mean()
    slow_ma = data['close'].rolling(params['slow_period']).mean()
    
    signals = []
    if fast_ma.iloc[-1] > slow_ma.iloc[-1] and fast_ma.iloc[-2] <= slow_ma.iloc[-2]:
        signals.append({'type': 'BUY', 'strength': 0.8})
    elif fast_ma.iloc[-1] < slow_ma.iloc[-1] and fast_ma.iloc[-2] >= slow_ma.iloc[-2]:
        signals.append({'type': 'SELL', 'strength': 0.8})
        
    return signals
"""
            },
            "bollinger_bands": {
                "name": "Bollinger Bands",
                "description": "Mean reversion using Bollinger Bands",
                "type": StrategyType.MEAN_REVERSION,
                "parameters": {
                    "period": 20,
                    "std_dev": 2
                },
                "code": """
def generate_signals(data, params):
    middle = data['close'].rolling(params['period']).mean()
    std = data['close'].rolling(params['period']).std()
    upper = middle + params['std_dev'] * std
    lower = middle - params['std_dev'] * std
    
    signals = []
    if data['close'].iloc[-1] < lower.iloc[-1]:
        signals.append({'type': 'BUY', 'strength': 0.7})
    elif data['close'].iloc[-1] > upper.iloc[-1]:
        signals.append({'type': 'SELL', 'strength': 0.7})
        
    return signals
"""
            },
            "rsi_momentum": {
                "name": "RSI Momentum",
                "description": "Momentum strategy using RSI",
                "type": StrategyType.MOMENTUM,
                "parameters": {
                    "rsi_period": 14,
                    "oversold": 30,
                    "overbought": 70
                },
                "code": """
def generate_signals(data, params):
    # Calculate RSI
    delta = data['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(params['rsi_period']).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(params['rsi_period']).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    
    signals = []
    if rsi.iloc[-1] < params['oversold']:
        signals.append({'type': 'BUY', 'strength': 0.9})
    elif rsi.iloc[-1] > params['overbought']:
        signals.append({'type': 'SELL', 'strength': 0.9})
        
    return signals
"""
            }
        }
        
    async def generate_signals(
        self,
        strategy: Strategy,
        portfolio: Portfolio,
        market_data: Dict[str, Any],
        historical_data: Dict[date, Dict[str, Any]],
        current_date: date
    ) -> List[Signal]:
        """Generate trading signals based on strategy"""
        signals = []
        
        for symbol in strategy.symbols:
            # Get historical data for symbol
            symbol_data = await self._prepare_symbol_data(
                symbol, historical_data, current_date, strategy.parameters
            )
            
            if not symbol_data:
                continue
                
            # Generate signals based on strategy type
            if strategy.strategy_type == StrategyType.TREND_FOLLOWING:
                symbol_signals = await self._trend_following_signals(
                    strategy, symbol, symbol_data, portfolio
                )
            elif strategy.strategy_type == StrategyType.MEAN_REVERSION:
                symbol_signals = await self._mean_reversion_signals(
                    strategy, symbol, symbol_data, portfolio
                )
            elif strategy.strategy_type == StrategyType.MOMENTUM:
                symbol_signals = await self._momentum_signals(
                    strategy, symbol, symbol_data, portfolio
                )
            elif strategy.strategy_type == StrategyType.CUSTOM and strategy.code:
                symbol_signals = await self._custom_strategy_signals(
                    strategy, symbol, symbol_data, portfolio
                )
            else:
                symbol_signals = []
                
            # Add generated signals
            signals.extend(symbol_signals)
            
            # Check exit conditions for open positions
            exit_signals = await self._check_exit_conditions(
                strategy, symbol, symbol_data, portfolio, current_date
            )
            signals.extend(exit_signals)
            
        return signals
        
    async def _prepare_symbol_data(
        self,
        symbol: str,
        historical_data: Dict[date, Dict[str, Any]],
        current_date: date,
        parameters: Dict[str, Any]
    ) -> Optional[pd.DataFrame]:
        """Prepare historical data for a symbol"""
        # Get lookback period
        lookback = parameters.get("lookback_period", 100)
        
        # Collect data
        data_points = []
        for i in range(lookback):
            data_date = current_date - timedelta(days=i)
            if data_date in historical_data and symbol in historical_data[data_date]:
                data_point = historical_data[data_date][symbol]
                data_points.append({
                    "date": data_date,
                    "open": float(data_point["open"]),
                    "high": float(data_point["high"]),
                    "low": float(data_point["low"]),
                    "close": float(data_point["close"]),
                    "volume": float(data_point["volume"])
                })
                
        if len(data_points) < 10:  # Need minimum data
            return None
            
        # Create DataFrame
        df = pd.DataFrame(data_points)
        df.set_index("date", inplace=True)
        df.sort_index(inplace=True)
        
        return df
        
    async def _trend_following_signals(
        self,
        strategy: Strategy,
        symbol: str,
        data: pd.DataFrame,
        portfolio: Portfolio
    ) -> List[Signal]:
        """Generate trend following signals"""
        signals = []
        params = strategy.parameters
        
        # Calculate moving averages
        fast_period = params.get("fast_period", 20)
        slow_period = params.get("slow_period", 50)
        
        if len(data) < slow_period:
            return signals
            
        fast_ma = data["close"].rolling(fast_period).mean()
        slow_ma = data["close"].rolling(slow_period).mean()
        
        # Check for crossover
        if len(fast_ma) >= 2 and len(slow_ma) >= 2:
            current_fast = fast_ma.iloc[-1]
            prev_fast = fast_ma.iloc[-2]
            current_slow = slow_ma.iloc[-1]
            prev_slow = slow_ma.iloc[-2]
            
            # Golden cross (bullish)
            if current_fast > current_slow and prev_fast <= prev_slow:
                # Check if not already in position
                has_position = any(
                    p.symbol == symbol and p.status == "open"
                    for p in portfolio.positions
                )
                
                if not has_position:
                    signal = Signal(
                        backtest_id="",  # Will be set later
                        symbol=symbol,
                        signal_type=SignalType.BUY,
                        strength=0.8,
                        generated_at=datetime.combine(data.index[-1], datetime.min.time()),
                        current_price=Decimal(str(data["close"].iloc[-1])),
                        indicators={
                            "fast_ma": float(current_fast),
                            "slow_ma": float(current_slow)
                        },
                        reason=f"Golden cross: {fast_period}MA > {slow_period}MA"
                    )
                    signals.append(signal)
                    
            # Death cross (bearish)
            elif current_fast < current_slow and prev_fast >= prev_slow:
                # Check if in long position
                for position in portfolio.positions:
                    if position.symbol == symbol and position.status == "open" and position.quantity > 0:
                        signal = Signal(
                            backtest_id="",
                            symbol=symbol,
                            signal_type=SignalType.SELL,
                            strength=0.8,
                            generated_at=datetime.combine(data.index[-1], datetime.min.time()),
                            current_price=Decimal(str(data["close"].iloc[-1])),
                            indicators={
                                "fast_ma": float(current_fast),
                                "slow_ma": float(current_slow)
                            },
                            reason=f"Death cross: {fast_period}MA < {slow_period}MA"
                        )
                        signals.append(signal)
                        
        return signals
        
    async def _mean_reversion_signals(
        self,
        strategy: Strategy,
        symbol: str,
        data: pd.DataFrame,
        portfolio: Portfolio
    ) -> List[Signal]:
        """Generate mean reversion signals"""
        signals = []
        params = strategy.parameters
        
        # Calculate Bollinger Bands
        period = params.get("lookback_period", 20)
        num_std = params.get("num_std", 2)
        
        if len(data) < period:
            return signals
            
        middle_band = data["close"].rolling(period).mean()
        std_dev = data["close"].rolling(period).std()
        upper_band = middle_band + (std_dev * num_std)
        lower_band = middle_band - (std_dev * num_std)
        
        current_price = data["close"].iloc[-1]
        current_lower = lower_band.iloc[-1]
        current_upper = upper_band.iloc[-1]
        current_middle = middle_band.iloc[-1]
        
        # Check for oversold condition
        if current_price < current_lower:
            # Check if not already in position
            has_position = any(
                p.symbol == symbol and p.status == "open"
                for p in portfolio.positions
            )
            
            if not has_position:
                signal = Signal(
                    backtest_id="",
                    symbol=symbol,
                    signal_type=SignalType.BUY,
                    strength=0.7,
                    generated_at=datetime.combine(data.index[-1], datetime.min.time()),
                    current_price=Decimal(str(current_price)),
                    target_price=Decimal(str(current_middle)),
                    indicators={
                        "bb_lower": float(current_lower),
                        "bb_middle": float(current_middle),
                        "bb_upper": float(current_upper)
                    },
                    reason="Price below lower Bollinger Band"
                )
                signals.append(signal)
                
        # Check for exit condition
        elif current_price > current_middle:
            # Check if in long position
            for position in portfolio.positions:
                if position.symbol == symbol and position.status == "open" and position.quantity > 0:
                    signal = Signal(
                        backtest_id="",
                        symbol=symbol,
                        signal_type=SignalType.SELL,
                        strength=0.6,
                        generated_at=datetime.combine(data.index[-1], datetime.min.time()),
                        current_price=Decimal(str(current_price)),
                        indicators={
                            "bb_middle": float(current_middle)
                        },
                        reason="Price reached middle Bollinger Band"
                    )
                    signals.append(signal)
                    
        return signals
        
    async def _momentum_signals(
        self,
        strategy: Strategy,
        symbol: str,
        data: pd.DataFrame,
        portfolio: Portfolio
    ) -> List[Signal]:
        """Generate momentum signals"""
        signals = []
        params = strategy.parameters
        
        # Calculate momentum indicator (RSI)
        period = params.get("momentum_period", 14)
        
        if len(data) < period + 1:
            return signals
            
        # Calculate RSI
        delta = data["close"].diff()
        gain = (delta.where(delta > 0, 0)).rolling(period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(period).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        current_rsi = rsi.iloc[-1]
        
        # Calculate price momentum
        momentum = (data["close"].iloc[-1] / data["close"].iloc[-period] - 1) * 100
        
        # Strong momentum buy signal
        if current_rsi > 50 and momentum > params.get("entry_percentile", 5):
            # Check if not already in position
            has_position = any(
                p.symbol == symbol and p.status == "open"
                for p in portfolio.positions
            )
            
            if not has_position:
                signal = Signal(
                    backtest_id="",
                    symbol=symbol,
                    signal_type=SignalType.BUY,
                    strength=min(0.9, momentum / 10),  # Stronger signal for higher momentum
                    generated_at=datetime.combine(data.index[-1], datetime.min.time()),
                    current_price=Decimal(str(data["close"].iloc[-1])),
                    indicators={
                        "rsi": float(current_rsi),
                        "momentum": float(momentum)
                    },
                    reason=f"Strong momentum: {momentum:.1f}% gain, RSI: {current_rsi:.0f}"
                )
                signals.append(signal)
                
        # Momentum exhaustion sell signal
        elif current_rsi > 70 or momentum < -params.get("exit_percentile", 5):
            # Check if in long position
            for position in portfolio.positions:
                if position.symbol == symbol and position.status == "open" and position.quantity > 0:
                    signal = Signal(
                        backtest_id="",
                        symbol=symbol,
                        signal_type=SignalType.SELL,
                        strength=0.7,
                        generated_at=datetime.combine(data.index[-1], datetime.min.time()),
                        current_price=Decimal(str(data["close"].iloc[-1])),
                        indicators={
                            "rsi": float(current_rsi),
                            "momentum": float(momentum)
                        },
                        reason="Momentum exhaustion or reversal"
                    )
                    signals.append(signal)
                    
        return signals
        
    async def _custom_strategy_signals(
        self,
        strategy: Strategy,
        symbol: str,
        data: pd.DataFrame,
        portfolio: Portfolio
    ) -> List[Signal]:
        """Execute custom strategy code"""
        signals = []
        
        try:
            # Create safe execution environment
            local_vars = {
                "data": data,
                "params": strategy.parameters,
                "portfolio": portfolio,
                "symbol": symbol
            }
            
            # Execute strategy code
            exec(strategy.code, {"__builtins__": {}}, local_vars)
            
            # Get generated signals
            if "signals" in local_vars:
                raw_signals = local_vars["signals"]
                
                # Convert to Signal objects
                for raw_signal in raw_signals:
                    signal = Signal(
                        backtest_id="",
                        symbol=symbol,
                        signal_type=SignalType[raw_signal["type"]],
                        strength=raw_signal.get("strength", 0.5),
                        generated_at=datetime.combine(data.index[-1], datetime.min.time()),
                        current_price=Decimal(str(data["close"].iloc[-1])),
                        indicators=raw_signal.get("indicators", {}),
                        reason=raw_signal.get("reason", "Custom strategy signal")
                    )
                    signals.append(signal)
                    
        except Exception as e:
            self.logger.error(f"Error executing custom strategy: {str(e)}")
            
        return signals
        
    async def _check_exit_conditions(
        self,
        strategy: Strategy,
        symbol: str,
        data: pd.DataFrame,
        portfolio: Portfolio,
        current_date: date
    ) -> List[Signal]:
        """Check exit conditions for open positions"""
        signals = []
        
        current_price = Decimal(str(data["close"].iloc[-1]))
        
        for position in portfolio.positions:
            if position.symbol != symbol or position.status != "open":
                continue
                
            # Check stop loss
            if strategy.stop_loss and position.quantity > 0:
                stop_price = position.entry_price * (1 - Decimal(str(strategy.stop_loss)))
                if current_price <= stop_price:
                    signal = Signal(
                        backtest_id="",
                        symbol=symbol,
                        signal_type=SignalType.STOP_LOSS,
                        strength=1.0,
                        generated_at=datetime.combine(current_date, datetime.min.time()),
                        current_price=current_price,
                        stop_price=stop_price,
                        reason=f"Stop loss triggered at {strategy.stop_loss:.1%}"
                    )
                    signals.append(signal)
                    
            # Check take profit
            if strategy.take_profit and position.quantity > 0:
                target_price = position.entry_price * (1 + Decimal(str(strategy.take_profit)))
                if current_price >= target_price:
                    signal = Signal(
                        backtest_id="",
                        symbol=symbol,
                        signal_type=SignalType.TAKE_PROFIT,
                        strength=1.0,
                        generated_at=datetime.combine(current_date, datetime.min.time()),
                        current_price=current_price,
                        target_price=target_price,
                        reason=f"Take profit triggered at {strategy.take_profit:.1%}"
                    )
                    signals.append(signal)
                    
            # Check time stop
            time_stop = strategy.exit_rules.get("time_stop")
            if time_stop:
                holding_days = (current_date - position.opened_at.date()).days
                if holding_days >= time_stop:
                    signal = Signal(
                        backtest_id="",
                        symbol=symbol,
                        signal_type=SignalType.EXIT,
                        strength=0.6,
                        generated_at=datetime.combine(current_date, datetime.min.time()),
                        current_price=current_price,
                        reason=f"Time stop: held for {holding_days} days"
                    )
                    signals.append(signal)
                    
        return signals
        
    async def validate_strategy(self, strategy: Strategy) -> Dict[str, Any]:
        """Validate strategy configuration"""
        errors = []
        warnings = []
        
        # Check basic requirements
        if not strategy.name:
            errors.append("Strategy name is required")
            
        if not strategy.symbols:
            errors.append("At least one symbol is required")
            
        # Validate parameters based on strategy type
        if strategy.strategy_type == StrategyType.TREND_FOLLOWING:
            if "fast_period" not in strategy.parameters:
                errors.append("Trend following strategy requires 'fast_period' parameter")
            if "slow_period" not in strategy.parameters:
                errors.append("Trend following strategy requires 'slow_period' parameter")
                
            # Check period relationship
            fast = strategy.parameters.get("fast_period", 0)
            slow = strategy.parameters.get("slow_period", 0)
            if fast >= slow:
                errors.append("Fast period must be less than slow period")
                
        elif strategy.strategy_type == StrategyType.MEAN_REVERSION:
            if "lookback_period" not in strategy.parameters:
                errors.append("Mean reversion strategy requires 'lookback_period' parameter")
                
        elif strategy.strategy_type == StrategyType.MOMENTUM:
            if "momentum_period" not in strategy.parameters:
                errors.append("Momentum strategy requires 'momentum_period' parameter")
                
        elif strategy.strategy_type == StrategyType.CUSTOM:
            if not strategy.code:
                errors.append("Custom strategy requires code implementation")
            else:
                # Try to compile code
                try:
                    compile(strategy.code, "<string>", "exec")
                except SyntaxError as e:
                    errors.append(f"Invalid Python syntax: {str(e)}")
                    
        # Validate risk parameters
        if strategy.stop_loss and (strategy.stop_loss <= 0 or strategy.stop_loss >= 1):
            errors.append("Stop loss must be between 0 and 1 (0-100%)")
            
        if strategy.take_profit and strategy.take_profit <= 0:
            errors.append("Take profit must be greater than 0")
            
        # Warnings
        if strategy.stop_loss and strategy.stop_loss > 0.1:
            warnings.append("Stop loss is greater than 10%, which is quite high")
            
        if len(strategy.symbols) > 50:
            warnings.append("Large number of symbols may slow down backtesting")
            
        return {
            "is_valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }
        
    async def get_strategy_templates(self) -> List[Dict[str, Any]]:
        """Get available strategy templates"""
        templates = []
        
        for key, template in self.strategy_templates.items():
            templates.append({
                "id": key,
                "name": template["name"],
                "description": template["description"],
                "type": template["type"],
                "parameters": template["parameters"]
            })
            
        return templates 