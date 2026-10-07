"""
Mutual Fund & ETF Analyzer
Analyzes funds for performance, switches to better options, and implements tax-loss harvesting
"""

import random
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import logging

class FundAnalyzer:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Sample mutual funds and ETFs
        self.funds = {
            # Large Cap Equity Funds
            "HDFC_TOP_100": {
                "name": "HDFC Top 100 Fund",
                "type": "Mutual Fund",
                "category": "Large Cap Equity",
                "expense_ratio": 1.92,
                "aum": 18500,  # in crores
                "nav": 656.45,
                "returns": {"1Y": 28.5, "3Y": 15.2, "5Y": 13.8},
                "risk_rating": "Moderately High",
                "holdings": ["RELIANCE", "TCS", "HDFC", "INFY"],
                "sharpe_ratio": 1.85,
                "beta": 0.95,
                "alpha": 2.1
            },
            "AXIS_BLUECHIP": {
                "name": "Axis Bluechip Fund",
                "type": "Mutual Fund",
                "category": "Large Cap Equity",
                "expense_ratio": 1.88,
                "aum": 32400,
                "nav": 48.25,
                "returns": {"1Y": 25.3, "3Y": 14.8, "5Y": 12.9},
                "risk_rating": "Moderately High",
                "holdings": ["HDFC", "ICICI", "KOTAK", "BHARTIARTL"],
                "sharpe_ratio": 1.72,
                "beta": 0.92,
                "alpha": 1.8
            },
            
            # Mid Cap Funds
            "KOTAK_EMERGING": {
                "name": "Kotak Emerging Equity",
                "type": "Mutual Fund",
                "category": "Mid Cap Equity",
                "expense_ratio": 2.05,
                "aum": 12300,
                "nav": 89.34,
                "returns": {"1Y": 35.2, "3Y": 18.5, "5Y": 16.2},
                "risk_rating": "High",
                "holdings": ["PAGEIND", "ASTRAL", "CROMPTON", "VOLTAS"],
                "sharpe_ratio": 1.95,
                "beta": 1.15,
                "alpha": 3.5
            },
            
            # Debt Funds
            "ICICI_LIQUID": {
                "name": "ICICI Prudential Liquid Fund",
                "type": "Mutual Fund",
                "category": "Liquid Fund",
                "expense_ratio": 0.25,
                "aum": 45600,
                "nav": 305.67,
                "returns": {"1Y": 6.8, "3Y": 6.2, "5Y": 6.5},
                "risk_rating": "Low",
                "holdings": ["T-Bills", "Commercial Papers", "CDs"],
                "sharpe_ratio": 0.85,
                "beta": 0.02,
                "alpha": 0.3
            },
            
            # ETFs
            "NIFTY_BEES": {
                "name": "Nippon India ETF Nifty BeES",
                "type": "ETF",
                "category": "Index ETF",
                "expense_ratio": 0.05,
                "aum": 8900,
                "nav": 245.32,
                "returns": {"1Y": 24.5, "3Y": 13.2, "5Y": 11.8},
                "risk_rating": "Moderately High",
                "holdings": ["NIFTY 50 Stocks"],
                "sharpe_ratio": 1.65,
                "beta": 1.0,
                "alpha": 0
            },
            "GOLDBEES": {
                "name": "Nippon India ETF Gold BeES",
                "type": "ETF",
                "category": "Gold ETF",
                "expense_ratio": 0.5,
                "aum": 3200,
                "nav": 52.45,
                "returns": {"1Y": 12.3, "3Y": 9.8, "5Y": 8.5},
                "risk_rating": "Moderate",
                "holdings": ["Physical Gold"],
                "sharpe_ratio": 0.95,
                "beta": 0.3,
                "alpha": 0
            },
            
            # International Funds
            "MOTILAL_NASDAQ": {
                "name": "Motilal Oswal Nasdaq 100",
                "type": "ETF",
                "category": "International ETF",
                "expense_ratio": 0.58,
                "aum": 5600,
                "nav": 25.67,
                "returns": {"1Y": 32.5, "3Y": 19.2, "5Y": 17.8},
                "risk_rating": "High",
                "holdings": ["AAPL", "MSFT", "GOOGL", "AMZN"],
                "sharpe_ratio": 1.82,
                "beta": 1.2,
                "alpha": 1.5
            }
        }
        
        # Performance tracking
        self.fund_performance = {}
        self.tax_lots = {}  # Track purchase lots for tax optimization
        self.switch_history = []
        
        # Initialize current performance
        self._initialize_performance()
        
    def _initialize_performance(self):
        """Initialize fund performance tracking"""
        for fund_id, fund_data in self.funds.items():
            self.fund_performance[fund_id] = {
                "current_nav": fund_data["nav"],
                "day_change": 0,
                "month_change": 0,
                "year_change": fund_data["returns"]["1Y"],
                "volatility": self._calculate_volatility(fund_data["category"]),
                "tracking_error": random.uniform(0.1, 0.5) if fund_data["type"] == "ETF" else 0,
                "alpha_trend": "stable",
                "relative_performance": 0,
                "risk_adjusted_return": fund_data["sharpe_ratio"]
            }
            
    def _calculate_volatility(self, category: str) -> float:
        """Calculate volatility based on fund category"""
        volatility_map = {
            "Large Cap Equity": random.uniform(12, 18),
            "Mid Cap Equity": random.uniform(18, 25),
            "Small Cap Equity": random.uniform(22, 30),
            "Liquid Fund": random.uniform(0.1, 0.5),
            "Index ETF": random.uniform(10, 16),
            "Gold ETF": random.uniform(8, 15),
            "International ETF": random.uniform(15, 22)
        }
        return volatility_map.get(category, 15)
        
    async def analyze_fund_multi_agent(self, fund_id: str) -> Dict[str, Any]:
        """Multi-agent analysis of a fund"""
        fund = self.funds.get(fund_id)
        if not fund:
            return None
            
        performance = self.fund_performance[fund_id]
        
        # Performance Agent Analysis
        perf_analysis = await self._performance_agent_analysis(fund, performance)
        
        # Risk Agent Analysis
        risk_analysis = await self._risk_agent_analysis(fund, performance)
        
        # Tax Agent Analysis
        tax_analysis = await self._tax_agent_analysis(fund_id)
        
        # Category Agent Analysis
        category_analysis = await self._category_agent_analysis(fund)
        
        # Build consensus
        consensus = await self._build_fund_consensus(
            perf_analysis, risk_analysis, tax_analysis, category_analysis
        )
        
        return {
            "fund_id": fund_id,
            "fund_name": fund["name"],
            "current_nav": performance["current_nav"],
            "agents": {
                "performance": perf_analysis,
                "risk": risk_analysis,
                "tax": tax_analysis,
                "category": category_analysis
            },
            "consensus": consensus,
            "timestamp": datetime.now().isoformat()
        }
        
    async def _performance_agent_analysis(self, fund: Dict, performance: Dict) -> Dict[str, Any]:
        """Analyze fund performance metrics"""
        # Compare to category average
        category_avg_return = self._get_category_average(fund["category"])
        outperformance = fund["returns"]["1Y"] - category_avg_return
        
        # Trend analysis
        performance_trend = "improving" if performance["alpha_trend"] == "improving" else "stable"
        if fund["returns"]["1Y"] < fund["returns"]["3Y"]:
            performance_trend = "declining"
            
        return {
            "returns": {
                "1Y": f"{fund['returns']['1Y']}%",
                "3Y": f"{fund['returns']['3Y']}%",
                "5Y": f"{fund['returns']['5Y']}%"
            },
            "sharpe_ratio": fund["sharpe_ratio"],
            "alpha": fund["alpha"],
            "beta": fund["beta"],
            "vs_category": f"{'+' if outperformance > 0 else ''}{outperformance:.1f}%",
            "performance_trend": performance_trend,
            "consistency_score": random.uniform(7, 10) if fund["sharpe_ratio"] > 1.5 else random.uniform(4, 7),
            "recommendation": "Hold" if outperformance > 0 else "Consider Switch"
        }
        
    async def _risk_agent_analysis(self, fund: Dict, performance: Dict) -> Dict[str, Any]:
        """Analyze fund risk metrics"""
        return {
            "risk_rating": fund["risk_rating"],
            "volatility": f"{performance['volatility']:.1f}%",
            "max_drawdown": f"{random.uniform(5, 20):.1f}%",
            "downside_deviation": f"{performance['volatility'] * 0.7:.1f}%",
            "risk_adjusted_return": performance["risk_adjusted_return"],
            "correlation_with_market": fund["beta"],
            "diversification_score": random.uniform(7, 10) if fund["type"] == "Mutual Fund" else 10,
            "risk_assessment": "Acceptable" if fund["sharpe_ratio"] > 1.2 else "Monitor Closely"
        }
        
    async def _tax_agent_analysis(self, fund_id: str) -> Dict[str, Any]:
        """Analyze tax implications"""
        tax_lots = self.tax_lots.get(fund_id, [])
        
        # Calculate unrealized gains/losses
        current_nav = self.fund_performance[fund_id]["current_nav"]
        total_units = sum(lot["units"] for lot in tax_lots)
        total_cost = sum(lot["units"] * lot["purchase_nav"] for lot in tax_lots)
        current_value = total_units * current_nav if total_units > 0 else 0
        unrealized_gain = current_value - total_cost if total_units > 0 else 0
        
        # Identify tax-loss harvesting opportunities
        harvest_opportunity = unrealized_gain < -1000  # Loss > ₹1000
        
        # Long-term vs short-term
        ltcg_eligible = any(
            (datetime.now() - lot["purchase_date"]).days > 365 
            for lot in tax_lots
        ) if tax_lots else False
        
        return {
            "unrealized_gain": f"₹{unrealized_gain:,.2f}",
            "tax_status": "LTCG Eligible" if ltcg_eligible else "STCG",
            "harvest_opportunity": harvest_opportunity,
            "harvest_amount": f"₹{abs(unrealized_gain):,.2f}" if harvest_opportunity else "N/A",
            "tax_efficiency_score": random.uniform(7, 10) if fund_id.endswith("BEES") else random.uniform(5, 8),
            "indexation_benefit": "Available" if fund["type"] == "Mutual Fund" else "Not Available",
            "recommendation": "Harvest Loss" if harvest_opportunity else "Hold for LTCG" if not ltcg_eligible else "Tax Efficient"
        }
        
    async def _category_agent_analysis(self, fund: Dict) -> Dict[str, Any]:
        """Analyze fund within its category"""
        category_rank = random.randint(1, 20)
        category_size = random.randint(50, 200)
        
        return {
            "category": fund["category"],
            "category_rank": f"{category_rank}/{category_size}",
            "expense_ratio": f"{fund['expense_ratio']}%",
            "expense_vs_category": "Below Average" if fund["expense_ratio"] < 1.5 else "Above Average",
            "aum": f"₹{fund['aum']:,} Cr",
            "fund_size_assessment": "Large" if fund["aum"] > 10000 else "Medium" if fund["aum"] > 1000 else "Small",
            "fund_manager_tenure": f"{random.randint(2, 10)} years",
            "style_consistency": "High" if random.random() > 0.3 else "Moderate"
        }
        
    async def _build_fund_consensus(self, perf: Dict, risk: Dict, tax: Dict, category: Dict) -> Dict[str, Any]:
        """Build multi-agent consensus for fund action"""
        scores = []
        
        # Performance score
        perf_score = 0.8 if "improving" in perf["performance_trend"] else 0.6
        if float(perf["vs_category"].replace("%", "").replace("+", "")) > 2:
            perf_score += 0.2
        scores.append(perf_score)
        
        # Risk score
        risk_score = 0.8 if risk["risk_adjusted_return"] > 1.5 else 0.6
        if "Acceptable" in risk["risk_assessment"]:
            risk_score += 0.1
        scores.append(risk_score)
        
        # Tax score
        tax_score = 0.9 if tax["harvest_opportunity"] else 0.7
        if "LTCG" in tax["tax_status"]:
            tax_score += 0.1
        scores.append(tax_score)
        
        # Category score
        cat_rank = int(category["category_rank"].split("/")[0])
        cat_score = 0.9 if cat_rank <= 5 else 0.7 if cat_rank <= 10 else 0.5
        scores.append(cat_score)
        
        consensus_score = sum(scores) / len(scores)
        
        # Determine action
        if tax["harvest_opportunity"]:
            action = "TAX_HARVEST"
            recommendation = f"Harvest tax loss of {tax['harvest_amount']} and switch to better performer"
        elif consensus_score < 0.6:
            action = "SWITCH"
            recommendation = "Fund underperforming - switch to category leader"
        elif consensus_score > 0.8:
            action = "ACCUMULATE"
            recommendation = "Strong performer - consider increasing allocation"
        else:
            action = "HOLD"
            recommendation = "Continue holding - performance satisfactory"
            
        return {
            "action": action,
            "confidence": f"{consensus_score * 100:.0f}%",
            "recommendation": recommendation,
            "switch_candidates": await self._find_switch_candidates(perf["category"]) if action in ["SWITCH", "TAX_HARVEST"] else [],
            "rebalance_suggestion": f"Target allocation: {self._calculate_target_allocation(consensus_score)}%"
        }
        
    async def _find_switch_candidates(self, category: str) -> List[Dict[str, Any]]:
        """Find better performing funds in the same category"""
        candidates = []
        
        for fund_id, fund in self.funds.items():
            if fund["category"] == category:
                candidates.append({
                    "fund_id": fund_id,
                    "name": fund["name"],
                    "returns_1y": fund["returns"]["1Y"],
                    "sharpe_ratio": fund["sharpe_ratio"],
                    "expense_ratio": fund["expense_ratio"]
                })
                
        # Sort by Sharpe ratio
        candidates.sort(key=lambda x: x["sharpe_ratio"], reverse=True)
        return candidates[:3]  # Top 3 candidates
        
    def _get_category_average(self, category: str) -> float:
        """Get average returns for a category"""
        category_funds = [
            fund for fund in self.funds.values() 
            if fund["category"] == category
        ]
        if not category_funds:
            return 15.0
            
        avg_return = sum(f["returns"]["1Y"] for f in category_funds) / len(category_funds)
        return avg_return
        
    def _calculate_target_allocation(self, score: float) -> int:
        """Calculate target allocation based on score"""
        if score > 0.8:
            return random.randint(15, 25)
        elif score > 0.7:
            return random.randint(10, 15)
        elif score > 0.6:
            return random.randint(5, 10)
        else:
            return random.randint(0, 5)
            
    async def execute_switch(self, from_fund: str, to_fund: str, units: float, reason: str) -> Dict[str, Any]:
        """Execute fund switch"""
        # Record switch
        switch_record = {
            "switch_id": f"SW-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "from_fund": from_fund,
            "to_fund": to_fund,
            "units_switched": units,
            "from_nav": self.fund_performance[from_fund]["current_nav"],
            "to_nav": self.fund_performance[to_fund]["current_nav"],
            "reason": reason,
            "timestamp": datetime.now(),
            "tax_impact": "Loss harvested" if reason == "tax_harvest" else "STCG applicable"
        }
        
        self.switch_history.append(switch_record)
        
        return {
            "status": "executed",
            "switch_details": switch_record,
            "message": f"Successfully switched from {self.funds[from_fund]['name']} to {self.funds[to_fund]['name']}"
        }
        
    async def monitor_all_funds(self) -> List[Dict[str, Any]]:
        """Monitor all funds for opportunities"""
        opportunities = []
        
        for fund_id in self.funds:
            analysis = await self.analyze_fund_multi_agent(fund_id)
            
            if analysis["consensus"]["action"] in ["SWITCH", "TAX_HARVEST"]:
                opportunities.append({
                    "fund_id": fund_id,
                    "fund_name": analysis["fund_name"],
                    "action": analysis["consensus"]["action"],
                    "reason": analysis["consensus"]["recommendation"],
                    "candidates": analysis["consensus"]["switch_candidates"]
                })
                
        return opportunities
        
    def update_fund_performance(self):
        """Update fund NAVs and performance metrics"""
        for fund_id, performance in self.fund_performance.items():
            # Simulate daily NAV change
            fund = self.funds[fund_id]
            volatility = performance["volatility"] / 100 / 252 ** 0.5  # Daily volatility
            
            daily_return = random.gauss(0.0003, volatility)  # Small positive drift
            performance["current_nav"] *= (1 + daily_return)
            performance["day_change"] = daily_return * 100
            
            # Update relative performance
            category_avg = self._get_category_average(fund["category"])
            performance["relative_performance"] = fund["returns"]["1Y"] - category_avg
            
    def add_tax_lot(self, fund_id: str, units: float, nav: float):
        """Add a tax lot for tracking"""
        if fund_id not in self.tax_lots:
            self.tax_lots[fund_id] = []
            
        self.tax_lots[fund_id].append({
            "units": units,
            "purchase_nav": nav,
            "purchase_date": datetime.now(),
            "lot_id": f"LOT-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        }) 