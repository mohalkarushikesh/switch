"""
Autonomous Trading Engine
Monitors markets 24/7, detects patterns, and executes trades automatically
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import random

from .market_simulator import MarketSimulator
from .fund_analyzer import FundAnalyzer
from .fixed_income_analyzer import FixedIncomeAnalyzer
from .commodity_analyzer import CommodityAnalyzer
from .alternative_analyzer import AlternativeAnalyzer
from .global_asset_analyzer import GlobalAssetAnalyzer
from .esg_analyzer import ESGAnalyzer

class AutonomousTradingEngine:
    def __init__(self):
        self.market_simulator = MarketSimulator()
        self.fund_analyzer = FundAnalyzer()
        self.fixed_income_analyzer = FixedIncomeAnalyzer()
        self.commodity_analyzer = CommodityAnalyzer()
        self.alternative_analyzer = AlternativeAnalyzer()
        self.global_asset_analyzer = GlobalAssetAnalyzer()
        self.esg_analyzer = ESGAnalyzer()
        self.logger = logging.getLogger(__name__)
        
        # Trading state
        self.enabled_users = {}  # user_id -> trading_params
        self.positions = {}  # user_id -> list of positions
        self.pending_orders = {}  # user_id -> list of orders
        self.executed_trades = []  # History of all trades
        
        # Fund positions
        self.fund_positions = {}  # user_id -> list of fund holdings
        self.fund_switches = []  # History of fund switches
        
        # Fixed income positions
        self.bond_positions = {}  # user_id -> list of bond holdings
        self.bond_ladders = {}  # user_id -> ladder configuration
        self.bond_trades = []  # History of bond trades
        
        # Commodity positions
        self.commodity_positions = {}  # user_id -> list of commodity holdings
        self.commodity_trades = []  # History of commodity trades
        self.hedge_allocations = {}  # user_id -> hedge allocation params
        
        # Alternative investment positions
        self.alternative_positions = {}  # user_id -> list of alternative holdings
        self.alternative_trades = []  # History of alternative trades
        self.discovered_opportunities = {}  # user_id -> list of discovered opportunities
        
        # Global asset positions
        self.global_positions = {}  # user_id -> list of global asset holdings
        self.global_trades = []  # History of global trades
        self.currency_hedges = {}  # user_id -> currency hedge positions
        
        # ESG investment positions
        self.esg_positions = {}  # user_id -> list of ESG holdings
        self.esg_trades = []  # History of ESG trades
        self.values_profiles = {}  # user_id -> values alignment profile
        self.controversy_alerts = {}  # symbol -> active controversies
        
        # Agent states
        self.agent_decisions = {}  # symbol -> agent analysis
        self.fund_decisions = {}  # fund_id -> fund analysis
        self.bond_decisions = {}  # bond_id -> bond analysis
        self.commodity_decisions = {}  # commodity_id -> commodity analysis
        self.alternative_decisions = {}  # alternative_id -> alternative analysis
        self.global_decisions = {}  # asset_id -> global asset analysis
        self.esg_decisions = {}  # investment_id -> ESG analysis
        self.monitoring_active = False
        
        # Performance tracking
        self.performance_metrics = {
            "total_trades": 0,
            "winning_trades": 0,
            "total_pnl": 0,
            "best_trade": 0,
            "worst_trade": 0,
        }
        
    async def start(self):
        """Start the autonomous trading engine"""
        self.logger.info("Starting Autonomous Trading Engine")
        
        # Start market simulation
        asyncio.create_task(self.market_simulator.start_simulation())
        
        # Wait for initial data
        await asyncio.sleep(5)
        
        # Start monitoring
        self.monitoring_active = True
        asyncio.create_task(self.monitor_markets())
        asyncio.create_task(self.execute_pending_trades())
        asyncio.create_task(self.monitor_positions())
        asyncio.create_task(self.monitor_funds())  # Add fund monitoring
        asyncio.create_task(self.monitor_bonds())  # Add bond monitoring
        asyncio.create_task(self.monitor_commodities())  # Add commodity monitoring
        asyncio.create_task(self.monitor_alternatives())  # Add alternative monitoring
        asyncio.create_task(self.monitor_global_assets())  # Add global asset monitoring
        asyncio.create_task(self.monitor_esg_investments())  # Add ESG monitoring
        
    async def monitor_markets(self):
        """Main monitoring loop - runs 24/7"""
        while self.monitoring_active:
            try:
                # Get market data
                market_data = self.market_simulator.get_all_market_data()
                
                # Run analysis for each stock
                for symbol, data in market_data.items():
                    analysis = await self.analyze_stock(symbol, data)
                    self.agent_decisions[symbol] = analysis
                    
                    # Check if we should trade
                    if analysis["consensus"]["action"] in ["BUY", "STRONG_BUY"]:
                        await self.evaluate_trade_opportunity(symbol, analysis)
                        
                await asyncio.sleep(2)  # Analyze every 2 seconds
                
            except Exception as e:
                self.logger.error(f"Error in market monitoring: {e}")
                await asyncio.sleep(5)
                
    async def analyze_stock(self, symbol: str, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """Multi-agent analysis of a stock"""
        
        # Equity Agent Analysis
        equity_analysis = await self.equity_agent_analysis(symbol, market_data)
        
        # Sentiment Agent Analysis
        sentiment_analysis = await self.sentiment_agent_analysis(symbol, market_data)
        
        # Risk Agent Analysis
        risk_analysis = await self.risk_agent_analysis(symbol, market_data)
        
        # Timing Agent Analysis
        timing_analysis = await self.timing_agent_analysis(symbol, market_data)
        
        # Build consensus
        consensus = await self.build_consensus(
            equity_analysis, sentiment_analysis, risk_analysis, timing_analysis
        )
        
        return {
            "symbol": symbol,
            "timestamp": datetime.now().isoformat(),
            "current_price": market_data["price"],
            "agents": {
                "equity": equity_analysis,
                "sentiment": sentiment_analysis,
                "risk": risk_analysis,
                "timing": timing_analysis,
            },
            "consensus": consensus,
            "market_data": market_data,
        }
        
    async def equity_agent_analysis(self, symbol: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Fundamental and technical analysis"""
        price = data["price"]
        change_percent = data["change_percent"]
        
        # Simple P/E calculation (mock)
        pe_ratio = random.uniform(10, 35)
        
        # Revenue growth (mock - would come from real fundamental data)
        revenue_growth = random.uniform(-5, 30)
        
        # Technical score based on moving averages
        tech_score = 5  # Base score
        if data["technical"]["ma_20"] > data["technical"]["ma_50"]:
            tech_score += 2
        if price > data["technical"]["ma_20"]:
            tech_score += 1.5
        if data["technical"]["rsi"] < 70 and data["technical"]["rsi"] > 30:
            tech_score += 1.5
            
        # Check for breakout
        if data.get("breakout"):
            if data["breakout"]["type"] == "resistance_breakout":
                tech_score = min(10, tech_score + 2)
                
        signal = "Buy" if tech_score > 6 else "Hold" if tech_score > 4 else "Sell"
        
        return {
            "pe_ratio": round(pe_ratio, 1),
            "pe_status": "Undervalued" if pe_ratio < 15 else "Fair" if pe_ratio < 25 else "Overvalued",
            "revenue_growth_yoy": f"+{revenue_growth:.1f}%" if revenue_growth > 0 else f"{revenue_growth:.1f}%",
            "technical_score": round(tech_score, 1),
            "signal": signal,
            "signal_strength": "Strong" if tech_score > 7 else "Moderate" if tech_score > 5 else "Weak",
            "breakout_detected": data.get("breakout") is not None,
        }
        
    async def sentiment_agent_analysis(self, symbol: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """News and sentiment analysis"""
        # Check for recent earnings
        earnings_coming = False
        if data.get("next_earnings"):
            days_to_earnings = (data["next_earnings"] - datetime.now()).days
            earnings_coming = days_to_earnings <= 7
            
        # Simulate sentiment based on price movement
        change = data["change_percent"]
        if change > 2:
            sentiment = "Very Positive"
        elif change > 0.5:
            sentiment = "Positive"
        elif change < -2:
            sentiment = "Negative"
        elif change < -0.5:
            sentiment = "Slightly Negative"
        else:
            sentiment = "Neutral"
            
        social_score = random.uniform(5, 10)
        analyst_buy = random.uniform(40, 95)
        
        return {
            "news_sentiment": sentiment,
            "social_score": round(social_score, 1),
            "analyst_rating": f"Buy ({analyst_buy:.0f}%)",
            "market_mood": "Bullish" if sentiment in ["Positive", "Very Positive"] else "Bearish" if "Negative" in sentiment else "Neutral",
            "earnings_coming": earnings_coming,
            "trending_topics": ["Strong momentum", "Technical breakout"] if data.get("breakout") else ["Stable trading"],
        }
        
    async def risk_agent_analysis(self, symbol: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Risk assessment"""
        price = data["price"]
        
        # Volatility based on price movements
        volatility = "High" if abs(data["change_percent"]) > 3 else "Medium" if abs(data["change_percent"]) > 1 else "Low"
        
        # Beta calculation (simplified)
        beta = 1.0 + (abs(data["change_percent"]) / 10)
        
        return {
            "volatility": volatility,
            "beta": round(beta, 2),
            "stop_loss": round(price * 0.95, 2),
            "take_profit": round(price * 1.15, 2),
            "risk_level": volatility,
            "position_size_recommendation": "3-5%" if volatility == "High" else "5-7%" if volatility == "Medium" else "7-10%",
            "max_drawdown_expected": f"{random.uniform(5, 15):.1f}%",
        }
        
    async def timing_agent_analysis(self, symbol: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Market timing analysis"""
        tech = data["technical"]
        
        rsi = tech["rsi"]
        macd = tech.get("macd_signal", "neutral")
        
        # Volume analysis
        volume_trend = "Increasing" if data["volume"] > 2000000 else "Stable"
        
        # Entry signal logic
        entry_signal = "Wait"
        if rsi < 30:
            entry_signal = "Oversold - Good Entry"
        elif rsi > 70:
            entry_signal = "Overbought - Wait"
        elif macd == "bullish_cross":
            entry_signal = "Good"
        elif data.get("breakout"):
            entry_signal = "Breakout - Enter Now"
            
        return {
            "rsi": round(rsi, 0),
            "rsi_signal": "Oversold" if rsi < 30 else "Overbought" if rsi > 70 else "Neutral",
            "macd_signal": macd,
            "volume_trend": volume_trend,
            "entry_signal": entry_signal,
            "market_phase": "Trending" if abs(data["change_percent"]) > 1 else "Ranging",
            "optimal_entry": "Now" if entry_signal in ["Good", "Breakout - Enter Now"] else "Wait",
        }
        
    async def build_consensus(self, equity: Dict, sentiment: Dict, risk: Dict, timing: Dict) -> Dict[str, Any]:
        """Build multi-agent consensus"""
        scores = []
        
        # Equity score
        if equity["signal"] == "Buy":
            scores.append(0.9 if equity["signal_strength"] == "Strong" else 0.7)
        elif equity["signal"] == "Hold":
            scores.append(0.5)
        else:
            scores.append(0.2)
            
        # Sentiment score
        if "Positive" in sentiment["news_sentiment"]:
            scores.append(0.8 if "Very" in sentiment["news_sentiment"] else 0.7)
        elif sentiment["news_sentiment"] == "Neutral":
            scores.append(0.5)
        else:
            scores.append(0.3)
            
        # Risk score
        risk_score_map = {"Low": 0.8, "Medium": 0.6, "High": 0.4}
        scores.append(risk_score_map.get(risk["volatility"], 0.5))
        
        # Timing score
        timing_score_map = {
            "Breakout - Enter Now": 0.95,
            "Good": 0.8,
            "Oversold - Good Entry": 0.85,
            "Wait": 0.4,
            "Overbought - Wait": 0.2,
        }
        scores.append(timing_score_map.get(timing["entry_signal"], 0.5))
        
        # Special conditions boost
        if equity.get("breakout_detected"):
            scores.append(0.9)
        if sentiment.get("earnings_coming"):
            scores.append(0.7)
            
        consensus_score = sum(scores) / len(scores)
        confidence = round(consensus_score * 100)
        
        # Determine action
        if consensus_score > 0.75:
            action = "STRONG_BUY"
            recommendation = "Excellent opportunity - multiple positive signals"
        elif consensus_score > 0.65:
            action = "BUY"
            recommendation = "Good entry point identified"
        elif consensus_score > 0.5:
            action = "HOLD"
            recommendation = "Wait for better entry"
        else:
            action = "AVOID"
            recommendation = "Risk outweighs reward"
            
        return {
            "action": action,
            "confidence": f"{confidence}%",
            "score": consensus_score,
            "recommendation": recommendation,
            "target_return": f"+{random.uniform(10, 25):.1f}%",
            "triggers": {
                "breakout": equity.get("breakout_detected", False),
                "earnings": sentiment.get("earnings_coming", False),
                "oversold": timing["rsi"] < 30,
                "momentum": equity["technical_score"] > 7,
            }
        }
        
    async def evaluate_trade_opportunity(self, symbol: str, analysis: Dict[str, Any]):
        """Evaluate if we should execute a trade"""
        # Check all enabled users
        for user_id, params in self.enabled_users.items():
            # Check if user has capacity
            user_positions = self.positions.get(user_id, [])
            position_value = sum(p["quantity"] * p["current_price"] for p in user_positions)
            
            if position_value >= params["investment_amount"] * 0.9:
                continue  # User is fully invested
                
            # Check if we already have this position
            has_position = any(p["symbol"] == symbol for p in user_positions)
            if has_position and analysis["consensus"]["action"] != "STRONG_BUY":
                continue
                
            # Risk check
            if params["risk_tolerance"] == "conservative" and analysis["agents"]["risk"]["volatility"] == "High":
                continue
                
            # Create order
            await self.create_autonomous_order(user_id, symbol, analysis)
            
    async def create_autonomous_order(self, user_id: str, symbol: str, analysis: Dict[str, Any]):
        """Create an autonomous trade order"""
        params = self.enabled_users[user_id]
        
        # Calculate position size
        available_capital = params["investment_amount"] - sum(
            p["quantity"] * p["current_price"] 
            for p in self.positions.get(user_id, [])
        )
        
        position_size_pct = float(
            analysis["agents"]["risk"]["position_size_recommendation"].split("-")[0]
        ) / 100
        
        position_value = min(
            available_capital,
            params["investment_amount"] * position_size_pct
        )
        
        quantity = int(position_value / analysis["current_price"])
        
        if quantity <= 0:
            return
            
        order = {
            "order_id": f"AT-{datetime.now().strftime('%Y%m%d%H%M%S')}-{random.randint(1000, 9999)}",
            "user_id": user_id,
            "symbol": symbol,
            "action": "BUY",
            "quantity": quantity,
            "price": analysis["current_price"],
            "order_type": "MARKET",
            "status": "PENDING",
            "timestamp": datetime.now(),
            "analysis": analysis,
            "stop_loss": analysis["agents"]["risk"]["stop_loss"],
            "take_profit": analysis["agents"]["risk"]["take_profit"],
            "autonomous": True,
            "confidence": analysis["consensus"]["confidence"],
        }
        
        if user_id not in self.pending_orders:
            self.pending_orders[user_id] = []
        self.pending_orders[user_id].append(order)
        
        self.logger.info(f"Created autonomous order: {order['order_id']} for {symbol}")
        
    async def execute_pending_trades(self):
        """Execute pending autonomous trades"""
        while self.monitoring_active:
            try:
                for user_id, orders in list(self.pending_orders.items()):
                    for order in orders[:]:  # Copy list to allow modification
                        # Simulate execution
                        await asyncio.sleep(0.5)  # Execution delay
                        
                        # Execute trade
                        order["status"] = "EXECUTED"
                        order["execution_time"] = datetime.now()
                        order["execution_price"] = self.market_simulator.current_prices[order["symbol"]]
                        
                        # Add to positions
                        position = {
                            "position_id": order["order_id"],
                            "user_id": user_id,
                            "symbol": order["symbol"],
                            "quantity": order["quantity"],
                            "entry_price": order["execution_price"],
                            "current_price": order["execution_price"],
                            "entry_time": order["execution_time"],
                            "stop_loss": order["stop_loss"],
                            "take_profit": order["take_profit"],
                            "pnl": 0,
                            "pnl_percent": 0,
                            "status": "ACTIVE",
                        }
                        
                        if user_id not in self.positions:
                            self.positions[user_id] = []
                        self.positions[user_id].append(position)
                        
                        # Remove from pending
                        orders.remove(order)
                        
                        # Track execution
                        self.executed_trades.append(order)
                        self.performance_metrics["total_trades"] += 1
                        
                        self.logger.info(
                            f"Executed trade: {order['order_id']} - "
                            f"BUY {order['quantity']} {order['symbol']} @ {order['execution_price']:.2f}"
                        )
                        
                await asyncio.sleep(1)
                
            except Exception as e:
                self.logger.error(f"Error executing trades: {e}")
                await asyncio.sleep(5)
                
    async def monitor_positions(self):
        """Monitor active positions for stop loss/take profit"""
        while self.monitoring_active:
            try:
                for user_id, positions in self.positions.items():
                    for position in positions:
                        if position["status"] != "ACTIVE":
                            continue
                            
                        # Update current price
                        current_price = self.market_simulator.current_prices.get(
                            position["symbol"], position["entry_price"]
                        )
                        position["current_price"] = current_price
                        
                        # Calculate P&L
                        pnl = (current_price - position["entry_price"]) * position["quantity"]
                        pnl_percent = ((current_price / position["entry_price"]) - 1) * 100
                        
                        position["pnl"] = pnl
                        position["pnl_percent"] = pnl_percent
                        
                        # Check stop loss
                        if current_price <= position["stop_loss"]:
                            await self.close_position(position, "STOP_LOSS")
                            
                        # Check take profit
                        elif current_price >= position["take_profit"]:
                            await self.close_position(position, "TAKE_PROFIT")
                            
                        # Dynamic stop loss adjustment
                        elif pnl_percent > 5:  # If profit > 5%, move stop loss up
                            new_stop = position["entry_price"] * 1.02  # 2% above entry
                            position["stop_loss"] = max(position["stop_loss"], new_stop)
                            
                await asyncio.sleep(1)
                
            except Exception as e:
                self.logger.error(f"Error monitoring positions: {e}")
                await asyncio.sleep(5)
                
    async def close_position(self, position: Dict[str, Any], reason: str):
        """Close a position"""
        position["status"] = "CLOSED"
        position["close_time"] = datetime.now()
        position["close_reason"] = reason
        
        # Update performance metrics
        if position["pnl"] > 0:
            self.performance_metrics["winning_trades"] += 1
        self.performance_metrics["total_pnl"] += position["pnl"]
        self.performance_metrics["best_trade"] = max(
            self.performance_metrics["best_trade"], position["pnl"]
        )
        self.performance_metrics["worst_trade"] = min(
            self.performance_metrics["worst_trade"], position["pnl"]
        )
        
        self.logger.info(
            f"Closed position: {position['position_id']} - "
            f"{reason} - P&L: {position['pnl']:.2f} ({position['pnl_percent']:.2f}%)"
        )
        
    def enable_for_user(self, user_id: str, params: Dict[str, Any]):
        """Enable autonomous trading for a user"""
        self.enabled_users[user_id] = params
        self.logger.info(f"Enabled autonomous trading for user {user_id}")
        
    def disable_for_user(self, user_id: str):
        """Disable autonomous trading for a user"""
        if user_id in self.enabled_users:
            del self.enabled_users[user_id]
        self.logger.info(f"Disabled autonomous trading for user {user_id}")
        
    def get_user_positions(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all positions for a user"""
        return self.positions.get(user_id, [])
        
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get overall performance metrics"""
        win_rate = (
            self.performance_metrics["winning_trades"] / self.performance_metrics["total_trades"]
            if self.performance_metrics["total_trades"] > 0 else 0
        )
        
        return {
            **self.performance_metrics,
            "win_rate": f"{win_rate * 100:.1f}%",
            "average_trade": (
                self.performance_metrics["total_pnl"] / self.performance_metrics["total_trades"]
                if self.performance_metrics["total_trades"] > 0 else 0
            ),
        }
        
    # Fund Management Methods
    
    async def monitor_funds(self):
        """Monitor mutual funds and ETFs for switching opportunities"""
        while self.monitoring_active:
            try:
                # Update fund performance
                self.fund_analyzer.update_fund_performance()
                
                # Get all fund opportunities
                opportunities = await self.fund_analyzer.monitor_all_funds()
                
                # Process opportunities for each user
                for user_id, params in self.enabled_users.items():
                    if params.get("include_funds", True):
                        for opportunity in opportunities:
                            await self.evaluate_fund_opportunity(user_id, opportunity)
                            
                await asyncio.sleep(60)  # Check funds every minute
                
            except Exception as e:
                self.logger.error(f"Error monitoring funds: {e}")
                await asyncio.sleep(60)
                
    async def evaluate_fund_opportunity(self, user_id: str, opportunity: Dict[str, Any]):
        """Evaluate and potentially execute fund switches"""
        fund_id = opportunity["fund_id"]
        action = opportunity["action"]
        
        # Get user's fund positions
        user_funds = self.fund_positions.get(user_id, [])
        
        # Check if user owns this fund
        fund_position = next((f for f in user_funds if f["fund_id"] == fund_id), None)
        
        if not fund_position:
            return
            
        if action == "TAX_HARVEST":
            # Execute tax-loss harvesting
            await self.execute_tax_harvest(user_id, fund_position, opportunity)
        elif action == "SWITCH":
            # Execute performance-based switch
            await self.execute_fund_switch(user_id, fund_position, opportunity)
            
    async def execute_tax_harvest(self, user_id: str, position: Dict, opportunity: Dict):
        """Execute tax-loss harvesting"""
        candidates = opportunity["candidates"]
        if not candidates:
            return
            
        # Select best candidate (highest Sharpe ratio)
        best_candidate = candidates[0]
        
        # Execute switch
        switch_result = await self.fund_analyzer.execute_switch(
            from_fund=position["fund_id"],
            to_fund=best_candidate["fund_id"],
            units=position["units"],
            reason="tax_harvest"
        )
        
        # Update positions
        self.fund_positions[user_id].remove(position)
        self.fund_positions[user_id].append({
            "fund_id": best_candidate["fund_id"],
            "units": position["units"],
            "entry_nav": self.fund_analyzer.fund_performance[best_candidate["fund_id"]]["current_nav"],
            "entry_time": datetime.now(),
            "switched_from": position["fund_id"]
        })
        
        # Record switch
        self.fund_switches.append({
            "user_id": user_id,
            **switch_result["switch_details"]
        })
        
        self.logger.info(f"Tax harvest executed for user {user_id}: {switch_result['message']}")
        
    async def execute_fund_switch(self, user_id: str, position: Dict, opportunity: Dict):
        """Execute performance-based fund switch"""
        candidates = opportunity["candidates"]
        if not candidates:
            return
            
        # Don't switch to the same fund
        candidates = [c for c in candidates if c["fund_id"] != position["fund_id"]]
        if not candidates:
            return
            
        # Select best candidate
        best_candidate = candidates[0]
        
        # Execute switch
        switch_result = await self.fund_analyzer.execute_switch(
            from_fund=position["fund_id"],
            to_fund=best_candidate["fund_id"],
            units=position["units"],
            reason="performance"
        )
        
        # Update positions
        self.fund_positions[user_id].remove(position)
        self.fund_positions[user_id].append({
            "fund_id": best_candidate["fund_id"],
            "units": position["units"],
            "entry_nav": self.fund_analyzer.fund_performance[best_candidate["fund_id"]]["current_nav"],
            "entry_time": datetime.now(),
            "switched_from": position["fund_id"]
        })
        
        # Record switch
        self.fund_switches.append({
            "user_id": user_id,
            **switch_result["switch_details"]
        })
        
        self.logger.info(f"Performance switch executed for user {user_id}: {switch_result['message']}")
        
    async def analyze_fund(self, fund_id: str) -> Dict[str, Any]:
        """Get multi-agent analysis for a specific fund"""
        return await self.fund_analyzer.analyze_fund_multi_agent(fund_id)
        
    def get_user_fund_positions(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all fund positions for a user"""
        positions = self.fund_positions.get(user_id, [])
        
        # Enrich with current data
        enriched_positions = []
        for pos in positions:
            fund_data = self.fund_analyzer.funds.get(pos["fund_id"])
            performance = self.fund_analyzer.fund_performance.get(pos["fund_id"])
            
            if fund_data and performance:
                current_value = pos["units"] * performance["current_nav"]
                invested_value = pos["units"] * pos["entry_nav"]
                
                enriched_positions.append({
                    **pos,
                    "fund_name": fund_data["name"],
                    "fund_type": fund_data["type"],
                    "category": fund_data["category"],
                    "current_nav": performance["current_nav"],
                    "current_value": current_value,
                    "invested_value": invested_value,
                    "pnl": current_value - invested_value,
                    "pnl_percent": ((current_value / invested_value) - 1) * 100,
                    "days_held": (datetime.now() - pos["entry_time"]).days
                })
                
        return enriched_positions
        
    def add_fund_position(self, user_id: str, fund_id: str, units: float, nav: float):
        """Add a fund position for a user"""
        if user_id not in self.fund_positions:
            self.fund_positions[user_id] = []
            
        self.fund_positions[user_id].append({
            "fund_id": fund_id,
            "units": units,
            "entry_nav": nav,
            "entry_time": datetime.now()
        })
        
        # Add tax lot for tracking
        self.fund_analyzer.add_tax_lot(fund_id, units, nav)
        
    def get_fund_switch_history(self, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get fund switch history"""
        if user_id:
            return [s for s in self.fund_switches if s.get("user_id") == user_id]
        return self.fund_switches
        
    # Fixed Income Management Methods
    
    async def monitor_bonds(self):
        """Monitor bonds for yield curve changes, credit events, and duration adjustments"""
        while self.monitoring_active:
            try:
                # Update bond prices based on yield curve
                self.fixed_income_analyzer.update_bond_prices()
                
                # Analyze all bonds
                for bond_id in self.fixed_income_analyzer.bonds:
                    analysis = await self.fixed_income_analyzer.analyze_bond_multi_agent(bond_id)
                    self.bond_decisions[bond_id] = analysis
                    
                # Check for opportunities for each user
                for user_id, params in self.enabled_users.items():
                    if params.get("include_bonds", True):
                        await self.evaluate_bond_opportunities(user_id)
                        await self.manage_ladder_rollovers(user_id)
                        
                await asyncio.sleep(30)  # Check bonds every 30 seconds
                
            except Exception as e:
                self.logger.error(f"Error monitoring bonds: {e}")
                await asyncio.sleep(30)
                
    async def evaluate_bond_opportunities(self, user_id: str):
        """Evaluate bond opportunities for a user"""
        user_bonds = self.bond_positions.get(user_id, [])
        
        for position in user_bonds:
            bond_id = position["bond_id"]
            analysis = self.bond_decisions.get(bond_id)
            
            if not analysis:
                continue
                
            consensus = analysis["consensus"]
            
            # Check for duration adjustment needs
            if self.fixed_income_analyzer.market_conditions["rate_environment"] == "rising":
                if analysis["agents"]["duration"]["duration_positioning"] == "Reduce":
                    await self.adjust_bond_duration(user_id, position, "shorten")
                    
            # Check for credit events
            if consensus["action"] == "SELL" and "downgrade risk" in str(consensus.get("key_risks", [])):
                await self.handle_credit_event(user_id, position)
                
    async def manage_ladder_rollovers(self, user_id: str):
        """Manage bond ladder rollovers for maturing bonds"""
        user_ladder = self.bond_ladders.get(user_id)
        if not user_ladder:
            return
            
        user_bonds = self.bond_positions.get(user_id, [])
        
        for position in user_bonds:
            bond = self.fixed_income_analyzer.bonds.get(position["bond_id"])
            if not bond or not bond.get("maturity"):
                continue
                
            days_to_maturity = (bond["maturity"] - datetime.now()).days
            
            # If bond matures within 30 days, find replacement
            if days_to_maturity < 30:
                rollover_recommendation = await self.fixed_income_analyzer.manage_rollover(
                    position["bond_id"],
                    position["face_value"] * position["units"]
                )
                
                if rollover_recommendation["status"] == "Rollover recommended":
                    await self.execute_bond_rollover(user_id, position, rollover_recommendation)
                    
    async def adjust_bond_duration(self, user_id: str, position: Dict, direction: str):
        """Adjust portfolio duration by switching bonds"""
        current_bond = self.fixed_income_analyzer.bonds[position["bond_id"]]
        target_duration = current_bond["duration"] - 2 if direction == "shorten" else current_bond["duration"] + 2
        
        # Find suitable replacement
        candidates = []
        for bond_id, bond in self.fixed_income_analyzer.bonds.items():
            if (bond["rating"] == current_bond["rating"] and
                abs(bond["duration"] - target_duration) < 0.5):
                candidates.append({
                    "bond_id": bond_id,
                    "bond": bond,
                    "duration_diff": bond["duration"] - current_bond["duration"]
                })
                
        if candidates:
            best_candidate = min(candidates, key=lambda x: abs(x["duration_diff"]))
            
            # Execute switch
            self.bond_trades.append({
                "user_id": user_id,
                "trade_type": "duration_adjustment",
                "from_bond": position["bond_id"],
                "to_bond": best_candidate["bond_id"],
                "reason": f"Duration adjustment - {direction}",
                "timestamp": datetime.now()
            })
            
            self.logger.info(f"Duration adjusted for user {user_id}: {current_bond['duration']} -> {best_candidate['bond']['duration']}")
            
    async def handle_credit_event(self, user_id: str, position: Dict):
        """Handle credit deterioration by switching bonds"""
        current_bond = self.fixed_income_analyzer.bonds[position["bond_id"]]
        
        # Find better credit quality bond
        alternatives = []
        for bond_id, bond in self.fixed_income_analyzer.bonds.items():
            if (bond["rating"] > current_bond["rating"] and
                abs(bond["duration"] - current_bond["duration"]) < 1):
                alternatives.append({
                    "bond_id": bond_id,
                    "bond": bond,
                    "yield_diff": bond["yield"] - current_bond["yield"]
                })
                
        if alternatives:
            # Select alternative with minimal yield give-up
            best_alternative = min(alternatives, key=lambda x: abs(x["yield_diff"]))
            
            self.bond_trades.append({
                "user_id": user_id,
                "trade_type": "credit_event",
                "from_bond": position["bond_id"],
                "to_bond": best_alternative["bond_id"],
                "reason": "Credit quality deterioration",
                "timestamp": datetime.now()
            })
            
    async def execute_bond_rollover(self, user_id: str, maturing_position: Dict, recommendation: Dict):
        """Execute bond rollover"""
        # Remove maturing bond
        self.bond_positions[user_id].remove(maturing_position)
        
        # Add replacement bond
        replacement = recommendation["replacement_bond"]
        new_position = {
            "bond_id": replacement["bond_id"],
            "units": maturing_position["units"],
            "face_value": 100,
            "purchase_price": self.fixed_income_analyzer.bond_performance[replacement["bond_id"]]["current_price"],
            "purchase_date": datetime.now()
        }
        
        self.bond_positions[user_id].append(new_position)
        
        self.bond_trades.append({
            "user_id": user_id,
            "trade_type": "rollover",
            "from_bond": maturing_position["bond_id"],
            "to_bond": replacement["bond_id"],
            "reason": "Maturity rollover",
            "yield_pickup": recommendation["replacement_bond"]["yield_pickup"],
            "timestamp": datetime.now()
        })
        
        self.logger.info(f"Bond rollover executed for user {user_id}")
        
    async def construct_bond_ladder(self, user_id: str, amount: float, strategy: str = "moderate") -> Dict[str, Any]:
        """Construct a bond ladder for a user"""
        ladder = await self.fixed_income_analyzer.construct_ladder(amount, strategy)
        
        # Store ladder configuration
        self.bond_ladders[user_id] = ladder
        
        # Add bond positions
        if user_id not in self.bond_positions:
            self.bond_positions[user_id] = []
            
        for bond_data in ladder["bonds"]:
            position = {
                "bond_id": bond_data["bond_id"],
                "units": bond_data["units"],
                "face_value": 100,
                "purchase_price": bond_data["bond"]["price"],
                "purchase_date": datetime.now(),
                "ladder_rung": True
            }
            self.bond_positions[user_id].append(position)
            
        return ladder
        
    def get_user_bond_positions(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all bond positions for a user"""
        positions = self.bond_positions.get(user_id, [])
        
        # Enrich with current data
        enriched_positions = []
        for pos in positions:
            bond_data = self.fixed_income_analyzer.bonds.get(pos["bond_id"])
            performance = self.fixed_income_analyzer.bond_performance.get(pos["bond_id"])
            
            if bond_data and performance:
                current_value = pos["units"] * performance["current_price"]
                purchase_value = pos["units"] * pos["purchase_price"]
                
                enriched_positions.append({
                    **pos,
                    "bond_name": bond_data["name"],
                    "bond_type": bond_data["type"],
                    "rating": bond_data["rating"],
                    "maturity": bond_data["maturity"].isoformat() if bond_data.get("maturity") else None,
                    "coupon": bond_data["coupon"],
                    "current_price": performance["current_price"],
                    "current_yield": performance["current_yield"],
                    "current_value": current_value,
                    "purchase_value": purchase_value,
                    "pnl": current_value - purchase_value,
                    "pnl_percent": ((current_value / purchase_value) - 1) * 100,
                    "accrued_interest": performance["accrued_interest"],
                    "days_to_maturity": performance["days_to_maturity"]
                })
                
        return enriched_positions
        
    def add_bond_position(self, user_id: str, bond_id: str, units: int, price: float):
        """Add a bond position for a user"""
        if user_id not in self.bond_positions:
            self.bond_positions[user_id] = []
            
        self.bond_positions[user_id].append({
            "bond_id": bond_id,
            "units": units,
            "face_value": 100,
            "purchase_price": price,
            "purchase_date": datetime.now()
        })
        
    async def analyze_bond(self, bond_id: str) -> Dict[str, Any]:
        """Get multi-agent analysis for a specific bond"""
        return await self.fixed_income_analyzer.analyze_bond_multi_agent(bond_id)
        
    def get_bond_trades_history(self, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get bond trading history"""
        if user_id:
            return [t for t in self.bond_trades if t.get("user_id") == user_id]
        return self.bond_trades
        
    # Commodity Management Methods
    
    async def monitor_commodities(self):
        """Monitor commodities for macro changes, uncertainty spikes, and inflation"""
        while self.monitoring_active:
            try:
                # Update prices and macro indicators
                self.commodity_analyzer.update_prices()
                self.commodity_analyzer.update_macro_indicators()
                
                # Analyze all commodities
                for commodity_id in self.commodity_analyzer.commodities:
                    analysis = await self.commodity_analyzer.analyze_commodity_multi_agent(commodity_id)
                    self.commodity_decisions[commodity_id] = analysis
                    
                # Check for hedging needs for each user
                for user_id, params in self.enabled_users.items():
                    if params.get("include_commodities", True):
                        await self.evaluate_hedge_needs(user_id)
                        await self.check_inflation_rebalance(user_id)
                        
                await asyncio.sleep(60)  # Check every minute
                
            except Exception as e:
                self.logger.error(f"Error monitoring commodities: {e}")
                await asyncio.sleep(60)
                
    async def evaluate_hedge_needs(self, user_id: str):
        """Evaluate portfolio hedging needs based on uncertainty"""
        market_stress = self.commodity_analyzer.uncertainty_metrics["market_stress"]
        
        if market_stress > self.commodity_analyzer.hedging_rules["uncertainty_threshold"]:
            # Calculate current commodity allocation
            portfolio_value = await self.get_portfolio_value(user_id)
            commodity_value = await self.get_commodity_value(user_id)
            current_allocation = commodity_value / portfolio_value if portfolio_value > 0 else 0
            
            # Execute hedge if needed
            hedge_result = await self.commodity_analyzer.execute_hedge(
                portfolio_value,
                current_allocation
            )
            
            if hedge_result["action"] != "No adjustment needed":
                await self.execute_commodity_hedge(user_id, hedge_result)
                
    async def check_inflation_rebalance(self, user_id: str):
        """Check if inflation-based rebalancing is needed"""
        current_inflation = self.commodity_analyzer.macro_indicators["US_CPI"]["value"]
        
        # Get user's last rebalance date
        last_rebalance = self.hedge_allocations.get(user_id, {}).get("last_rebalance")
        if last_rebalance:
            days_since = (datetime.now() - last_rebalance).days
            if days_since < self.commodity_analyzer.hedging_rules["rebalance_frequency"]:
                return
                
        # Prepare portfolio data
        portfolio = {
            "commodity_positions": self.commodity_positions.get(user_id, [])
        }
        
        # Check rebalancing
        rebalance_result = await self.commodity_analyzer.rebalance_for_inflation(
            portfolio,
            current_inflation
        )
        
        if rebalance_result["rebalance_needed"]:
            await self.execute_inflation_rebalance(user_id, rebalance_result)
            
    async def execute_commodity_hedge(self, user_id: str, hedge_result: Dict):
        """Execute commodity hedge trades"""
        for commodity in hedge_result.get("commodities_to_buy", []):
            self.commodity_trades.append({
                "user_id": user_id,
                "trade_type": "hedge",
                "commodity_id": commodity["commodity_id"],
                "action": "buy",
                "units": commodity["units"],
                "allocation": commodity["allocation"],
                "reason": hedge_result["reason"],
                "timestamp": datetime.now()
            })
            
        self.logger.info(f"Hedge executed for user {user_id}: {hedge_result['action']}")
        
    async def execute_inflation_rebalance(self, user_id: str, rebalance_result: Dict):
        """Execute inflation-based rebalancing"""
        for trade in rebalance_result["trades"]:
            self.commodity_trades.append({
                "user_id": user_id,
                "trade_type": "rebalance",
                "commodity_id": trade["commodity_id"],
                "action": trade["action"].lower(),
                "from_allocation": trade["current_allocation"],
                "to_allocation": trade["target_allocation"],
                "reason": rebalance_result["reason"],
                "timestamp": datetime.now()
            })
            
        # Update last rebalance date
        if user_id not in self.hedge_allocations:
            self.hedge_allocations[user_id] = {}
        self.hedge_allocations[user_id]["last_rebalance"] = datetime.now()
        
        self.logger.info(f"Inflation rebalance executed for user {user_id}")
        
    async def get_portfolio_value(self, user_id: str) -> float:
        """Get total portfolio value for a user"""
        # Mock implementation - would connect to portfolio service
        return 10000000  # 10M INR
        
    async def get_commodity_value(self, user_id: str) -> float:
        """Get total commodity value for a user"""
        positions = self.commodity_positions.get(user_id, [])
        total_value = 0
        
        for position in positions:
            performance = self.commodity_analyzer.commodity_performance.get(position["commodity_id"])
            if performance:
                total_value += position["units"] * performance["current_price"]
                
        return total_value
        
    def add_commodity_position(self, user_id: str, commodity_id: str, units: float, price: float):
        """Add a commodity position for a user"""
        if user_id not in self.commodity_positions:
            self.commodity_positions[user_id] = []
            
        self.commodity_positions[user_id].append({
            "commodity_id": commodity_id,
            "units": units,
            "purchase_price": price,
            "purchase_date": datetime.now(),
            "allocation": 0.1  # Will be recalculated
        })
        
    def get_user_commodity_positions(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all commodity positions for a user"""
        positions = self.commodity_positions.get(user_id, [])
        
        # Enrich with current data
        enriched_positions = []
        for pos in positions:
            commodity_data = self.commodity_analyzer.commodities.get(pos["commodity_id"])
            performance = self.commodity_analyzer.commodity_performance.get(pos["commodity_id"])
            
            if commodity_data and performance:
                current_value = pos["units"] * performance["current_price"]
                purchase_value = pos["units"] * pos["purchase_price"]
                
                enriched_positions.append({
                    **pos,
                    "commodity_name": commodity_data["name"],
                    "commodity_type": commodity_data["type"],
                    "current_price": performance["current_price"],
                    "current_value": current_value,
                    "purchase_value": purchase_value,
                    "pnl": current_value - purchase_value,
                    "pnl_percent": ((current_value / purchase_value) - 1) * 100,
                    "daily_change": performance["daily_change_percent"],
                    "ytd_return": performance["ytd_return"]
                })
                
        return enriched_positions
        
    async def analyze_commodity(self, commodity_id: str) -> Dict[str, Any]:
        """Get multi-agent analysis for a specific commodity"""
        return await self.commodity_analyzer.analyze_commodity_multi_agent(commodity_id)
        
    def get_commodity_trades_history(self, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get commodity trading history"""
        if user_id:
            return [t for t in self.commodity_trades if t.get("user_id") == user_id]
        return self.commodity_trades
        
    def get_macro_indicators(self) -> Dict[str, Any]:
        """Get current macro indicators"""
        return {
            "indicators": self.commodity_analyzer.macro_indicators,
            "uncertainty_metrics": self.commodity_analyzer.uncertainty_metrics,
            "timestamp": datetime.now().isoformat()
        }
        
    # Alternative Investment Management Methods
    
    async def monitor_alternatives(self):
        """Monitor alternative investments for opportunities and liquidity"""
        while self.monitoring_active:
            try:
                # Update prices
                self.alternative_analyzer.update_prices()
                
                # Analyze all alternatives
                for alt_id in self.alternative_analyzer.alternatives:
                    analysis = await self.alternative_analyzer.analyze_alternative_multi_agent(alt_id)
                    self.alternative_decisions[alt_id] = analysis
                    
                # Check for new opportunities for each user
                for user_id, params in self.enabled_users.items():
                    if params.get("include_alternatives", True):
                        await self.discover_alternative_opportunities(user_id)
                        await self.manage_alternative_liquidity(user_id)
                        
                await asyncio.sleep(300)  # Check every 5 minutes
                
            except Exception as e:
                self.logger.error(f"Error monitoring alternatives: {e}")
                await asyncio.sleep(300)
                
    async def discover_alternative_opportunities(self, user_id: str):
        """Discover new alternative investment opportunities"""
        # Get user profile
        portfolio_profile = {
            "risk_tolerance": "medium",  # Would come from user profile
            "target_return": 0.12,
            "liquidity_preference": "medium",
            "time_horizon": 5,
            "portfolio_size": 10000000
        }
        
        # Discover opportunities
        opportunities = await self.alternative_analyzer.discover_opportunities(portfolio_profile)
        
        # Store discovered opportunities
        self.discovered_opportunities[user_id] = opportunities
        
        # Check for high-priority opportunities
        for opp in opportunities:
            if opp["fit_score"] > 0.8:
                self.logger.info(f"High-priority opportunity discovered for user {user_id}: {opp['name']}")
                
    async def manage_alternative_liquidity(self, user_id: str):
        """Manage liquidity across alternative investments"""
        positions = self.alternative_positions.get(user_id, [])
        
        if not positions:
            return
            
        # Prepare portfolio data
        portfolio = {
            "alternative_positions": positions
        }
        
        # Check liquidity management
        liquidity_result = await self.alternative_analyzer.manage_liquidity(portfolio)
        
        if liquidity_result["rebalancing_needed"]:
            self.logger.info(f"Liquidity rebalancing needed for user {user_id}")
            # In production, would execute rebalancing trades
            
    def add_alternative_position(self, user_id: str, alt_id: str, units: float, price: float):
        """Add an alternative investment position"""
        if user_id not in self.alternative_positions:
            self.alternative_positions[user_id] = []
            
        self.alternative_positions[user_id].append({
            "alternative_id": alt_id,
            "units": units,
            "purchase_price": price,
            "purchase_date": datetime.now(),
            "current_value": units * price
        })
        
    def get_user_alternative_positions(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all alternative positions for a user"""
        positions = self.alternative_positions.get(user_id, [])
        
        # Enrich with current data
        enriched_positions = []
        for pos in positions:
            alt_data = self.alternative_analyzer.alternatives.get(pos["alternative_id"])
            performance = self.alternative_analyzer.alternative_performance.get(pos["alternative_id"])
            
            if alt_data and performance:
                current_value = pos["units"] * performance["current_price"]
                purchase_value = pos["units"] * pos["purchase_price"]
                
                enriched_positions.append({
                    **pos,
                    "alternative_name": alt_data["name"],
                    "alternative_type": alt_data["type"],
                    "sub_type": alt_data.get("sub_type", "General"),
                    "current_price": performance["current_price"],
                    "current_value": current_value,
                    "purchase_value": purchase_value,
                    "pnl": current_value - purchase_value,
                    "pnl_percent": ((current_value / purchase_value) - 1) * 100,
                    "daily_change": performance["daily_change_percent"],
                    "ytd_return": performance["ytd_return"],
                    "liquidity": alt_data.get("liquidity", "Unknown"),
                    "liquidity_score": performance["liquidity_score"]
                })
                
        return enriched_positions
        
    async def analyze_alternative(self, alt_id: str) -> Dict[str, Any]:
        """Get multi-agent analysis for a specific alternative"""
        return await self.alternative_analyzer.analyze_alternative_multi_agent(alt_id)
        
    def get_alternative_trades_history(self, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get alternative investment trading history"""
        if user_id:
            return [t for t in self.alternative_trades if t.get("user_id") == user_id]
        return self.alternative_trades
        
    def get_discovered_opportunities(self, user_id: str) -> List[Dict[str, Any]]:
        """Get discovered opportunities for a user"""
        return self.discovered_opportunities.get(user_id, [])
        
    async def invest_in_opportunity(self, user_id: str, opportunity_id: str, amount: float) -> Dict[str, Any]:
        """Invest in a discovered opportunity"""
        # Find the opportunity
        opportunities = self.discovered_opportunities.get(user_id, [])
        opportunity = next((o for o in opportunities if o["id"] == opportunity_id), None)
        
        if not opportunity:
            return {"status": "error", "message": "Opportunity not found"}
            
        # Record the investment
        self.alternative_trades.append({
            "user_id": user_id,
            "trade_type": "new_opportunity",
            "opportunity_id": opportunity_id,
            "opportunity_name": opportunity["name"],
            "amount": amount,
            "expected_return": opportunity["expected_return"],
            "timestamp": datetime.now()
        })
        
        return {
            "status": "success",
            "message": f"Invested ₹{amount:,.0f} in {opportunity['name']}",
            "expected_return": opportunity["expected_return"],
            "time_horizon": opportunity["time_horizon"]
        }
        
    # Global Asset Management Methods
    
    async def monitor_global_assets(self):
        """Monitor global assets for currency movements and rebalancing"""
        while self.monitoring_active:
            try:
                # Update exchange rates
                self.global_asset_analyzer.update_exchange_rates()
                
                # Update prices
                self.global_asset_analyzer.update_prices()
                
                # Analyze all global assets
                for asset_id in self.global_asset_analyzer.global_assets:
                    analysis = await self.global_asset_analyzer.analyze_global_asset_multi_agent(asset_id)
                    self.global_decisions[asset_id] = analysis
                    
                # Check for rebalancing needs for each user
                for user_id, params in self.enabled_users.items():
                    if params.get("include_global", True):
                        await self.check_geographic_rebalancing(user_id)
                        await self.optimize_user_currency_exposure(user_id)
                        
                await asyncio.sleep(300)  # Check every 5 minutes
                
            except Exception as e:
                self.logger.error(f"Error monitoring global assets: {e}")
                await asyncio.sleep(300)
                
    async def check_geographic_rebalancing(self, user_id: str):
        """Check if geographic rebalancing is needed"""
        positions = self.global_positions.get(user_id, [])
        
        if not positions:
            return
            
        # Get user's last rebalance date
        last_rebalance = self.currency_hedges.get(user_id, {}).get("last_geographic_rebalance")
        if last_rebalance:
            days_since = (datetime.now() - last_rebalance).days
            if days_since < 30:  # Monthly rebalancing
                return
                
        # Prepare portfolio data
        portfolio = {
            "global_positions": positions
        }
        
        # Check rebalancing
        rebalance_result = await self.global_asset_analyzer.rebalance_geographic_allocation(portfolio)
        
        if len(rebalance_result["rebalancing_trades"]) > 0:
            self.logger.info(f"Geographic rebalancing needed for user {user_id}")
            # In production, would execute trades
            
            # Update last rebalance date
            if user_id not in self.currency_hedges:
                self.currency_hedges[user_id] = {}
            self.currency_hedges[user_id]["last_geographic_rebalance"] = datetime.now()
            
    async def optimize_user_currency_exposure(self, user_id: str):
        """Optimize currency exposure for a user"""
        positions = self.global_positions.get(user_id, [])
        
        if not positions:
            return
            
        # Prepare portfolio data
        portfolio = {
            "global_positions": positions
        }
        
        # Optimize currency exposure
        optimization_result = await self.global_asset_analyzer.optimize_currency_exposure(portfolio)
        
        # Check if hedging is needed
        if optimization_result["hedging_recommendations"]:
            self.logger.info(f"Currency hedging recommended for user {user_id}")
            # Store recommendations
            if user_id not in self.currency_hedges:
                self.currency_hedges[user_id] = {}
            self.currency_hedges[user_id]["recommendations"] = optimization_result["hedging_recommendations"]
            
    def add_global_position(self, user_id: str, asset_id: str, units: float, price: float):
        """Add a global asset position"""
        if user_id not in self.global_positions:
            self.global_positions[user_id] = []
            
        self.global_positions[user_id].append({
            "asset_id": asset_id,
            "units": units,
            "purchase_price": price,
            "purchase_date": datetime.now(),
            "current_value": units * price
        })
        
    def get_user_global_positions(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all global positions for a user"""
        positions = self.global_positions.get(user_id, [])
        
        # Enrich with current data
        enriched_positions = []
        for pos in positions:
            asset_data = self.global_asset_analyzer.global_assets.get(pos["asset_id"])
            performance = self.global_asset_analyzer.asset_performance.get(pos["asset_id"])
            
            if asset_data and performance:
                current_value = pos["units"] * performance["current_price"]
                purchase_value = pos["units"] * pos["purchase_price"]
                
                enriched_positions.append({
                    **pos,
                    "asset_name": asset_data["name"],
                    "asset_type": asset_data["type"],
                    "region": asset_data["region"],
                    "country": asset_data["country"],
                    "currency": asset_data["currency"],
                    "current_price": performance["current_price"],
                    "current_value": current_value,
                    "purchase_value": purchase_value,
                    "pnl": current_value - purchase_value,
                    "pnl_percent": ((current_value / purchase_value) - 1) * 100,
                    "daily_change": performance["daily_change_percent"],
                    "local_return": performance["local_currency_return"],
                    "usd_return": performance["usd_return"],
                    "is_hedged": asset_data.get("currency_hedged", False)
                })
                
        return enriched_positions
        
    async def analyze_global_asset(self, asset_id: str) -> Dict[str, Any]:
        """Get multi-agent analysis for a specific global asset"""
        return await self.global_asset_analyzer.analyze_global_asset_multi_agent(asset_id)
        
    def get_global_trades_history(self, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get global asset trading history"""
        if user_id:
            return [t for t in self.global_trades if t.get("user_id") == user_id]
        return self.global_trades
        
    def get_currency_exposures(self, user_id: str) -> Dict[str, Any]:
        """Get currency exposures for a user"""
        positions = self.global_positions.get(user_id, [])
        
        if not positions:
            return {"exposures": {}, "recommendations": []}
            
        portfolio = {"global_positions": positions}
        
        # Use analyzer to calculate exposures
        exposures = self.global_asset_analyzer._calculate_currency_exposures(positions)
        
        return {
            "exposures": {k: f"{v*100:.1f}%" for k, v in exposures.items()},
            "total_foreign_exposure": f"{(1 - exposures.get('USD', 0)) * 100:.1f}%",
            "hedging_recommendations": self.currency_hedges.get(user_id, {}).get("recommendations", [])
        }
        
    async def execute_currency_hedge(self, user_id: str, currency: str, hedge_ratio: float) -> Dict[str, Any]:
        """Execute a currency hedge"""
        # Record the hedge
        self.global_trades.append({
            "user_id": user_id,
            "trade_type": "currency_hedge",
            "currency": currency,
            "hedge_ratio": hedge_ratio,
            "timestamp": datetime.now()
        })
        
        # Update hedges tracking
        if user_id not in self.currency_hedges:
            self.currency_hedges[user_id] = {}
            
        if "active_hedges" not in self.currency_hedges[user_id]:
            self.currency_hedges[user_id]["active_hedges"] = {}
            
        self.currency_hedges[user_id]["active_hedges"][currency] = hedge_ratio
        
        return {
            "status": "success",
            "message": f"Currency hedge executed: {hedge_ratio*100:.0f}% of {currency} exposure",
            "estimated_cost": f"{self.global_asset_analyzer._calculate_hedging_cost(currency) * 100:.1f}%"
        }
        
    def get_regional_growth_data(self) -> Dict[str, Any]:
        """Get regional growth projections"""
        return {
            "regional_data": self.global_asset_analyzer.regional_growth,
            "exchange_rates": self.global_asset_analyzer.exchange_rates,
            "currency_volatility": self.global_asset_analyzer.currency_volatility,
            "timestamp": datetime.now().isoformat()
        } 
        
    # ESG Investment Management Methods
    
    async def monitor_esg_investments(self):
        """Monitor ESG investments for controversies and impact changes"""
        while self.monitoring_active:
            try:
                # Update prices
                self.esg_analyzer.update_prices()
                
                # Check for controversies
                for investment_id in self.esg_analyzer.esg_investments:
                    controversy = self.esg_analyzer.check_controversy(investment_id)
                    
                    if controversy["controversy_detected"]:
                        self.logger.warning(f"ESG controversy detected for {investment_id}: {controversy['type']}")
                        
                        # Store controversy
                        if investment_id not in self.controversy_alerts:
                            self.controversy_alerts[investment_id] = []
                        self.controversy_alerts[investment_id].append(controversy)
                        
                        # Check if divestment needed
                        if controversy["action_required"] == "DIVEST":
                            await self.trigger_esg_divestment(investment_id)
                
                # Analyze all ESG investments
                for investment_id in self.esg_analyzer.esg_investments:
                    analysis = await self.esg_analyzer.analyze_esg_investment_multi_agent(investment_id)
                    self.esg_decisions[investment_id] = analysis
                    
                # Check portfolio values alignment for each user
                for user_id, params in self.enabled_users.items():
                    if params.get("esg_enabled", False):
                        await self.check_values_alignment(user_id)
                        
                await asyncio.sleep(300)  # Check every 5 minutes
                
            except Exception as e:
                self.logger.error(f"Error monitoring ESG investments: {e}")
                await asyncio.sleep(300)
                
    async def trigger_esg_divestment(self, investment_id: str):
        """Trigger immediate divestment due to controversy"""
        # Find users holding this investment
        for user_id, positions in self.esg_positions.items():
            for position in positions:
                if position["investment_id"] == investment_id:
                    self.logger.info(f"Triggering divestment of {investment_id} for user {user_id}")
                    
                    # Record divestment
                    self.esg_trades.append({
                        "user_id": user_id,
                        "investment_id": investment_id,
                        "trade_type": "controversy_divestment",
                        "units": position["units"],
                        "price": self.esg_analyzer.investment_performance[investment_id]["current_price"],
                        "reason": "ESG controversy violation",
                        "timestamp": datetime.now()
                    })
                    
                    # Remove position
                    positions.remove(position)
                    
    async def check_values_alignment(self, user_id: str):
        """Check if portfolio aligns with user values"""
        positions = self.esg_positions.get(user_id, [])
        values_profile = self.values_profiles.get(user_id, "balanced_esg")
        
        if positions:
            # Screen portfolio
            screening_result = await self.esg_analyzer.screen_portfolio_values(
                [{"investment_id": p["investment_id"], "value": p["current_value"]} for p in positions],
                values_profile
            )
            
            # Process exclusions
            for exclusion in screening_result["exclusions"]:
                if exclusion["action"] == "Divest":
                    # Find and remove the position
                    for position in positions:
                        if self.esg_analyzer.esg_investments[position["investment_id"]]["name"] == exclusion["investment"]:
                            await self.trigger_esg_divestment(position["investment_id"])
                            break
                            
    def add_esg_position(self, user_id: str, investment_id: str, units: float, price: float):
        """Add an ESG position"""
        if user_id not in self.esg_positions:
            self.esg_positions[user_id] = []
            
        self.esg_positions[user_id].append({
            "investment_id": investment_id,
            "units": units,
            "purchase_price": price,
            "purchase_date": datetime.now(),
            "current_value": units * price
        })
        
    def get_user_esg_positions(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all ESG positions for a user"""
        positions = self.esg_positions.get(user_id, [])
        
        # Enrich with current data
        enriched_positions = []
        for pos in positions:
            investment_data = self.esg_analyzer.esg_investments.get(pos["investment_id"])
            performance = self.esg_analyzer.investment_performance.get(pos["investment_id"])
            
            if investment_data and performance:
                current_value = pos["units"] * performance["current_price"]
                purchase_value = pos["units"] * pos["purchase_price"]
                
                enriched_positions.append({
                    **pos,
                    "investment_name": investment_data["name"],
                    "investment_type": investment_data["type"],
                    "category": investment_data["category"],
                    "esg_score": investment_data["esg_score"],
                    "current_price": performance["current_price"],
                    "current_value": current_value,
                    "purchase_value": purchase_value,
                    "pnl": current_value - purchase_value,
                    "pnl_percent": ((current_value / purchase_value) - 1) * 100,
                    "daily_change": performance["daily_change_percent"],
                    "impact_score": performance["impact_score"],
                    "controversy_alert": performance.get("controversy_alert", False)
                })
                
        return enriched_positions
        
    async def analyze_esg_investment(self, investment_id: str) -> Dict[str, Any]:
        """Get multi-agent analysis for a specific ESG investment"""
        return await self.esg_analyzer.analyze_esg_investment_multi_agent(investment_id)
        
    def get_esg_trades_history(self, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get ESG trading history"""
        if user_id:
            return [t for t in self.esg_trades if t.get("user_id") == user_id]
        return self.esg_trades
        
    def set_values_profile(self, user_id: str, profile: str):
        """Set user's values alignment profile"""
        self.values_profiles[user_id] = profile
        
    def get_controversy_alerts(self, investment_id: Optional[str] = None) -> Dict[str, Any]:
        """Get active controversy alerts"""
        if investment_id:
            return self.controversy_alerts.get(investment_id, [])
        return self.controversy_alerts
        
    async def calculate_portfolio_impact(self, user_id: str) -> Dict[str, Any]:
        """Calculate portfolio-wide ESG impact"""
        positions = self.get_user_esg_positions(user_id)
        
        if not positions:
            return {"impact_score": 0, "total_impacts": {}}
            
        return await self.esg_analyzer.calculate_portfolio_impact(
            [{"investment_id": p["investment_id"], "value": p["current_value"]} for p in positions]
        )
        
    def enable_esg_management(self, user_id: str, values_profile: str = "balanced_esg"):
        """Enable ESG investment management for a user"""
        if user_id in self.enabled_users:
            self.enabled_users[user_id]["esg_enabled"] = True
            
        self.values_profiles[user_id] = values_profile
        
    def get_esg_themes(self) -> Dict[str, Any]:
        """Get available ESG themes and investments"""
        return self.esg_analyzer.esg_themes
        
    def search_esg_investments(self, criteria: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Search for ESG investments based on criteria"""
        results = []
        
        min_esg_score = criteria.get("min_esg_score", 0)
        max_carbon = criteria.get("max_carbon_intensity", float('inf'))
        category = criteria.get("category")
        exclude_controversies = criteria.get("exclude_controversies", True)
        
        for inv_id, investment in self.esg_analyzer.esg_investments.items():
            # Apply filters
            if investment["esg_score"] < min_esg_score:
                continue
            if investment["carbon_intensity"] > max_carbon:
                continue
            if category and investment["category"] != category:
                continue
            if exclude_controversies and investment["controversy_score"] > 2:
                continue
                
            # Add performance data
            performance = self.esg_analyzer.investment_performance.get(inv_id, {})
            
            results.append({
                "investment_id": inv_id,
                **investment,
                "current_price": performance.get("current_price", investment["price"]),
                "daily_change": performance.get("daily_change_percent", 0),
                "impact_score": performance.get("impact_score", 0)
            })
            
        # Sort by ESG score
        results.sort(key=lambda x: x["esg_score"], reverse=True)
        
        return results 