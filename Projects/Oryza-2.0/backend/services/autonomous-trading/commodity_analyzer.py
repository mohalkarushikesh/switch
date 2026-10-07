"""
Commodity Analyzer
Monitors gold & metals, tracks macro indicators, hedges during uncertainty, rebalances on inflation
"""

import random
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import logging
import math

class CommodityAnalyzer:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Commodity universe
        self.commodities = {
            # Precious Metals
            "GOLD": {
                "name": "Gold (per oz)",
                "symbol": "GOLD",
                "type": "Precious Metal",
                "price": 1950.50,
                "currency": "USD",
                "unit": "oz",
                "correlation_to_inflation": 0.75,
                "safe_haven_score": 0.95,
                "volatility": 0.15,
                "liquidity": "Very High",
                "etf_available": True,
                "futures_available": True,
                "storage_cost": 0.002  # 0.2% annually
            },
            "SILVER": {
                "name": "Silver (per oz)",
                "symbol": "SILVER",
                "type": "Precious Metal",
                "price": 23.45,
                "currency": "USD",
                "unit": "oz",
                "correlation_to_inflation": 0.65,
                "safe_haven_score": 0.70,
                "volatility": 0.25,
                "liquidity": "High",
                "etf_available": True,
                "futures_available": True,
                "storage_cost": 0.003
            },
            "PLATINUM": {
                "name": "Platinum (per oz)",
                "symbol": "PLATINUM",
                "type": "Precious Metal",
                "price": 985.30,
                "currency": "USD",
                "unit": "oz",
                "correlation_to_inflation": 0.55,
                "safe_haven_score": 0.60,
                "volatility": 0.30,
                "liquidity": "Medium",
                "etf_available": True,
                "futures_available": True,
                "storage_cost": 0.0025
            },
            "PALLADIUM": {
                "name": "Palladium (per oz)",
                "symbol": "PALLADIUM",
                "type": "Precious Metal",
                "price": 1025.75,
                "currency": "USD",
                "unit": "oz",
                "correlation_to_inflation": 0.45,
                "safe_haven_score": 0.50,
                "volatility": 0.35,
                "liquidity": "Medium",
                "etf_available": True,
                "futures_available": True,
                "storage_cost": 0.0025
            },
            
            # Industrial Metals
            "COPPER": {
                "name": "Copper (per lb)",
                "symbol": "COPPER",
                "type": "Industrial Metal",
                "price": 3.85,
                "currency": "USD",
                "unit": "lb",
                "correlation_to_inflation": 0.60,
                "safe_haven_score": 0.20,
                "volatility": 0.20,
                "liquidity": "High",
                "etf_available": True,
                "futures_available": True,
                "economic_indicator": True
            },
            "ALUMINUM": {
                "name": "Aluminum (per tonne)",
                "symbol": "ALUMINUM",
                "type": "Industrial Metal",
                "price": 2265.00,
                "currency": "USD",
                "unit": "tonne",
                "correlation_to_inflation": 0.50,
                "safe_haven_score": 0.15,
                "volatility": 0.18,
                "liquidity": "High",
                "etf_available": True,
                "futures_available": True,
                "economic_indicator": True
            },
            
            # Commodity ETFs
            "GOLDBEES": {
                "name": "Nippon India Gold ETF",
                "symbol": "GOLDBEES",
                "type": "Gold ETF",
                "price": 4850.50,
                "currency": "INR",
                "unit": "unit",
                "correlation_to_inflation": 0.73,
                "safe_haven_score": 0.90,
                "volatility": 0.14,
                "liquidity": "Very High",
                "etf_available": True,
                "futures_available": False,
                "expense_ratio": 0.0079
            },
            "GOLDM": {
                "name": "SBI Gold ETF",
                "symbol": "GOLDM",
                "type": "Gold ETF",
                "price": 4820.00,
                "currency": "INR",
                "unit": "unit",
                "correlation_to_inflation": 0.73,
                "safe_haven_score": 0.90,
                "volatility": 0.14,
                "liquidity": "High",
                "etf_available": True,
                "futures_available": False,
                "expense_ratio": 0.0065
            }
        }
        
        # Global macro indicators
        self.macro_indicators = {
            "US_CPI": {
                "name": "US Consumer Price Index",
                "value": 3.7,
                "trend": "rising",
                "impact_on_gold": "positive"
            },
            "US_DOLLAR_INDEX": {
                "name": "US Dollar Index (DXY)",
                "value": 103.5,
                "trend": "stable",
                "impact_on_gold": "negative"
            },
            "REAL_RATES": {
                "name": "US Real Interest Rates",
                "value": 1.8,
                "trend": "rising",
                "impact_on_gold": "negative"
            },
            "VIX": {
                "name": "Volatility Index",
                "value": 18.5,
                "trend": "falling",
                "impact_on_gold": "neutral"
            },
            "GEOPOLITICAL_RISK": {
                "name": "Geopolitical Risk Index",
                "value": 65,  # 0-100 scale
                "trend": "rising",
                "impact_on_gold": "positive"
            },
            "GLOBAL_GROWTH": {
                "name": "Global GDP Growth",
                "value": 3.2,
                "trend": "stable",
                "impact_on_gold": "neutral"
            },
            "CENTRAL_BANK_BUYING": {
                "name": "Central Bank Gold Purchases",
                "value": 850,  # tonnes annually
                "trend": "rising",
                "impact_on_gold": "positive"
            },
            "INFLATION_EXPECTATIONS": {
                "name": "10Y Inflation Expectations",
                "value": 2.8,
                "trend": "rising",
                "impact_on_gold": "positive"
            }
        }
        
        # Market uncertainty metrics
        self.uncertainty_metrics = {
            "market_stress": 0.3,  # 0-1 scale
            "currency_volatility": 0.25,
            "bond_equity_correlation": -0.4,
            "credit_spreads": "normal",
            "liquidity_conditions": "normal",
            "fear_greed_index": 55  # 0-100
        }
        
        # Performance tracking
        self.commodity_performance = {}
        self._initialize_performance()
        
        # Hedging parameters
        self.hedging_rules = {
            "uncertainty_threshold": 0.6,  # When to increase allocation
            "inflation_threshold": 3.0,    # When to rebalance
            "max_allocation": 0.20,        # Maximum 20% portfolio
            "min_allocation": 0.05,        # Minimum 5% portfolio
            "rebalance_frequency": 30      # Days
        }
        
        # Technical indicators
        self.technical_indicators = {}
        self._initialize_technicals()
        
    def _initialize_performance(self):
        """Initialize commodity performance tracking"""
        for commodity_id, commodity_data in self.commodities.items():
            self.commodity_performance[commodity_id] = {
                "current_price": commodity_data["price"],
                "daily_change": 0,
                "daily_change_percent": 0,
                "weekly_return": random.uniform(-3, 5),
                "monthly_return": random.uniform(-5, 8),
                "ytd_return": random.uniform(-10, 25),
                "52w_high": commodity_data["price"] * 1.15,
                "52w_low": commodity_data["price"] * 0.85,
                "volume": random.randint(100000, 1000000),
                "moving_avg_50": commodity_data["price"] * random.uniform(0.95, 1.05),
                "moving_avg_200": commodity_data["price"] * random.uniform(0.90, 1.10),
                "rsi": random.uniform(30, 70),
                "momentum": random.uniform(-10, 10)
            }
            
    def _initialize_technicals(self):
        """Initialize technical indicators"""
        for commodity_id in self.commodities:
            self.technical_indicators[commodity_id] = {
                "support_levels": [],
                "resistance_levels": [],
                "trend": "neutral",
                "pattern": None,
                "breakout_potential": False
            }
            
    async def analyze_commodity_multi_agent(self, commodity_id: str) -> Dict[str, Any]:
        """Multi-agent analysis of a commodity"""
        commodity = self.commodities.get(commodity_id)
        if not commodity:
            return None
            
        performance = self.commodity_performance[commodity_id]
        
        # Commodity Agent Analysis
        commodity_analysis = await self._commodity_agent_analysis(commodity, performance)
        
        # Macro Agent Analysis
        macro_analysis = await self._macro_agent_analysis(commodity, performance)
        
        # Hedge Agent Analysis
        hedge_analysis = await self._hedge_agent_analysis(commodity, performance)
        
        # Inflation Agent Analysis
        inflation_analysis = await self._inflation_agent_analysis(commodity, performance)
        
        # Build consensus
        consensus = await self._build_commodity_consensus(
            commodity_analysis, macro_analysis, hedge_analysis, inflation_analysis
        )
        
        return {
            "commodity_id": commodity_id,
            "commodity_name": commodity["name"],
            "current_price": performance["current_price"],
            "daily_change": performance["daily_change_percent"],
            "agents": {
                "commodity": commodity_analysis,
                "macro": macro_analysis,
                "hedge": hedge_analysis,
                "inflation": inflation_analysis
            },
            "consensus": consensus,
            "timestamp": datetime.now().isoformat()
        }
        
    async def _commodity_agent_analysis(self, commodity: Dict, performance: Dict) -> Dict[str, Any]:
        """Analyze commodity fundamentals and technicals"""
        # Technical analysis
        trend = self._determine_trend(performance)
        momentum_signal = "Buy" if performance["rsi"] < 40 else \
                         "Sell" if performance["rsi"] > 60 else "Neutral"
        
        # Supply/demand analysis
        supply_demand = self._analyze_supply_demand(commodity["symbol"])
        
        # Seasonality
        seasonal_factor = self._get_seasonal_factor(commodity["symbol"])
        
        return {
            "price_trend": trend,
            "momentum_signal": momentum_signal,
            "rsi": f"{performance['rsi']:.1f}",
            "vs_50ma": f"{((performance['current_price'] / performance['moving_avg_50']) - 1) * 100:.1f}%",
            "vs_200ma": f"{((performance['current_price'] / performance['moving_avg_200']) - 1) * 100:.1f}%",
            "supply_demand": supply_demand,
            "seasonal_factor": seasonal_factor,
            "liquidity": commodity["liquidity"],
            "volatility": f"{commodity['volatility'] * 100:.1f}%",
            "technical_rating": self._get_technical_rating(performance)
        }
        
    async def _macro_agent_analysis(self, commodity: Dict, performance: Dict) -> Dict[str, Any]:
        """Analyze global macro impact on commodity"""
        # Calculate macro score
        macro_score = self._calculate_macro_score(commodity["symbol"])
        
        # Key drivers
        key_drivers = self._identify_key_drivers(commodity["symbol"])
        
        # Currency impact
        currency_impact = "Negative" if self.macro_indicators["US_DOLLAR_INDEX"]["trend"] == "rising" else \
                         "Positive" if self.macro_indicators["US_DOLLAR_INDEX"]["trend"] == "falling" else "Neutral"
        
        return {
            "macro_score": f"{macro_score:.1f}/10",
            "dollar_impact": currency_impact,
            "real_rates_impact": self.macro_indicators["REAL_RATES"]["impact_on_gold"],
            "geopolitical_risk": f"{self.macro_indicators['GEOPOLITICAL_RISK']['value']}/100",
            "central_bank_demand": self.macro_indicators["CENTRAL_BANK_BUYING"]["trend"],
            "key_drivers": key_drivers,
            "global_growth": f"{self.macro_indicators['GLOBAL_GROWTH']['value']}%",
            "recommendation": self._get_macro_recommendation(macro_score),
            "risk_factors": self._identify_macro_risks()
        }
        
    async def _hedge_agent_analysis(self, commodity: Dict, performance: Dict) -> Dict[str, Any]:
        """Analyze hedging effectiveness"""
        # Calculate hedge effectiveness
        hedge_score = commodity["safe_haven_score"]
        
        # Portfolio protection metrics
        protection_value = self._calculate_protection_value(commodity, self.uncertainty_metrics["market_stress"])
        
        # Optimal hedge ratio
        optimal_ratio = self._calculate_optimal_hedge_ratio(
            commodity["volatility"],
            self.uncertainty_metrics["market_stress"]
        )
        
        # Crisis performance
        crisis_beta = -0.3 if commodity["safe_haven_score"] > 0.8 else 0.1
        
        return {
            "safe_haven_score": f"{hedge_score:.2f}",
            "market_stress_level": f"{self.uncertainty_metrics['market_stress']:.2f}",
            "protection_value": f"{protection_value:.1f}%",
            "optimal_hedge_ratio": f"{optimal_ratio:.1f}%",
            "crisis_beta": f"{crisis_beta:.2f}",
            "vix_level": f"{self.macro_indicators['VIX']['value']:.1f}",
            "correlation_to_equities": f"{self._get_equity_correlation(commodity['symbol']):.2f}",
            "hedge_effectiveness": self._rate_hedge_effectiveness(hedge_score, self.uncertainty_metrics["market_stress"]),
            "action": "Increase" if self.uncertainty_metrics["market_stress"] > self.hedging_rules["uncertainty_threshold"] else "Maintain"
        }
        
    async def _inflation_agent_analysis(self, commodity: Dict, performance: Dict) -> Dict[str, Any]:
        """Analyze inflation protection and rebalancing needs"""
        # Inflation metrics
        current_inflation = self.macro_indicators["US_CPI"]["value"]
        inflation_expectations = self.macro_indicators["INFLATION_EXPECTATIONS"]["value"]
        
        # Real return calculation
        nominal_return = performance["ytd_return"]
        real_return = nominal_return - current_inflation
        
        # Rebalancing signal
        rebalance_signal = self._get_rebalance_signal(
            current_inflation,
            inflation_expectations,
            commodity["correlation_to_inflation"]
        )
        
        return {
            "current_inflation": f"{current_inflation}%",
            "inflation_expectations": f"{inflation_expectations}%",
            "inflation_trend": self.macro_indicators["US_CPI"]["trend"],
            "correlation_to_inflation": f"{commodity['correlation_to_inflation']:.2f}",
            "nominal_return_ytd": f"{nominal_return:.1f}%",
            "real_return_ytd": f"{real_return:.1f}%",
            "inflation_protection": self._rate_inflation_protection(commodity["correlation_to_inflation"]),
            "rebalance_signal": rebalance_signal,
            "target_allocation": f"{self._calculate_target_allocation(current_inflation, commodity['symbol']):.1f}%"
        }
        
    async def _build_commodity_consensus(self, commodity: Dict, macro: Dict, hedge: Dict, inflation: Dict) -> Dict[str, Any]:
        """Build multi-agent consensus for commodity action"""
        scores = []
        
        # Commodity score (technical/fundamental)
        commodity_score = 0.8 if commodity["technical_rating"] == "Strong Buy" else \
                         0.6 if commodity["technical_rating"] == "Buy" else \
                         0.4 if commodity["technical_rating"] == "Sell" else 0.5
        scores.append(commodity_score)
        
        # Macro score
        macro_score = float(macro["macro_score"].split("/")[0]) / 10
        scores.append(macro_score)
        
        # Hedge score (weighted by market stress)
        hedge_effectiveness = 0.9 if hedge["hedge_effectiveness"] == "Excellent" else \
                            0.7 if hedge["hedge_effectiveness"] == "Good" else \
                            0.5 if hedge["hedge_effectiveness"] == "Moderate" else 0.3
        hedge_weight = 1 + self.uncertainty_metrics["market_stress"]
        scores.append(hedge_effectiveness * hedge_weight)
        
        # Inflation score
        inflation_score = 0.8 if inflation["rebalance_signal"] == "Increase" else \
                         0.6 if inflation["rebalance_signal"] == "Hold" else 0.4
        scores.append(inflation_score)
        
        # Weighted consensus
        weights = [1, 1.2, hedge_weight, 1.1]
        weighted_score = sum(s * w for s, w in zip(scores, weights)) / sum(weights)
        
        # Determine action
        if weighted_score > 0.7:
            action = "BUY"
            recommendation = "Strong allocation increase recommended"
        elif weighted_score > 0.55:
            action = "ACCUMULATE"
            recommendation = "Gradually increase position"
        elif weighted_score > 0.45:
            action = "HOLD"
            recommendation = "Maintain current allocation"
        else:
            action = "REDUCE"
            recommendation = "Consider reducing exposure"
            
        # Special conditions
        if self.uncertainty_metrics["market_stress"] > 0.7:
            action = "BUY"
            recommendation = "Crisis hedge - increase allocation immediately"
        elif float(inflation["current_inflation"]) > 5:
            action = "ACCUMULATE"
            recommendation = "High inflation - increase commodity exposure"
            
        return {
            "action": action,
            "confidence": f"{weighted_score * 100:.0f}%",
            "recommendation": recommendation,
            "primary_driver": self._identify_primary_driver(commodity, macro, hedge, inflation),
            "allocation_target": inflation["target_allocation"],
            "risk_warnings": self._identify_commodity_risks(commodity, macro, hedge),
            "alternatives": self._suggest_alternatives(action)
        }
        
    def _determine_trend(self, performance: Dict) -> str:
        """Determine price trend"""
        if performance["current_price"] > performance["moving_avg_50"] > performance["moving_avg_200"]:
            return "Strong Uptrend"
        elif performance["current_price"] > performance["moving_avg_50"]:
            return "Uptrend"
        elif performance["current_price"] < performance["moving_avg_50"] < performance["moving_avg_200"]:
            return "Strong Downtrend"
        elif performance["current_price"] < performance["moving_avg_50"]:
            return "Downtrend"
        else:
            return "Sideways"
            
    def _analyze_supply_demand(self, symbol: str) -> str:
        """Analyze supply/demand dynamics"""
        if symbol == "GOLD":
            return "Tight supply, strong central bank demand"
        elif symbol == "SILVER":
            return "Industrial demand rising, investment demand moderate"
        elif symbol == "COPPER":
            return "Supply constraints, EV demand growing"
        else:
            return "Balanced supply/demand"
            
    def _get_seasonal_factor(self, symbol: str) -> str:
        """Get seasonal patterns"""
        month = datetime.now().month
        
        if symbol in ["GOLD", "SILVER"]:
            if month in [8, 9, 10, 11]:  # Indian wedding season
                return "Positive (wedding season)"
            elif month in [12, 1]:  # Chinese New Year
                return "Positive (festival demand)"
            else:
                return "Neutral"
        else:
            return "Neutral"
            
    def _get_technical_rating(self, performance: Dict) -> str:
        """Calculate technical rating"""
        score = 0
        
        # Trend
        if performance["current_price"] > performance["moving_avg_50"]:
            score += 1
        if performance["current_price"] > performance["moving_avg_200"]:
            score += 1
            
        # Momentum
        if performance["rsi"] < 70 and performance["rsi"] > 30:
            score += 1
        if performance["momentum"] > 0:
            score += 1
            
        if score >= 3:
            return "Strong Buy"
        elif score >= 2:
            return "Buy"
        elif score >= 1:
            return "Neutral"
        else:
            return "Sell"
            
    def _calculate_macro_score(self, symbol: str) -> float:
        """Calculate macro favorability score"""
        score = 5.0  # Base score
        
        # Dollar impact
        if self.macro_indicators["US_DOLLAR_INDEX"]["trend"] == "falling":
            score += 1.5
        elif self.macro_indicators["US_DOLLAR_INDEX"]["trend"] == "rising":
            score -= 1.5
            
        # Real rates impact
        if self.macro_indicators["REAL_RATES"]["value"] < 0:
            score += 2
        elif self.macro_indicators["REAL_RATES"]["value"] > 2:
            score -= 1
            
        # Inflation impact
        if self.macro_indicators["US_CPI"]["value"] > 3:
            score += 1
            
        # Geopolitical risk
        if self.macro_indicators["GEOPOLITICAL_RISK"]["value"] > 70:
            score += 1.5
            
        return max(0, min(10, score))
        
    def _identify_key_drivers(self, symbol: str) -> List[str]:
        """Identify key price drivers"""
        drivers = []
        
        if self.macro_indicators["US_DOLLAR_INDEX"]["trend"] == "falling":
            drivers.append("Weakening dollar")
        if self.macro_indicators["REAL_RATES"]["value"] < 1:
            drivers.append("Low real rates")
        if self.macro_indicators["GEOPOLITICAL_RISK"]["value"] > 60:
            drivers.append("Geopolitical tensions")
        if self.macro_indicators["CENTRAL_BANK_BUYING"]["trend"] == "rising":
            drivers.append("Central bank buying")
            
        return drivers[:3]  # Top 3 drivers
        
    def _get_macro_recommendation(self, score: float) -> str:
        """Get macro-based recommendation"""
        if score >= 7:
            return "Very favorable macro environment"
        elif score >= 5:
            return "Supportive macro conditions"
        elif score >= 3:
            return "Mixed macro signals"
        else:
            return "Challenging macro headwinds"
            
    def _identify_macro_risks(self) -> List[str]:
        """Identify macro risks"""
        risks = []
        
        if self.macro_indicators["REAL_RATES"]["value"] > 2:
            risks.append("Rising real rates")
        if self.macro_indicators["US_DOLLAR_INDEX"]["value"] > 105:
            risks.append("Strong dollar")
        if self.macro_indicators["GLOBAL_GROWTH"]["value"] < 2:
            risks.append("Slowing growth")
            
        return risks
        
    def _calculate_protection_value(self, commodity: Dict, market_stress: float) -> float:
        """Calculate portfolio protection value"""
        base_protection = commodity["safe_haven_score"] * 10
        stress_multiplier = 1 + (market_stress * 2)
        return base_protection * stress_multiplier
        
    def _calculate_optimal_hedge_ratio(self, volatility: float, market_stress: float) -> float:
        """Calculate optimal hedge ratio"""
        base_ratio = 5  # Base 5% allocation
        
        # Adjust for market stress
        stress_adjustment = market_stress * 10
        
        # Adjust for volatility (inverse relationship)
        volatility_adjustment = (1 - volatility) * 5
        
        optimal = base_ratio + stress_adjustment + volatility_adjustment
        
        # Apply bounds
        return max(self.hedging_rules["min_allocation"] * 100, 
                  min(self.hedging_rules["max_allocation"] * 100, optimal))
                  
    def _get_equity_correlation(self, symbol: str) -> float:
        """Get correlation to equity markets"""
        correlations = {
            "GOLD": -0.15,
            "SILVER": 0.10,
            "PLATINUM": 0.25,
            "PALLADIUM": 0.30,
            "COPPER": 0.60,
            "ALUMINUM": 0.55,
            "GOLDBEES": -0.12,
            "GOLDM": -0.12
        }
        return correlations.get(symbol, 0)
        
    def _rate_hedge_effectiveness(self, safe_haven_score: float, market_stress: float) -> str:
        """Rate hedging effectiveness"""
        effectiveness = safe_haven_score * (1 + market_stress)
        
        if effectiveness > 1.2:
            return "Excellent"
        elif effectiveness > 0.8:
            return "Good"
        elif effectiveness > 0.5:
            return "Moderate"
        else:
            return "Poor"
            
    def _get_rebalance_signal(self, inflation: float, expectations: float, correlation: float) -> str:
        """Generate rebalancing signal"""
        if inflation > self.hedging_rules["inflation_threshold"] and correlation > 0.6:
            return "Increase"
        elif inflation < 2 and correlation > 0.6:
            return "Decrease"
        else:
            return "Hold"
            
    def _rate_inflation_protection(self, correlation: float) -> str:
        """Rate inflation protection quality"""
        if correlation > 0.7:
            return "Excellent"
        elif correlation > 0.5:
            return "Good"
        elif correlation > 0.3:
            return "Moderate"
        else:
            return "Poor"
            
    def _calculate_target_allocation(self, inflation: float, symbol: str) -> float:
        """Calculate target allocation based on inflation"""
        base_allocation = 10  # 10% base
        
        # Inflation adjustment
        if inflation > 4:
            inflation_adj = 5
        elif inflation > 3:
            inflation_adj = 3
        elif inflation > 2:
            inflation_adj = 1
        else:
            inflation_adj = -2
            
        # Commodity-specific adjustment
        if symbol in ["GOLD", "GOLDBEES", "GOLDM"]:
            commodity_adj = 2
        else:
            commodity_adj = 0
            
        target = base_allocation + inflation_adj + commodity_adj
        
        # Apply bounds
        return max(self.hedging_rules["min_allocation"] * 100,
                  min(self.hedging_rules["max_allocation"] * 100, target))
                  
    def _identify_primary_driver(self, commodity: Dict, macro: Dict, hedge: Dict, inflation: Dict) -> str:
        """Identify primary investment driver"""
        drivers = []
        
        if float(hedge["market_stress_level"]) > 0.6:
            drivers.append(("Uncertainty hedge", 3))
        if float(inflation["current_inflation"]) > 3:
            drivers.append(("Inflation protection", 2.5))
        if float(macro["macro_score"].split("/")[0]) > 7:
            drivers.append(("Favorable macro", 2))
        if commodity["technical_rating"] in ["Strong Buy", "Buy"]:
            drivers.append(("Technical breakout", 1.5))
            
        if drivers:
            return max(drivers, key=lambda x: x[1])[0]
        return "Diversification"
        
    def _identify_commodity_risks(self, commodity: Dict, macro: Dict, hedge: Dict) -> List[str]:
        """Identify commodity-specific risks"""
        risks = []
        
        if commodity["volatility"] == "High":
            risks.append("High price volatility")
        if macro["dollar_impact"] == "Negative":
            risks.append("Strong dollar headwind")
        if float(hedge["market_stress_level"]) < 0.3:
            risks.append("Low crisis demand")
            
        return risks
        
    def _suggest_alternatives(self, action: str) -> List[Dict[str, str]]:
        """Suggest alternative commodities"""
        if action in ["REDUCE", "HOLD"]:
            return []
            
        alternatives = []
        for comm_id, comm_data in self.commodities.items():
            if comm_data["safe_haven_score"] > 0.7:
                alternatives.append({
                    "commodity": comm_data["name"],
                    "reason": f"Safe haven score: {comm_data['safe_haven_score']}"
                })
                
        return alternatives[:3]
        
    def update_prices(self):
        """Update commodity prices based on market conditions"""
        for commodity_id, performance in self.commodity_performance.items():
            commodity = self.commodities[commodity_id]
            
            # Base price movement
            volatility = commodity["volatility"]
            daily_move = random.gauss(0, volatility / math.sqrt(252))
            
            # Macro adjustments
            if self.macro_indicators["US_DOLLAR_INDEX"]["trend"] == "falling":
                daily_move += 0.001  # Positive for commodities
            if self.macro_indicators["GEOPOLITICAL_RISK"]["value"] > 70:
                if commodity["safe_haven_score"] > 0.7:
                    daily_move += 0.002  # Flight to safety
                    
            # Apply price change
            old_price = performance["current_price"]
            new_price = old_price * (1 + daily_move)
            
            performance["current_price"] = new_price
            performance["daily_change"] = new_price - old_price
            performance["daily_change_percent"] = daily_move * 100
            
            # Update moving averages
            performance["moving_avg_50"] = performance["moving_avg_50"] * 0.98 + new_price * 0.02
            performance["moving_avg_200"] = performance["moving_avg_200"] * 0.995 + new_price * 0.005
            
            # Update RSI
            performance["rsi"] = max(20, min(80, performance["rsi"] + random.uniform(-5, 5)))
            
            # Update momentum
            performance["momentum"] = daily_move * 100 * 10
            
    def update_macro_indicators(self):
        """Update macro indicators"""
        # Simulate macro changes
        for indicator_id, indicator in self.macro_indicators.items():
            if indicator_id == "VIX":
                # VIX mean reverts
                indicator["value"] = max(10, min(50, indicator["value"] + random.gauss(0, 2)))
            elif indicator_id == "GEOPOLITICAL_RISK":
                # Geopolitical risk can spike
                if random.random() < 0.05:  # 5% chance of spike
                    indicator["value"] = min(100, indicator["value"] + random.uniform(10, 30))
                else:
                    indicator["value"] = max(0, min(100, indicator["value"] + random.gauss(0, 5)))
            elif indicator_id == "US_CPI":
                # Inflation moves slowly
                indicator["value"] = max(0, indicator["value"] + random.gauss(0, 0.1))
                
        # Update uncertainty metrics
        self.uncertainty_metrics["market_stress"] = self.macro_indicators["VIX"]["value"] / 50
        self.uncertainty_metrics["fear_greed_index"] = 100 - (self.macro_indicators["VIX"]["value"] * 2)
        
    async def execute_hedge(self, portfolio_value: float, current_allocation: float) -> Dict[str, Any]:
        """Execute portfolio hedge with gold/commodities"""
        optimal_allocation = self._calculate_optimal_hedge_ratio(
            self.commodities["GOLD"]["volatility"],
            self.uncertainty_metrics["market_stress"]
        ) / 100
        
        adjustment_needed = optimal_allocation - current_allocation
        
        if abs(adjustment_needed) < 0.01:  # Less than 1% change
            return {
                "action": "No adjustment needed",
                "current_allocation": f"{current_allocation * 100:.1f}%",
                "target_allocation": f"{optimal_allocation * 100:.1f}%"
            }
            
        trade_value = portfolio_value * abs(adjustment_needed)
        
        return {
            "action": "Increase hedge" if adjustment_needed > 0 else "Reduce hedge",
            "current_allocation": f"{current_allocation * 100:.1f}%",
            "target_allocation": f"{optimal_allocation * 100:.1f}%",
            "trade_value": trade_value,
            "commodities_to_buy": self._select_hedge_commodities(trade_value) if adjustment_needed > 0 else [],
            "reason": f"Market stress at {self.uncertainty_metrics['market_stress']:.2f}"
        }
        
    def _select_hedge_commodities(self, value: float) -> List[Dict[str, Any]]:
        """Select commodities for hedging"""
        # Prioritize by safe haven score
        safe_havens = [
            (cid, cdata) for cid, cdata in self.commodities.items()
            if cdata["safe_haven_score"] > 0.7
        ]
        safe_havens.sort(key=lambda x: x[1]["safe_haven_score"], reverse=True)
        
        selections = []
        remaining_value = value
        
        for comm_id, comm_data in safe_havens[:3]:  # Top 3 safe havens
            allocation = remaining_value * 0.4 if len(selections) == 0 else remaining_value * 0.3
            selections.append({
                "commodity_id": comm_id,
                "commodity_name": comm_data["name"],
                "allocation": allocation,
                "units": allocation / self.commodity_performance[comm_id]["current_price"]
            })
            remaining_value -= allocation
            
        return selections
        
    async def rebalance_for_inflation(self, portfolio: Dict, current_inflation: float) -> Dict[str, Any]:
        """Rebalance commodity allocation based on inflation"""
        target_allocations = {}
        total_target = 0
        
        # Calculate target allocation for each commodity
        for position in portfolio.get("commodity_positions", []):
            commodity = self.commodities[position["commodity_id"]]
            target = self._calculate_target_allocation(current_inflation, position["commodity_id"]) / 100
            target_allocations[position["commodity_id"]] = target
            total_target += target
            
        # Normalize if over limit
        if total_target > self.hedging_rules["max_allocation"]:
            factor = self.hedging_rules["max_allocation"] / total_target
            target_allocations = {k: v * factor for k, v in target_allocations.items()}
            
        trades = []
        for position in portfolio.get("commodity_positions", []):
            current = position["allocation"]
            target = target_allocations.get(position["commodity_id"], 0)
            
            if abs(target - current) > 0.01:
                trades.append({
                    "commodity_id": position["commodity_id"],
                    "action": "Increase" if target > current else "Decrease",
                    "current_allocation": f"{current * 100:.1f}%",
                    "target_allocation": f"{target * 100:.1f}%",
                    "trade_percent": f"{abs(target - current) * 100:.1f}%"
                })
                
        return {
            "rebalance_needed": len(trades) > 0,
            "current_inflation": f"{current_inflation:.1f}%",
            "trades": trades,
            "reason": f"Inflation at {current_inflation:.1f}%, rebalancing commodity exposure"
        } 