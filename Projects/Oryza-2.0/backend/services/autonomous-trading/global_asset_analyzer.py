"""
Global Asset Analyzer
Handles currency hedging, geographic rebalancing based on growth, and FX optimization
"""

import random
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import logging
import math

class GlobalAssetAnalyzer:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Global assets universe
        self.global_assets = {
            # US Markets
            "SPY": {
                "name": "SPDR S&P 500 ETF",
                "symbol": "SPY",
                "type": "Equity ETF",
                "region": "North America",
                "country": "USA",
                "currency": "USD",
                "price": 445.50,
                "market_cap": 410000000000,
                "expense_ratio": 0.0945,
                "dividend_yield": 1.5,
                "liquidity": "Very High",
                "gdp_growth": 2.5,
                "correlation_to_world": 0.85
            },
            "QQQ": {
                "name": "Invesco QQQ Trust",
                "symbol": "QQQ",
                "type": "Tech ETF",
                "region": "North America",
                "country": "USA",
                "currency": "USD",
                "price": 385.25,
                "market_cap": 195000000000,
                "expense_ratio": 0.20,
                "dividend_yield": 0.6,
                "liquidity": "Very High",
                "gdp_growth": 2.5,
                "correlation_to_world": 0.75
            },
            
            # European Markets
            "VEUR": {
                "name": "Vanguard FTSE Europe ETF",
                "symbol": "VEUR",
                "type": "Regional ETF",
                "region": "Europe",
                "country": "Multi",
                "currency": "EUR",
                "price": 65.80,
                "market_cap": 18000000000,
                "expense_ratio": 0.08,
                "dividend_yield": 2.8,
                "liquidity": "High",
                "gdp_growth": 1.5,
                "correlation_to_world": 0.70
            },
            "EWG": {
                "name": "iShares MSCI Germany ETF",
                "symbol": "EWG",
                "type": "Country ETF",
                "region": "Europe",
                "country": "Germany",
                "currency": "EUR",
                "price": 28.50,
                "market_cap": 5500000000,
                "expense_ratio": 0.49,
                "dividend_yield": 2.2,
                "liquidity": "High",
                "gdp_growth": 1.2,
                "correlation_to_world": 0.65
            },
            
            # Asia-Pacific Markets
            "VPL": {
                "name": "Vanguard FTSE Pacific ETF",
                "symbol": "VPL",
                "type": "Regional ETF",
                "region": "Asia-Pacific",
                "country": "Multi",
                "currency": "Multi",
                "price": 78.25,
                "market_cap": 6800000000,
                "expense_ratio": 0.08,
                "dividend_yield": 2.5,
                "liquidity": "High",
                "gdp_growth": 3.5,
                "correlation_to_world": 0.60
            },
            "EWJ": {
                "name": "iShares MSCI Japan ETF",
                "symbol": "EWJ",
                "type": "Country ETF",
                "region": "Asia-Pacific",
                "country": "Japan",
                "currency": "JPY",
                "price": 58.90,
                "market_cap": 15000000000,
                "expense_ratio": 0.49,
                "dividend_yield": 1.8,
                "liquidity": "Very High",
                "gdp_growth": 1.0,
                "correlation_to_world": 0.55
            },
            
            # Emerging Markets
            "VWO": {
                "name": "Vanguard FTSE Emerging Markets ETF",
                "symbol": "VWO",
                "type": "Regional ETF",
                "region": "Emerging Markets",
                "country": "Multi",
                "currency": "Multi",
                "price": 42.15,
                "market_cap": 75000000000,
                "expense_ratio": 0.08,
                "dividend_yield": 3.1,
                "liquidity": "Very High",
                "gdp_growth": 4.5,
                "correlation_to_world": 0.65
            },
            "INDA": {
                "name": "iShares MSCI India ETF",
                "symbol": "INDA",
                "type": "Country ETF",
                "region": "Emerging Markets",
                "country": "India",
                "currency": "INR",
                "price": 45.75,
                "market_cap": 8500000000,
                "expense_ratio": 0.65,
                "dividend_yield": 0.9,
                "liquidity": "High",
                "gdp_growth": 6.5,
                "correlation_to_world": 0.50
            },
            "FXI": {
                "name": "iShares China Large-Cap ETF",
                "symbol": "FXI",
                "type": "Country ETF",
                "region": "Emerging Markets",
                "country": "China",
                "currency": "CNY",
                "price": 28.35,
                "market_cap": 5200000000,
                "expense_ratio": 0.74,
                "dividend_yield": 2.4,
                "liquidity": "High",
                "gdp_growth": 5.0,
                "correlation_to_world": 0.45
            },
            "EWZ": {
                "name": "iShares MSCI Brazil ETF",
                "symbol": "EWZ",
                "type": "Country ETF",
                "region": "Emerging Markets",
                "country": "Brazil",
                "currency": "BRL",
                "price": 32.40,
                "market_cap": 7000000000,
                "expense_ratio": 0.59,
                "dividend_yield": 4.5,
                "liquidity": "High",
                "gdp_growth": 2.8,
                "correlation_to_world": 0.55
            },
            
            # Currency-Hedged Versions
            "HEDJ": {
                "name": "WisdomTree Europe Hedged Equity",
                "symbol": "HEDJ",
                "type": "Currency-Hedged ETF",
                "region": "Europe",
                "country": "Multi",
                "currency": "USD",
                "price": 28.75,
                "market_cap": 1200000000,
                "expense_ratio": 0.58,
                "dividend_yield": 2.6,
                "liquidity": "Medium",
                "gdp_growth": 1.5,
                "correlation_to_world": 0.68,
                "currency_hedged": True
            },
            "DXJ": {
                "name": "WisdomTree Japan Hedged Equity",
                "symbol": "DXJ",
                "type": "Currency-Hedged ETF",
                "region": "Asia-Pacific",
                "country": "Japan",
                "currency": "USD",
                "price": 62.15,
                "market_cap": 3500000000,
                "expense_ratio": 0.48,
                "dividend_yield": 1.7,
                "liquidity": "High",
                "gdp_growth": 1.0,
                "correlation_to_world": 0.52,
                "currency_hedged": True
            }
        }
        
        # Currency exchange rates (to USD)
        self.exchange_rates = {
            "USD": 1.0,
            "EUR": 1.08,
            "JPY": 0.0067,  # 1 USD = 150 JPY
            "GBP": 1.27,
            "CNY": 0.14,    # 1 USD = 7.2 CNY
            "INR": 0.012,   # 1 USD = 83 INR
            "BRL": 0.20,    # 1 USD = 5 BRL
            "AUD": 0.65,
            "CAD": 0.73,
            "CHF": 1.10
        }
        
        # Regional growth projections
        self.regional_growth = {
            "North America": {
                "current_gdp_growth": 2.5,
                "projected_growth": 2.3,
                "trend": "stable",
                "demographic_bonus": 0.3,
                "innovation_index": 0.85
            },
            "Europe": {
                "current_gdp_growth": 1.5,
                "projected_growth": 1.8,
                "trend": "recovering",
                "demographic_bonus": -0.2,
                "innovation_index": 0.75
            },
            "Asia-Pacific": {
                "current_gdp_growth": 3.5,
                "projected_growth": 4.0,
                "trend": "accelerating",
                "demographic_bonus": 0.5,
                "innovation_index": 0.70
            },
            "Emerging Markets": {
                "current_gdp_growth": 4.5,
                "projected_growth": 5.2,
                "trend": "strong",
                "demographic_bonus": 0.8,
                "innovation_index": 0.60
            }
        }
        
        # Currency volatility tracking
        self.currency_volatility = {
            "USD": 0.08,
            "EUR": 0.10,
            "JPY": 0.12,
            "GBP": 0.11,
            "CNY": 0.06,
            "INR": 0.15,
            "BRL": 0.20,
            "AUD": 0.13,
            "CAD": 0.09,
            "CHF": 0.07
        }
        
        # Performance tracking
        self.asset_performance = {}
        self._initialize_performance()
        
        # Hedging parameters
        self.hedging_rules = {
            "volatility_threshold": 0.15,  # Hedge when currency vol > 15%
            "correlation_threshold": -0.3,  # Hedge when negative correlation
            "cost_threshold": 0.005,       # Max 50 bps hedging cost
            "min_exposure": 0.05,          # Min 5% exposure to hedge
            "rebalance_frequency": 30      # Days
        }
        
        # FX optimization parameters
        self.fx_optimization = {
            "target_currency": "USD",
            "max_unhedged_exposure": 0.30,
            "emerging_market_limit": 0.20,
            "developed_market_limit": 0.50
        }
        
    def _initialize_performance(self):
        """Initialize asset performance tracking"""
        for asset_id, asset_data in self.global_assets.items():
            self.asset_performance[asset_id] = {
                "current_price": asset_data["price"],
                "daily_change": 0,
                "daily_change_percent": 0,
                "weekly_return": random.uniform(-2, 3),
                "monthly_return": random.uniform(-5, 8),
                "ytd_return": random.uniform(-10, 25),
                "local_currency_return": random.uniform(-8, 20),
                "usd_return": random.uniform(-12, 22),
                "volatility": random.uniform(0.12, 0.25),
                "sharpe_ratio": random.uniform(0.5, 2.0),
                "tracking_error": random.uniform(0.02, 0.08)
            }
            
    async def analyze_global_asset_multi_agent(self, asset_id: str) -> Dict[str, Any]:
        """Multi-agent analysis of a global asset"""
        asset = self.global_assets.get(asset_id)
        if not asset:
            return None
            
        performance = self.asset_performance[asset_id]
        
        # Global Agent Analysis
        global_analysis = await self._global_agent_analysis(asset, performance)
        
        # Macro Agent Analysis
        macro_analysis = await self._macro_agent_analysis(asset, performance)
        
        # Currency Agent Analysis
        currency_analysis = await self._currency_agent_analysis(asset, performance)
        
        # Growth Agent Analysis
        growth_analysis = await self._growth_agent_analysis(asset, performance)
        
        # Build consensus
        consensus = await self._build_global_consensus(
            global_analysis, macro_analysis, currency_analysis, growth_analysis
        )
        
        return {
            "asset_id": asset_id,
            "asset_name": asset["name"],
            "current_price": performance["current_price"],
            "daily_change": performance["daily_change_percent"],
            "agents": {
                "global": global_analysis,
                "macro": macro_analysis,
                "currency": currency_analysis,
                "growth": growth_analysis
            },
            "consensus": consensus,
            "timestamp": datetime.now().isoformat()
        }
        
    async def _global_agent_analysis(self, asset: Dict, performance: Dict) -> Dict[str, Any]:
        """Analyze global asset positioning and diversification"""
        # Regional analysis
        regional_score = self._calculate_regional_score(asset["region"])
        
        # Diversification benefit
        diversification_benefit = 1 - asset["correlation_to_world"]
        
        # Liquidity assessment
        liquidity_score = self._assess_liquidity(asset["liquidity"])
        
        # Cost efficiency
        cost_score = 1 - (asset["expense_ratio"] / 100)
        
        return {
            "region": asset["region"],
            "country": asset["country"],
            "regional_score": f"{regional_score:.2f}/10",
            "diversification_benefit": f"{diversification_benefit:.2f}",
            "correlation_to_world": f"{asset['correlation_to_world']:.2f}",
            "liquidity": asset["liquidity"],
            "liquidity_score": f"{liquidity_score:.1f}/10",
            "expense_ratio": f"{asset['expense_ratio']:.2f}%",
            "dividend_yield": f"{asset['dividend_yield']:.1f}%",
            "ytd_performance": f"{performance['ytd_return']:.1f}%",
            "volatility": f"{performance['volatility'] * 100:.1f}%",
            "sharpe_ratio": f"{performance['sharpe_ratio']:.2f}",
            "recommendation": self._get_global_recommendation(regional_score, diversification_benefit)
        }
        
    async def _macro_agent_analysis(self, asset: Dict, performance: Dict) -> Dict[str, Any]:
        """Analyze macroeconomic factors affecting the asset"""
        # GDP growth impact
        gdp_impact = self._assess_gdp_impact(asset["gdp_growth"])
        
        # Regional trends
        regional_trend = self.regional_growth[asset["region"]]["trend"]
        
        # Interest rate differential
        rate_differential = self._calculate_rate_differential(asset["region"])
        
        # Political stability
        political_risk = self._assess_political_risk(asset["country"])
        
        # Trade dynamics
        trade_balance = self._assess_trade_dynamics(asset["region"])
        
        return {
            "gdp_growth": f"{asset['gdp_growth']}%",
            "gdp_impact": gdp_impact,
            "regional_trend": regional_trend,
            "projected_growth": f"{self.regional_growth[asset['region']]['projected_growth']}%",
            "rate_differential": f"{rate_differential:.1f}%",
            "political_risk": political_risk,
            "trade_balance": trade_balance,
            "demographic_bonus": f"{self.regional_growth[asset['region']]['demographic_bonus']:.1f}",
            "innovation_index": f"{self.regional_growth[asset['region']]['innovation_index']:.2f}",
            "macro_score": f"{self._calculate_macro_score(asset):.1f}/10",
            "outlook": self._get_macro_outlook(asset["region"])
        }
        
    async def _currency_agent_analysis(self, asset: Dict, performance: Dict) -> Dict[str, Any]:
        """Analyze currency exposure and hedging needs"""
        currency = asset["currency"]
        
        # Currency volatility
        currency_vol = self.currency_volatility.get(currency, 0.15)
        
        # Exchange rate trend
        fx_trend = self._analyze_fx_trend(currency)
        
        # Hedging cost
        hedging_cost = self._calculate_hedging_cost(currency)
        
        # Currency carry
        carry_return = self._calculate_carry_return(currency)
        
        # Hedging recommendation
        hedge_recommendation = self._recommend_hedging(
            currency, currency_vol, asset.get("currency_hedged", False)
        )
        
        return {
            "base_currency": currency,
            "exchange_rate": f"{self.exchange_rates.get(currency, 1):.4f}",
            "currency_volatility": f"{currency_vol * 100:.1f}%",
            "fx_trend": fx_trend,
            "local_return": f"{performance['local_currency_return']:.1f}%",
            "usd_return": f"{performance['usd_return']:.1f}%",
            "currency_impact": f"{performance['usd_return'] - performance['local_currency_return']:.1f}%",
            "hedging_cost": f"{hedging_cost * 100:.1f}%",
            "carry_return": f"{carry_return:.1f}%",
            "is_hedged": asset.get("currency_hedged", False),
            "hedge_recommendation": hedge_recommendation,
            "optimal_hedge_ratio": self._calculate_optimal_hedge_ratio(currency_vol)
        }
        
    async def _growth_agent_analysis(self, asset: Dict, performance: Dict) -> Dict[str, Any]:
        """Analyze growth prospects and rebalancing needs"""
        region = asset["region"]
        
        # Growth differential
        growth_diff = self.regional_growth[region]["projected_growth"] - self.regional_growth[region]["current_gdp_growth"]
        
        # Valuation metrics
        valuation = self._assess_valuation(asset, performance)
        
        # Momentum score
        momentum = self._calculate_momentum(performance)
        
        # Rebalancing signal
        rebalance_signal = self._generate_rebalance_signal(
            region, growth_diff, valuation, momentum
        )
        
        # Target allocation
        target_allocation = self._calculate_target_allocation(region)
        
        return {
            "current_growth": f"{self.regional_growth[region]['current_gdp_growth']}%",
            "projected_growth": f"{self.regional_growth[region]['projected_growth']}%",
            "growth_differential": f"{growth_diff:+.1f}%",
            "growth_trend": self.regional_growth[region]["trend"],
            "valuation": valuation,
            "momentum_score": f"{momentum:.2f}",
            "demographic_tailwind": self.regional_growth[region]["demographic_bonus"] > 0,
            "innovation_strength": self.regional_growth[region]["innovation_index"] > 0.7,
            "rebalance_signal": rebalance_signal,
            "target_allocation": f"{target_allocation:.1f}%",
            "time_horizon": self._suggest_time_horizon(region)
        }
        
    async def _build_global_consensus(self, global_a: Dict, macro: Dict, currency: Dict, growth: Dict) -> Dict[str, Any]:
        """Build multi-agent consensus for global asset allocation"""
        scores = []
        
        # Global score (diversification and efficiency)
        global_score = float(global_a["regional_score"].split("/")[0]) / 10
        scores.append(global_score)
        
        # Macro score
        macro_score = float(macro["macro_score"].split("/")[0]) / 10
        scores.append(macro_score)
        
        # Currency score (inverse if high volatility)
        currency_risk = float(currency["currency_volatility"].strip("%")) / 100
        currency_score = 1 - (currency_risk / 0.3)  # Normalize to 0-1
        if currency["is_hedged"]:
            currency_score = min(1, currency_score + 0.2)
        scores.append(currency_score)
        
        # Growth score
        growth_score = 0.8 if growth["rebalance_signal"] == "Increase" else \
                      0.6 if growth["rebalance_signal"] == "Hold" else 0.4
        scores.append(growth_score)
        
        # Weighted consensus
        weights = [1.0, 1.2, 0.8, 1.5]  # Growth weighted highest
        weighted_score = sum(s * w for s, w in zip(scores, weights)) / sum(weights)
        
        # Determine action
        if weighted_score > 0.7:
            action = "OVERWEIGHT"
            recommendation = "Increase allocation to capture growth"
        elif weighted_score > 0.55:
            action = "NEUTRAL"
            recommendation = "Maintain market weight"
        elif weighted_score > 0.45:
            action = "UNDERWEIGHT"
            recommendation = "Reduce exposure"
        else:
            action = "AVOID"
            recommendation = "Exit position"
            
        # Currency hedging decision
        currency_action = self._determine_currency_action(currency, macro)
        
        return {
            "action": action,
            "confidence": f"{weighted_score * 100:.0f}%",
            "recommendation": recommendation,
            "target_allocation": growth["target_allocation"],
            "currency_action": currency_action,
            "key_drivers": self._identify_key_drivers(global_a, macro, currency, growth),
            "risks": self._identify_risks(global_a, macro, currency, growth),
            "implementation": self._suggest_implementation(action, currency_action)
        }
        
    def _calculate_regional_score(self, region: str) -> float:
        """Calculate regional attractiveness score"""
        growth_data = self.regional_growth[region]
        
        score = 5.0  # Base score
        
        # Growth component
        if growth_data["projected_growth"] > 4:
            score += 2
        elif growth_data["projected_growth"] > 2:
            score += 1
            
        # Trend component
        if growth_data["trend"] == "accelerating":
            score += 1.5
        elif growth_data["trend"] == "strong":
            score += 1
            
        # Demographic component
        score += growth_data["demographic_bonus"]
        
        # Innovation component
        score += growth_data["innovation_index"] * 2
        
        return min(10, max(0, score))
        
    def _assess_liquidity(self, liquidity: str) -> float:
        """Assess liquidity score"""
        liquidity_scores = {
            "Very High": 10,
            "High": 8,
            "Medium": 6,
            "Low": 4,
            "Very Low": 2
        }
        return liquidity_scores.get(liquidity, 5)
        
    def _get_global_recommendation(self, regional_score: float, diversification: float) -> str:
        """Get global positioning recommendation"""
        if regional_score > 7 and diversification > 0.4:
            return "Strong allocation recommended"
        elif regional_score > 5:
            return "Moderate allocation suitable"
        else:
            return "Limited allocation advised"
            
    def _assess_gdp_impact(self, gdp_growth: float) -> str:
        """Assess GDP growth impact"""
        if gdp_growth > 5:
            return "Very Positive"
        elif gdp_growth > 3:
            return "Positive"
        elif gdp_growth > 1:
            return "Neutral"
        else:
            return "Negative"
            
    def _calculate_rate_differential(self, region: str) -> float:
        """Calculate interest rate differential"""
        # Simplified - would use actual central bank rates
        rate_differentials = {
            "North America": 0.0,
            "Europe": -2.5,
            "Asia-Pacific": -3.0,
            "Emerging Markets": 2.5
        }
        return rate_differentials.get(region, 0)
        
    def _assess_political_risk(self, country: str) -> str:
        """Assess political risk level"""
        low_risk = ["USA", "Germany", "Japan", "Multi"]
        medium_risk = ["India", "Brazil"]
        high_risk = ["China"]
        
        if country in low_risk:
            return "Low"
        elif country in medium_risk:
            return "Medium"
        elif country in high_risk:
            return "High"
        else:
            return "Medium"
            
    def _assess_trade_dynamics(self, region: str) -> str:
        """Assess trade balance dynamics"""
        trade_assessment = {
            "North America": "Deficit but reserve currency",
            "Europe": "Balanced with surplus bias",
            "Asia-Pacific": "Export driven surplus",
            "Emerging Markets": "Mixed dynamics"
        }
        return trade_assessment.get(region, "Neutral")
        
    def _calculate_macro_score(self, asset: Dict) -> float:
        """Calculate comprehensive macro score"""
        score = 5.0
        
        # GDP growth
        if asset["gdp_growth"] > 4:
            score += 2
        elif asset["gdp_growth"] > 2:
            score += 1
            
        # Regional trend
        region = asset["region"]
        if self.regional_growth[region]["trend"] in ["accelerating", "strong"]:
            score += 1.5
            
        # Political stability
        if self._assess_political_risk(asset["country"]) == "Low":
            score += 1
            
        # Innovation
        score += self.regional_growth[region]["innovation_index"]
        
        return min(10, score)
        
    def _get_macro_outlook(self, region: str) -> str:
        """Get macroeconomic outlook"""
        outlooks = {
            "North America": "Stable growth with innovation leadership",
            "Europe": "Recovery phase with structural reforms",
            "Asia-Pacific": "Dynamic growth with demographic dividend",
            "Emerging Markets": "High growth with volatility"
        }
        return outlooks.get(region, "Neutral outlook")
        
    def _analyze_fx_trend(self, currency: str) -> str:
        """Analyze foreign exchange trend"""
        # Simplified - would use actual FX data
        if currency == "USD":
            return "Strengthening"
        elif currency in ["EUR", "GBP", "CHF"]:
            return "Stable"
        elif currency in ["JPY", "CNY"]:
            return "Weakening"
        else:
            return "Volatile"
            
    def _calculate_hedging_cost(self, currency: str) -> float:
        """Calculate currency hedging cost"""
        # Based on interest rate differentials and volatility
        base_cost = 0.002  # 20 bps base
        
        volatility_adj = self.currency_volatility.get(currency, 0.15) * 0.1
        
        # Emerging market premium
        if currency in ["BRL", "INR", "CNY"]:
            base_cost += 0.003
            
        return base_cost + volatility_adj
        
    def _calculate_carry_return(self, currency: str) -> float:
        """Calculate currency carry return"""
        # Interest rate differential approximation
        carry_returns = {
            "USD": 0.0,
            "EUR": -2.5,
            "JPY": -5.0,
            "GBP": -0.5,
            "CNY": 2.0,
            "INR": 3.5,
            "BRL": 8.0
        }
        return carry_returns.get(currency, 0)
        
    def _recommend_hedging(self, currency: str, volatility: float, is_hedged: bool) -> str:
        """Recommend currency hedging strategy"""
        if is_hedged:
            return "Already hedged - monitor costs"
            
        if volatility > self.hedging_rules["volatility_threshold"]:
            return "Hedge recommended - high volatility"
        elif currency in ["BRL", "INR"] and volatility > 0.12:
            return "Partial hedge suggested"
        elif currency in ["EUR", "GBP", "CHF"]:
            return "Optional - stable currency"
        else:
            return "Monitor - hedging not urgent"
            
    def _calculate_optimal_hedge_ratio(self, volatility: float) -> str:
        """Calculate optimal hedge ratio"""
        if volatility > 0.20:
            return "80-100%"
        elif volatility > 0.15:
            return "50-80%"
        elif volatility > 0.10:
            return "30-50%"
        else:
            return "0-30%"
            
    def _assess_valuation(self, asset: Dict, performance: Dict) -> str:
        """Assess regional valuation"""
        # Simplified P/E based on region
        pe_ratios = {
            "North America": 22,
            "Europe": 16,
            "Asia-Pacific": 18,
            "Emerging Markets": 14
        }
        
        regional_pe = pe_ratios.get(asset["region"], 18)
        
        if regional_pe > 20:
            return "Expensive"
        elif regional_pe > 16:
            return "Fair"
        else:
            return "Attractive"
            
    def _calculate_momentum(self, performance: Dict) -> float:
        """Calculate momentum score"""
        # Weighted average of returns
        momentum = (
            performance["weekly_return"] * 0.5 +
            performance["monthly_return"] * 0.3 +
            performance["ytd_return"] * 0.2
        ) / 10
        
        return max(-1, min(1, momentum))
        
    def _generate_rebalance_signal(self, region: str, growth_diff: float, valuation: str, momentum: float) -> str:
        """Generate rebalancing signal"""
        score = 0
        
        if growth_diff > 0.5:
            score += 2
        elif growth_diff > 0:
            score += 1
            
        if valuation == "Attractive":
            score += 2
        elif valuation == "Fair":
            score += 1
            
        if momentum > 0.5:
            score += 1
            
        if score >= 4:
            return "Increase"
        elif score >= 2:
            return "Hold"
        else:
            return "Reduce"
            
    def _calculate_target_allocation(self, region: str) -> float:
        """Calculate target allocation by region"""
        base_allocations = {
            "North America": 35,
            "Europe": 20,
            "Asia-Pacific": 25,
            "Emerging Markets": 20
        }
        
        base = base_allocations.get(region, 25)
        
        # Adjust for growth
        growth_adj = (self.regional_growth[region]["projected_growth"] - 2.5) * 2
        
        # Adjust for demographics
        demo_adj = self.regional_growth[region]["demographic_bonus"] * 5
        
        target = base + growth_adj + demo_adj
        
        return max(10, min(40, target))
        
    def _suggest_time_horizon(self, region: str) -> str:
        """Suggest investment time horizon"""
        if region == "Emerging Markets":
            return "5-10 years (volatility buffer)"
        elif region == "Asia-Pacific":
            return "3-7 years (growth capture)"
        else:
            return "3-5 years (standard)"
            
    def _determine_currency_action(self, currency: Dict, macro: Dict) -> str:
        """Determine currency hedging action"""
        if currency["hedge_recommendation"].startswith("Hedge recommended"):
            return "Implement full hedge"
        elif currency["hedge_recommendation"].startswith("Partial"):
            return f"Hedge {currency['optimal_hedge_ratio']}"
        elif currency["is_hedged"] and float(currency["hedging_cost"].strip("%")) > 1:
            return "Consider removing hedge (high cost)"
        else:
            return "No hedging needed"
            
    def _identify_key_drivers(self, global_a: Dict, macro: Dict, currency: Dict, growth: Dict) -> List[str]:
        """Identify key investment drivers"""
        drivers = []
        
        if float(growth["growth_differential"]) > 1:
            drivers.append("Accelerating growth")
        if macro["regional_trend"] in ["accelerating", "strong"]:
            drivers.append(f"Regional momentum ({macro['regional_trend']})")
        if float(global_a["diversification_benefit"]) > 0.4:
            drivers.append("High diversification benefit")
        if growth["valuation"] == "Attractive":
            drivers.append("Attractive valuations")
            
        return drivers[:3]
        
    def _identify_risks(self, global_a: Dict, macro: Dict, currency: Dict, growth: Dict) -> List[str]:
        """Identify key risks"""
        risks = []
        
        if float(currency["currency_volatility"].strip("%")) > 15:
            risks.append("High currency volatility")
        if macro["political_risk"] in ["Medium", "High"]:
            risks.append(f"{macro['political_risk']} political risk")
        if float(global_a["expense_ratio"].strip("%")) > 0.5:
            risks.append("High expense ratio")
        if growth["valuation"] == "Expensive":
            risks.append("Elevated valuations")
            
        return risks
        
    def _suggest_implementation(self, action: str, currency_action: str) -> List[str]:
        """Suggest implementation steps"""
        steps = []
        
        if action == "OVERWEIGHT":
            steps.append("Increase allocation by 5-10%")
            steps.append("Use limit orders for better execution")
        elif action == "UNDERWEIGHT":
            steps.append("Reduce allocation by 5-10%")
            steps.append("Sell into strength")
            
        if "Implement" in currency_action:
            steps.append(currency_action)
        elif "Hedge" in currency_action and "%" in currency_action:
            steps.append(f"Implement {currency_action}")
            
        if len(steps) == 0:
            steps.append("Maintain current positioning")
            
        return steps
        
    def update_exchange_rates(self):
        """Update exchange rates with realistic movements"""
        for currency, rate in self.exchange_rates.items():
            if currency == "USD":
                continue
                
            # Daily movement based on volatility
            volatility = self.currency_volatility.get(currency, 0.10)
            daily_move = random.gauss(0, volatility / math.sqrt(252))
            
            # Trend bias
            if currency in ["EUR", "GBP", "CHF"]:
                daily_move += random.uniform(-0.0005, 0.0005)  # Stable
            elif currency in ["JPY"]:
                daily_move -= 0.0002  # Weakening bias
            elif currency in ["BRL", "INR"]:
                daily_move -= 0.0003  # EM weakness
                
            # Apply change
            self.exchange_rates[currency] = rate * (1 + daily_move)
            
    def update_prices(self):
        """Update global asset prices"""
        for asset_id, performance in self.asset_performance.items():
            asset = self.global_assets[asset_id]
            
            # Base price movement
            volatility = performance["volatility"]
            daily_move = random.gauss(0, volatility / math.sqrt(252))
            
            # Regional bias
            region = asset["region"]
            if self.regional_growth[region]["trend"] == "accelerating":
                daily_move += 0.0005
            elif self.regional_growth[region]["trend"] == "strong":
                daily_move += 0.0003
                
            # Currency impact (if not USD)
            if asset["currency"] != "USD" and not asset.get("currency_hedged", False):
                fx_rate = self.exchange_rates.get(asset["currency"], 1)
                fx_impact = (fx_rate - 1) * 0.01  # Simplified
                daily_move += fx_impact
                
            # Apply price change
            old_price = performance["current_price"]
            new_price = old_price * (1 + daily_move)
            
            performance["current_price"] = new_price
            performance["daily_change"] = new_price - old_price
            performance["daily_change_percent"] = daily_move * 100
            
            # Update returns
            performance["weekly_return"] = performance["weekly_return"] * 0.8 + daily_move * 100 * 5
            performance["monthly_return"] = performance["monthly_return"] * 0.95 + daily_move * 100 * 2
            
            # Update currency returns
            performance["local_currency_return"] = performance["ytd_return"]
            if asset["currency"] != "USD":
                fx_ytd_impact = (self.exchange_rates[asset["currency"]] - 1) * 100
                performance["usd_return"] = performance["local_currency_return"] + fx_ytd_impact
            else:
                performance["usd_return"] = performance["local_currency_return"]
                
    async def optimize_currency_exposure(self, portfolio: Dict) -> Dict[str, Any]:
        """Optimize currency exposure across portfolio"""
        positions = portfolio.get("global_positions", [])
        
        # Calculate current exposures
        currency_exposures = self._calculate_currency_exposures(positions)
        
        # Assess hedging needs
        hedging_recommendations = []
        for currency, exposure in currency_exposures.items():
            if currency == "USD":
                continue
                
            volatility = self.currency_volatility.get(currency, 0.15)
            
            if exposure > self.fx_optimization["max_unhedged_exposure"]:
                hedging_recommendations.append({
                    "currency": currency,
                    "current_exposure": f"{exposure * 100:.1f}%",
                    "recommended_hedge": f"{(exposure - self.fx_optimization['max_unhedged_exposure']) * 100:.1f}%",
                    "volatility": f"{volatility * 100:.1f}%",
                    "cost": f"{self._calculate_hedging_cost(currency) * 100:.1f}%"
                })
                
        # Calculate optimal allocation
        optimal_hedges = self._optimize_hedge_allocation(currency_exposures)
        
        return {
            "currency_exposures": {k: f"{v*100:.1f}%" for k, v in currency_exposures.items()},
            "total_foreign_exposure": f"{(1 - currency_exposures.get('USD', 0)) * 100:.1f}%",
            "hedging_recommendations": hedging_recommendations,
            "optimal_hedges": optimal_hedges,
            "estimated_cost": self._calculate_total_hedging_cost(optimal_hedges),
            "risk_reduction": self._estimate_risk_reduction(optimal_hedges)
        }
        
    def _calculate_currency_exposures(self, positions: List[Dict]) -> Dict[str, float]:
        """Calculate currency exposures from positions"""
        total_value = sum(p["current_value"] for p in positions)
        exposures = {}
        
        for position in positions:
            asset = self.global_assets.get(position["asset_id"])
            if not asset:
                continue
                
            currency = asset["currency"]
            if asset.get("currency_hedged", False):
                currency = "USD"
                
            if currency == "Multi":
                # Distribute across major currencies
                weight = position["current_value"] / total_value
                exposures["USD"] = exposures.get("USD", 0) + weight * 0.4
                exposures["EUR"] = exposures.get("EUR", 0) + weight * 0.3
                exposures["JPY"] = exposures.get("JPY", 0) + weight * 0.2
                exposures["Other"] = exposures.get("Other", 0) + weight * 0.1
            else:
                exposures[currency] = exposures.get(currency, 0) + position["current_value"] / total_value
                
        return exposures
        
    def _optimize_hedge_allocation(self, exposures: Dict[str, float]) -> List[Dict[str, Any]]:
        """Optimize hedge allocation across currencies"""
        hedges = []
        
        for currency, exposure in exposures.items():
            if currency == "USD":
                continue
                
            volatility = self.currency_volatility.get(currency, 0.15)
            cost = self._calculate_hedging_cost(currency)
            
            # Decision logic
            if volatility > self.hedging_rules["volatility_threshold"] and exposure > self.hedging_rules["min_exposure"]:
                hedge_ratio = min(1.0, volatility / self.hedging_rules["volatility_threshold"])
                
                hedges.append({
                    "currency": currency,
                    "exposure": exposure,
                    "hedge_ratio": hedge_ratio,
                    "notional": exposure * hedge_ratio,
                    "cost": cost,
                    "benefit": volatility * hedge_ratio
                })
                
        return hedges
        
    def _calculate_total_hedging_cost(self, hedges: List[Dict]) -> str:
        """Calculate total cost of hedging program"""
        total_cost = sum(h["notional"] * h["cost"] for h in hedges)
        return f"{total_cost * 100:.2f}%"
        
    def _estimate_risk_reduction(self, hedges: List[Dict]) -> str:
        """Estimate portfolio risk reduction from hedging"""
        if not hedges:
            return "0.0%"
            
        risk_reduction = sum(h["benefit"] * h["notional"] for h in hedges) / sum(h["notional"] for h in hedges)
        return f"{risk_reduction * 100:.1f}%"
        
    async def rebalance_geographic_allocation(self, portfolio: Dict) -> Dict[str, Any]:
        """Rebalance portfolio based on growth projections"""
        positions = portfolio.get("global_positions", [])
        
        # Calculate current allocation
        current_allocation = self._calculate_regional_allocation(positions)
        
        # Calculate target allocation
        target_allocation = self._calculate_target_regional_allocation()
        
        # Generate rebalancing trades
        trades = self._generate_rebalancing_trades(current_allocation, target_allocation, positions)
        
        return {
            "current_allocation": {k: f"{v*100:.1f}%" for k, v in current_allocation.items()},
            "target_allocation": {k: f"{v*100:.1f}%" for k, v in target_allocation.items()},
            "rebalancing_trades": trades,
            "expected_impact": self._calculate_rebalancing_impact(trades),
            "implementation_cost": self._estimate_implementation_cost(trades)
        }
        
    def _calculate_regional_allocation(self, positions: List[Dict]) -> Dict[str, float]:
        """Calculate current regional allocation"""
        total_value = sum(p["current_value"] for p in positions)
        allocation = {}
        
        for position in positions:
            asset = self.global_assets.get(position["asset_id"])
            if not asset:
                continue
                
            region = asset["region"]
            allocation[region] = allocation.get(region, 0) + position["current_value"] / total_value
            
        return allocation
        
    def _calculate_target_regional_allocation(self) -> Dict[str, float]:
        """Calculate target allocation based on growth and other factors"""
        targets = {}
        total_score = 0
        
        for region, data in self.regional_growth.items():
            # Score based on multiple factors
            score = (
                data["projected_growth"] * 2 +
                data["demographic_bonus"] * 10 +
                data["innovation_index"] * 10
            )
            
            if data["trend"] == "accelerating":
                score *= 1.2
            elif data["trend"] == "strong":
                score *= 1.1
                
            targets[region] = score
            total_score += score
            
        # Normalize to percentages
        for region in targets:
            targets[region] = targets[region] / total_score
            
        return targets
        
    def _generate_rebalancing_trades(self, current: Dict, target: Dict, positions: List[Dict]) -> List[Dict]:
        """Generate specific rebalancing trades"""
        trades = []
        portfolio_value = sum(p["current_value"] for p in positions)
        
        for region in set(list(current.keys()) + list(target.keys())):
            current_weight = current.get(region, 0)
            target_weight = target.get(region, 0)
            
            difference = target_weight - current_weight
            
            if abs(difference) > 0.02:  # 2% threshold
                trade_value = difference * portfolio_value
                
                trades.append({
                    "region": region,
                    "action": "Buy" if difference > 0 else "Sell",
                    "current_weight": f"{current_weight * 100:.1f}%",
                    "target_weight": f"{target_weight * 100:.1f}%",
                    "trade_value": abs(trade_value),
                    "assets_affected": self._identify_affected_assets(region, positions, difference > 0)
                })
                
        return trades
        
    def _identify_affected_assets(self, region: str, positions: List[Dict], is_buy: bool) -> List[str]:
        """Identify which assets to trade for rebalancing"""
        affected = []
        
        for position in positions:
            asset = self.global_assets.get(position["asset_id"])
            if not asset or asset["region"] != region:
                continue
                
            if is_buy:
                # Prefer liquid, low-cost options for buys
                if asset["liquidity"] in ["Very High", "High"] and asset["expense_ratio"] < 0.5:
                    affected.append(asset["symbol"])
            else:
                # Prefer overvalued or underperforming for sells
                performance = self.asset_performance.get(position["asset_id"], {})
                if performance.get("ytd_return", 0) < 0 or affected == []:
                    affected.append(asset["symbol"])
                    
        return affected[:3]  # Top 3 assets
        
    def _calculate_rebalancing_impact(self, trades: List[Dict]) -> Dict[str, str]:
        """Calculate expected impact of rebalancing"""
        total_trades = sum(t["trade_value"] for t in trades)
        
        growth_improvement = 0
        for trade in trades:
            region = trade["region"]
            if trade["action"] == "Buy":
                growth_improvement += self.regional_growth[region]["projected_growth"] * (trade["trade_value"] / total_trades)
            else:
                growth_improvement -= self.regional_growth[region]["projected_growth"] * (trade["trade_value"] / total_trades)
                
        return {
            "expected_growth_improvement": f"{growth_improvement:.2f}%",
            "diversification_change": "Improved" if len(trades) > 2 else "Minimal",
            "risk_impact": "Reduced through rebalancing"
        }
        
    def _estimate_implementation_cost(self, trades: List[Dict]) -> str:
        """Estimate cost to implement rebalancing"""
        # Assume 10 bps for liquid markets, 20 bps for emerging
        total_cost = 0
        
        for trade in trades:
            if trade["region"] == "Emerging Markets":
                cost_bps = 20
            else:
                cost_bps = 10
                
            total_cost += trade["trade_value"] * cost_bps / 10000
            
        return f"${total_cost:,.0f}" 