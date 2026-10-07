"""
Alternative Investments Analyzer
Discovers opportunities in REITs, crypto, art, and manages liquidity across illiquid assets
"""

import random
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import logging
import math

class AlternativeAnalyzer:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Alternative investments universe
        self.alternatives = {
            # REITs (Real Estate Investment Trusts)
            "EMBASSY_REIT": {
                "name": "Embassy Office Parks REIT",
                "symbol": "EMBASSY",
                "type": "REIT",
                "sub_type": "Commercial",
                "price": 320.50,
                "currency": "INR",
                "dividend_yield": 6.8,
                "nav": 385.00,
                "discount_to_nav": -16.7,
                "liquidity": "High",
                "min_investment": 1000,
                "volatility": 0.18,
                "correlation_to_equity": 0.65,
                "income_stability": 0.85
            },
            "MINDSPACE_REIT": {
                "name": "Mindspace Business Parks REIT",
                "symbol": "MINDSPACE",
                "type": "REIT",
                "sub_type": "Commercial",
                "price": 295.25,
                "currency": "INR",
                "dividend_yield": 7.2,
                "nav": 340.00,
                "discount_to_nav": -13.2,
                "liquidity": "High",
                "min_investment": 1000,
                "volatility": 0.20,
                "correlation_to_equity": 0.62,
                "income_stability": 0.83
            },
            "BROOKFIELD_REIT": {
                "name": "Brookfield India Real Estate Trust",
                "symbol": "BIRET",
                "type": "REIT",
                "sub_type": "Mixed",
                "price": 275.00,
                "currency": "INR",
                "dividend_yield": 7.5,
                "nav": 310.00,
                "discount_to_nav": -11.3,
                "liquidity": "Medium",
                "min_investment": 1000,
                "volatility": 0.22,
                "correlation_to_equity": 0.60,
                "income_stability": 0.80
            },
            
            # Cryptocurrencies
            "BITCOIN": {
                "name": "Bitcoin",
                "symbol": "BTC",
                "type": "Cryptocurrency",
                "sub_type": "Major",
                "price": 42850.00,
                "currency": "USD",
                "market_cap": 838000000000,
                "24h_volume": 25000000000,
                "liquidity": "Very High",
                "min_investment": 0.001,
                "volatility": 0.45,
                "correlation_to_equity": 0.35,
                "network_effect": 0.95,
                "adoption_rate": 0.80
            },
            "ETHEREUM": {
                "name": "Ethereum",
                "symbol": "ETH",
                "type": "Cryptocurrency",
                "sub_type": "Major",
                "price": 2280.00,
                "currency": "USD",
                "market_cap": 274000000000,
                "24h_volume": 12000000000,
                "liquidity": "Very High",
                "min_investment": 0.01,
                "volatility": 0.50,
                "correlation_to_equity": 0.40,
                "network_effect": 0.85,
                "adoption_rate": 0.75
            },
            "SOLANA": {
                "name": "Solana",
                "symbol": "SOL",
                "type": "Cryptocurrency",
                "sub_type": "Alt",
                "price": 98.50,
                "currency": "USD",
                "market_cap": 42000000000,
                "24h_volume": 2500000000,
                "liquidity": "High",
                "min_investment": 0.1,
                "volatility": 0.65,
                "correlation_to_equity": 0.45,
                "network_effect": 0.60,
                "adoption_rate": 0.55
            },
            
            # Digital Art / NFTs
            "BLUE_CHIP_NFT": {
                "name": "Blue Chip NFT Index",
                "symbol": "BCNFT",
                "type": "Digital Art",
                "sub_type": "NFT Collection",
                "floor_price": 15000.00,
                "currency": "USD",
                "collection_size": 10000,
                "unique_holders": 5500,
                "liquidity": "Low",
                "min_investment": 15000,
                "volatility": 0.80,
                "correlation_to_equity": 0.20,
                "cultural_value": 0.85,
                "rarity_score": 0.75
            },
            "DIGITAL_ART_FUND": {
                "name": "Curated Digital Art Fund",
                "symbol": "CDAF",
                "type": "Digital Art",
                "sub_type": "Fund",
                "nav": 1250.00,
                "currency": "USD",
                "aum": 50000000,
                "pieces_owned": 250,
                "liquidity": "Very Low",
                "min_investment": 10000,
                "volatility": 0.60,
                "correlation_to_equity": 0.15,
                "curator_reputation": 0.90,
                "historical_returns": 0.25
            },
            
            # Physical Art
            "CONTEMPORARY_ART": {
                "name": "Contemporary Art Investment Trust",
                "symbol": "CAIT",
                "type": "Physical Art",
                "sub_type": "Fund",
                "nav": 5000.00,
                "currency": "USD",
                "aum": 200000000,
                "pieces_owned": 150,
                "liquidity": "Very Low",
                "min_investment": 50000,
                "volatility": 0.35,
                "correlation_to_equity": 0.10,
                "auction_performance": 0.70,
                "storage_cost": 0.02
            },
            
            # Commodities/Collectibles
            "RARE_WHISKY": {
                "name": "Rare Whisky Index Fund",
                "symbol": "RWIF",
                "type": "Collectibles",
                "sub_type": "Whisky",
                "nav": 2500.00,
                "currency": "GBP",
                "bottles_owned": 500,
                "avg_age": 25,
                "liquidity": "Very Low",
                "min_investment": 25000,
                "volatility": 0.25,
                "correlation_to_equity": 0.05,
                "appreciation_rate": 0.12,
                "storage_cost": 0.015
            },
            "CLASSIC_CARS": {
                "name": "Classic Car Investment Fund",
                "symbol": "CCIF",
                "type": "Collectibles",
                "sub_type": "Automobiles",
                "nav": 100000.00,
                "currency": "USD",
                "cars_owned": 25,
                "avg_vintage": 1965,
                "liquidity": "Very Low",
                "min_investment": 100000,
                "volatility": 0.30,
                "correlation_to_equity": 0.08,
                "condition_score": 0.85,
                "maintenance_cost": 0.03
            },
            
            # Private Equity / Venture
            "STARTUP_FUND": {
                "name": "Early Stage Startup Fund",
                "symbol": "ESSF",
                "type": "Private Equity",
                "sub_type": "Venture",
                "committed_capital": 100000000,
                "deployed_capital": 65000000,
                "portfolio_companies": 35,
                "liquidity": "Illiquid",
                "min_investment": 250000,
                "lock_in_period": 7,  # years
                "expected_irr": 0.25,
                "j_curve_position": -0.15,
                "success_rate": 0.10
            }
        }
        
        # Opportunity discovery parameters
        self.opportunity_metrics = {
            "market_inefficiency": 0.3,  # 0-1 scale
            "regulatory_changes": [],
            "emerging_trends": [],
            "valuation_gaps": {},
            "liquidity_events": []
        }
        
        # Liquidity management
        self.liquidity_buckets = {
            "immediate": 0.40,    # < 1 day
            "short_term": 0.30,   # 1-30 days
            "medium_term": 0.20,  # 30-180 days
            "long_term": 0.10     # > 180 days
        }
        
        # Performance tracking
        self.alternative_performance = {}
        self._initialize_performance()
        
        # Risk parameters
        self.risk_limits = {
            "max_alternatives_allocation": 0.30,  # 30% of portfolio
            "max_crypto_allocation": 0.10,
            "max_illiquid_allocation": 0.15,
            "min_liquidity_ratio": 0.60,
            "concentration_limit": 0.05  # Single alternative
        }
        
        # Emerging opportunities
        self.emerging_opportunities = []
        self._scan_for_opportunities()
        
    def _initialize_performance(self):
        """Initialize alternative performance tracking"""
        for alt_id, alt_data in self.alternatives.items():
            self.alternative_performance[alt_id] = {
                "current_price": alt_data.get("price", alt_data.get("nav", alt_data.get("floor_price", 0))),
                "daily_change": 0,
                "daily_change_percent": 0,
                "weekly_return": random.uniform(-5, 10),
                "monthly_return": random.uniform(-10, 20),
                "ytd_return": random.uniform(-20, 50),
                "sharpe_ratio": random.uniform(0.5, 2.5),
                "sortino_ratio": random.uniform(0.8, 3.0),
                "max_drawdown": random.uniform(-15, -40),
                "liquidity_score": self._calculate_liquidity_score(alt_data),
                "opportunity_score": random.uniform(0.4, 0.9)
            }
            
    def _scan_for_opportunities(self):
        """Scan for emerging investment opportunities"""
        self.emerging_opportunities = [
            {
                "id": "CARBON_CREDITS",
                "name": "Carbon Credit Trading Platform",
                "type": "Environmental",
                "opportunity": "New regulatory framework creating tradeable market",
                "expected_return": 0.15,
                "risk_level": "Medium",
                "time_horizon": "2-3 years",
                "min_investment": 50000,
                "liquidity": "Medium"
            },
            {
                "id": "METAVERSE_LAND",
                "name": "Virtual Real Estate in Gaming Metaverse",
                "type": "Digital Real Estate",
                "opportunity": "Major gaming platform launching property ownership",
                "expected_return": 0.35,
                "risk_level": "High",
                "time_horizon": "3-5 years",
                "min_investment": 5000,
                "liquidity": "Low"
            },
            {
                "id": "DEFI_YIELD",
                "name": "DeFi Yield Farming Strategy",
                "type": "Cryptocurrency",
                "opportunity": "High yield opportunities in decentralized finance",
                "expected_return": 0.20,
                "risk_level": "Very High",
                "time_horizon": "6-12 months",
                "min_investment": 10000,
                "liquidity": "High"
            },
            {
                "id": "INFRASTRUCTURE_INVIT",
                "name": "Infrastructure Investment Trust",
                "type": "InvIT",
                "opportunity": "Government privatization of toll roads",
                "expected_return": 0.12,
                "risk_level": "Low",
                "time_horizon": "5-10 years",
                "min_investment": 100000,
                "liquidity": "Medium"
            }
        ]
        
    async def analyze_alternative_multi_agent(self, alt_id: str) -> Dict[str, Any]:
        """Multi-agent analysis of an alternative investment"""
        alternative = self.alternatives.get(alt_id)
        if not alternative:
            return None
            
        performance = self.alternative_performance[alt_id]
        
        # Alternative Agent Analysis
        alt_analysis = await self._alternative_agent_analysis(alternative, performance)
        
        # Opportunity Agent Analysis
        opp_analysis = await self._opportunity_agent_analysis(alternative, performance)
        
        # Liquidity Agent Analysis
        liq_analysis = await self._liquidity_agent_analysis(alternative, performance)
        
        # Risk Agent Analysis
        risk_analysis = await self._risk_agent_analysis(alternative, performance)
        
        # Build consensus
        consensus = await self._build_alternative_consensus(
            alt_analysis, opp_analysis, liq_analysis, risk_analysis
        )
        
        return {
            "alternative_id": alt_id,
            "alternative_name": alternative["name"],
            "current_value": performance["current_price"],
            "daily_change": performance["daily_change_percent"],
            "agents": {
                "alternative": alt_analysis,
                "opportunity": opp_analysis,
                "liquidity": liq_analysis,
                "risk": risk_analysis
            },
            "consensus": consensus,
            "timestamp": datetime.now().isoformat()
        }
        
    async def _alternative_agent_analysis(self, alternative: Dict, performance: Dict) -> Dict[str, Any]:
        """Analyze alternative investment fundamentals"""
        # Type-specific analysis
        if alternative["type"] == "REIT":
            specific_analysis = {
                "dividend_yield": f"{alternative.get('dividend_yield', 0)}%",
                "discount_to_nav": f"{alternative.get('discount_to_nav', 0)}%",
                "income_stability": f"{alternative.get('income_stability', 0) * 100:.0f}%",
                "occupancy_trend": "Stable",  # Would be dynamic in real implementation
                "rental_growth": "3-5% annually"
            }
        elif alternative["type"] == "Cryptocurrency":
            specific_analysis = {
                "market_cap_rank": self._get_crypto_rank(alternative["symbol"]),
                "network_activity": "High" if alternative.get("network_effect", 0) > 0.7 else "Medium",
                "adoption_trend": "Growing" if alternative.get("adoption_rate", 0) > 0.6 else "Stable",
                "on_chain_metrics": "Bullish",
                "developer_activity": "Active"
            }
        elif alternative["type"] in ["Digital Art", "Physical Art"]:
            specific_analysis = {
                "cultural_significance": "High" if alternative.get("cultural_value", 0) > 0.7 else "Medium",
                "artist_trajectory": "Rising",
                "market_liquidity": alternative["liquidity"],
                "authentication": "Verified",
                "provenance": "Clear"
            }
        else:
            specific_analysis = {
                "asset_quality": "Premium",
                "market_position": "Strong",
                "management_quality": "Experienced"
            }
            
        return {
            "asset_type": alternative["type"],
            "sub_type": alternative.get("sub_type", "General"),
            "performance_ytd": f"{performance['ytd_return']:.1f}%",
            "sharpe_ratio": f"{performance['sharpe_ratio']:.2f}",
            "correlation_to_equity": f"{alternative.get('correlation_to_equity', 0):.2f}",
            "volatility": f"{alternative.get('volatility', 0) * 100:.0f}%",
            **specific_analysis,
            "valuation": self._assess_valuation(alternative, performance),
            "recommendation": self._get_alt_recommendation(performance)
        }
        
    async def _opportunity_agent_analysis(self, alternative: Dict, performance: Dict) -> Dict[str, Any]:
        """Analyze investment opportunities and emerging trends"""
        # Opportunity scoring
        opportunity_score = performance["opportunity_score"]
        
        # Market inefficiencies
        inefficiencies = self._identify_inefficiencies(alternative)
        
        # Growth catalysts
        catalysts = self._identify_catalysts(alternative)
        
        # Competitive advantages
        advantages = self._assess_advantages(alternative)
        
        return {
            "opportunity_score": f"{opportunity_score:.2f}/1.0",
            "market_inefficiency": inefficiencies,
            "growth_catalysts": catalysts,
            "time_horizon": self._get_investment_horizon(alternative),
            "expected_return": f"{self._calculate_expected_return(alternative, performance):.1f}%",
            "risk_reward_ratio": f"{self._calculate_risk_reward(alternative, performance):.2f}",
            "competitive_advantages": advantages,
            "market_timing": self._assess_market_timing(alternative),
            "emerging_trends": self._relevant_trends(alternative["type"])
        }
        
    async def _liquidity_agent_analysis(self, alternative: Dict, performance: Dict) -> Dict[str, Any]:
        """Analyze liquidity profile and management"""
        # Liquidity scoring
        liquidity_score = performance["liquidity_score"]
        
        # Exit options
        exit_options = self._identify_exit_options(alternative)
        
        # Liquidity timeline
        liquidity_timeline = self._estimate_liquidity_timeline(alternative)
        
        # Secondary market
        secondary_market = self._assess_secondary_market(alternative)
        
        return {
            "liquidity_score": f"{liquidity_score:.2f}/10",
            "liquidity_category": alternative.get("liquidity", "Unknown"),
            "days_to_liquidate": liquidity_timeline,
            "exit_options": exit_options,
            "secondary_market": secondary_market,
            "bid_ask_spread": self._estimate_spread(alternative),
            "market_depth": self._assess_market_depth(alternative),
            "lock_in_period": f"{alternative.get('lock_in_period', 0)} years" if alternative.get('lock_in_period') else "None",
            "redemption_terms": self._get_redemption_terms(alternative)
        }
        
    async def _risk_agent_analysis(self, alternative: Dict, performance: Dict) -> Dict[str, Any]:
        """Analyze risks specific to alternative investments"""
        # Risk scoring
        risk_score = self._calculate_risk_score(alternative, performance)
        
        # Specific risks
        specific_risks = self._identify_specific_risks(alternative)
        
        # Regulatory risks
        regulatory_risks = self._assess_regulatory_risks(alternative)
        
        # Counterparty risks
        counterparty_risks = self._assess_counterparty_risks(alternative)
        
        return {
            "overall_risk_score": f"{risk_score:.1f}/10",
            "volatility_percentile": self._get_volatility_percentile(alternative["volatility"]),
            "max_drawdown": f"{performance['max_drawdown']:.1f}%",
            "specific_risks": specific_risks,
            "regulatory_risks": regulatory_risks,
            "counterparty_risks": counterparty_risks,
            "concentration_risk": self._assess_concentration_risk(alternative),
            "currency_risk": "High" if alternative.get("currency") not in ["INR", "USD"] else "Low",
            "operational_risks": self._assess_operational_risks(alternative)
        }
        
    async def _build_alternative_consensus(self, alt: Dict, opp: Dict, liq: Dict, risk: Dict) -> Dict[str, Any]:
        """Build multi-agent consensus for alternative investment"""
        scores = []
        
        # Alternative score (fundamentals)
        alt_score = 0.8 if alt["valuation"] == "Undervalued" else \
                   0.6 if alt["valuation"] == "Fair" else 0.4
        scores.append(alt_score)
        
        # Opportunity score
        opp_score = float(opp["opportunity_score"].split("/")[0])
        scores.append(opp_score)
        
        # Liquidity score (inverse weight for alternatives)
        liq_score = float(liq["liquidity_score"].split("/")[0]) / 10
        # Lower weight for liquidity in alternatives
        scores.append(liq_score * 0.5)
        
        # Risk score (inverse)
        risk_score = 1 - (float(risk["overall_risk_score"].split("/")[0]) / 10)
        scores.append(risk_score)
        
        # Weighted consensus
        weights = [1.2, 1.5, 0.5, 0.8]  # Opportunity weighted highest
        weighted_score = sum(s * w for s, w in zip(scores, weights)) / sum(weights)
        
        # Determine action
        if weighted_score > 0.7:
            action = "INVEST"
            recommendation = "Strong opportunity with acceptable risks"
        elif weighted_score > 0.55:
            action = "ACCUMULATE"
            recommendation = "Gradually build position"
        elif weighted_score > 0.45:
            action = "HOLD"
            recommendation = "Monitor for better entry"
        else:
            action = "AVOID"
            recommendation = "Risks outweigh opportunities"
            
        # Allocation recommendation
        allocation = self._recommend_allocation(alt["asset_type"], weighted_score)
        
        return {
            "action": action,
            "confidence": f"{weighted_score * 100:.0f}%",
            "recommendation": recommendation,
            "allocation_recommendation": f"{allocation:.1f}%",
            "key_factors": self._identify_key_factors(alt, opp, liq, risk),
            "risks": self._summarize_risks(risk),
            "exit_strategy": self._recommend_exit_strategy(liq),
            "alternatives": self._suggest_similar_alternatives(alt["asset_type"])
        }
        
    def _calculate_liquidity_score(self, alternative: Dict) -> float:
        """Calculate liquidity score for an alternative"""
        liquidity_map = {
            "Very High": 10,
            "High": 8,
            "Medium": 6,
            "Low": 4,
            "Very Low": 2,
            "Illiquid": 0
        }
        
        base_score = liquidity_map.get(alternative.get("liquidity", "Unknown"), 5)
        
        # Adjustments
        if alternative["type"] == "Cryptocurrency":
            base_score = min(10, base_score + 2)  # Crypto generally more liquid
        elif alternative["type"] in ["Physical Art", "Collectibles"]:
            base_score = max(0, base_score - 2)  # Physical assets less liquid
            
        return base_score
        
    def _get_crypto_rank(self, symbol: str) -> str:
        """Get cryptocurrency market cap ranking"""
        ranks = {
            "BTC": "1st",
            "ETH": "2nd",
            "SOL": "Top 10"
        }
        return ranks.get(symbol, "Top 100")
        
    def _assess_valuation(self, alternative: Dict, performance: Dict) -> str:
        """Assess valuation of alternative investment"""
        if alternative["type"] == "REIT":
            if alternative.get("discount_to_nav", 0) < -15:
                return "Undervalued"
            elif alternative.get("discount_to_nav", 0) < -5:
                return "Fair"
            else:
                return "Overvalued"
        elif alternative["type"] == "Cryptocurrency":
            # Simplified - would use on-chain metrics in reality
            if performance["ytd_return"] < -30:
                return "Oversold"
            elif performance["ytd_return"] > 100:
                return "Overbought"
            else:
                return "Fair"
        else:
            return "Fair"
            
    def _get_alt_recommendation(self, performance: Dict) -> str:
        """Get recommendation based on performance"""
        if performance["sharpe_ratio"] > 2 and performance["ytd_return"] > 20:
            return "Strong Buy"
        elif performance["sharpe_ratio"] > 1.5:
            return "Buy"
        elif performance["sharpe_ratio"] > 1:
            return "Hold"
        else:
            return "Review"
            
    def _identify_inefficiencies(self, alternative: Dict) -> List[str]:
        """Identify market inefficiencies"""
        inefficiencies = []
        
        if alternative["type"] == "REIT" and alternative.get("discount_to_nav", 0) < -15:
            inefficiencies.append("Trading below NAV")
        if alternative.get("liquidity") in ["Low", "Very Low"] and alternative.get("volatility", 0) < 0.3:
            inefficiencies.append("Liquidity premium available")
        if alternative["type"] == "Cryptocurrency" and alternative.get("adoption_rate", 0) < 0.5:
            inefficiencies.append("Early adoption phase")
            
        return inefficiencies[:2]
        
    def _identify_catalysts(self, alternative: Dict) -> List[str]:
        """Identify growth catalysts"""
        catalysts = []
        
        if alternative["type"] == "REIT":
            catalysts.append("Economic recovery driving occupancy")
            catalysts.append("Interest rate stabilization")
        elif alternative["type"] == "Cryptocurrency":
            catalysts.append("Institutional adoption increasing")
            catalysts.append("Regulatory clarity improving")
        elif alternative["type"] in ["Digital Art", "Physical Art"]:
            catalysts.append("Growing collector base")
            catalysts.append("Digital authentication standards")
            
        return catalysts[:2]
        
    def _assess_advantages(self, alternative: Dict) -> List[str]:
        """Assess competitive advantages"""
        advantages = []
        
        if alternative.get("income_stability", 0) > 0.8:
            advantages.append("Stable income generation")
        if alternative.get("correlation_to_equity", 1) < 0.3:
            advantages.append("Low correlation to traditional assets")
        if alternative.get("network_effect", 0) > 0.8:
            advantages.append("Strong network effects")
            
        return advantages
        
    def _get_investment_horizon(self, alternative: Dict) -> str:
        """Get recommended investment horizon"""
        if alternative.get("lock_in_period"):
            return f"{alternative['lock_in_period']} years (locked)"
        elif alternative["type"] in ["Physical Art", "Collectibles"]:
            return "5-10 years"
        elif alternative["type"] == "Cryptocurrency":
            return "1-3 years"
        elif alternative["type"] == "REIT":
            return "3-5 years"
        else:
            return "3-7 years"
            
    def _calculate_expected_return(self, alternative: Dict, performance: Dict) -> float:
        """Calculate expected return"""
        base_return = performance["ytd_return"] * 0.5  # Mean reversion
        
        # Type-specific adjustments
        if alternative["type"] == "REIT":
            base_return = alternative.get("dividend_yield", 0) + 3  # Capital appreciation
        elif alternative["type"] == "Cryptocurrency":
            base_return = base_return * 0.7  # High volatility adjustment
            
        return max(-20, min(50, base_return))
        
    def _calculate_risk_reward(self, alternative: Dict, performance: Dict) -> float:
        """Calculate risk-reward ratio"""
        expected_return = self._calculate_expected_return(alternative, performance)
        risk = alternative.get("volatility", 0.5) * 100
        
        if risk > 0:
            return expected_return / risk
        return 0
        
    def _assess_market_timing(self, alternative: Dict) -> str:
        """Assess market timing"""
        if alternative["type"] == "REIT":
            return "Favorable - interest rates stabilizing"
        elif alternative["type"] == "Cryptocurrency":
            return "Accumulation phase"
        else:
            return "Neutral timing"
            
    def _relevant_trends(self, asset_type: str) -> List[str]:
        """Get relevant trends for asset type"""
        trends = {
            "REIT": ["Remote work stabilization", "Urban revival"],
            "Cryptocurrency": ["DeFi growth", "CBDC development"],
            "Digital Art": ["Metaverse expansion", "Creator economy"],
            "Physical Art": ["Wealth preservation demand", "Asian collector growth"],
            "Private Equity": ["Tech disruption", "ESG focus"]
        }
        return trends.get(asset_type, ["Diversification demand"])
        
    def _identify_exit_options(self, alternative: Dict) -> List[str]:
        """Identify exit options"""
        options = []
        
        if alternative.get("liquidity") in ["Very High", "High"]:
            options.append("Market sale anytime")
        if alternative["type"] == "REIT":
            options.append("Exchange trading")
        elif alternative["type"] in ["Digital Art", "Physical Art"]:
            options.append("Auction house sale")
            options.append("Private sale")
        elif alternative["type"] == "Private Equity":
            options.append("Secondary market")
            options.append("IPO exit")
            
        return options[:3]
        
    def _estimate_liquidity_timeline(self, alternative: Dict) -> str:
        """Estimate time to liquidate"""
        liquidity_timeline = {
            "Very High": "< 1 day",
            "High": "1-3 days",
            "Medium": "3-30 days",
            "Low": "30-90 days",
            "Very Low": "90-180 days",
            "Illiquid": "> 180 days"
        }
        return liquidity_timeline.get(alternative.get("liquidity", "Unknown"), "Unknown")
        
    def _assess_secondary_market(self, alternative: Dict) -> str:
        """Assess secondary market depth"""
        if alternative["type"] in ["REIT", "Cryptocurrency"]:
            return "Deep and active"
        elif alternative["type"] == "Private Equity":
            return "Growing but limited"
        elif alternative["type"] in ["Digital Art", "Physical Art"]:
            return "Specialist market"
        else:
            return "Limited"
            
    def _estimate_spread(self, alternative: Dict) -> str:
        """Estimate bid-ask spread"""
        if alternative["type"] == "Cryptocurrency":
            return "0.1-0.5%"
        elif alternative["type"] == "REIT":
            return "0.5-1%"
        elif alternative["type"] in ["Digital Art", "Physical Art"]:
            return "5-15%"
        else:
            return "10-20%"
            
    def _assess_market_depth(self, alternative: Dict) -> str:
        """Assess market depth"""
        if alternative.get("liquidity") in ["Very High", "High"]:
            return "Deep"
        elif alternative.get("liquidity") == "Medium":
            return "Moderate"
        else:
            return "Shallow"
            
    def _get_redemption_terms(self, alternative: Dict) -> str:
        """Get redemption terms"""
        if alternative["type"] == "Private Equity":
            return "Quarterly with 90-day notice"
        elif alternative["type"] == "REIT":
            return "Daily trading"
        else:
            return "Subject to buyer availability"
            
    def _calculate_risk_score(self, alternative: Dict, performance: Dict) -> float:
        """Calculate overall risk score"""
        volatility_risk = alternative.get("volatility", 0.5) * 10
        liquidity_risk = (10 - performance["liquidity_score"]) / 2
        drawdown_risk = abs(performance["max_drawdown"]) / 10
        
        return min(10, (volatility_risk + liquidity_risk + drawdown_risk) / 3)
        
    def _get_volatility_percentile(self, volatility: float) -> str:
        """Get volatility percentile"""
        if volatility < 0.2:
            return "Bottom 25%"
        elif volatility < 0.4:
            return "25-50%"
        elif volatility < 0.6:
            return "50-75%"
        else:
            return "Top 25%"
            
    def _identify_specific_risks(self, alternative: Dict) -> List[str]:
        """Identify asset-specific risks"""
        risks = []
        
        if alternative["type"] == "REIT":
            risks.append("Interest rate sensitivity")
            risks.append("Occupancy risk")
        elif alternative["type"] == "Cryptocurrency":
            risks.append("Regulatory uncertainty")
            risks.append("Technology risk")
        elif alternative["type"] in ["Digital Art", "Physical Art"]:
            risks.append("Valuation subjectivity")
            risks.append("Storage/preservation risk")
        elif alternative["type"] == "Private Equity":
            risks.append("J-curve effect")
            risks.append("Key person risk")
            
        return risks[:2]
        
    def _assess_regulatory_risks(self, alternative: Dict) -> str:
        """Assess regulatory risks"""
        risk_levels = {
            "REIT": "Low - Well regulated",
            "Cryptocurrency": "High - Evolving regulations",
            "Digital Art": "Medium - Tax treatment unclear",
            "Physical Art": "Low - Established framework",
            "Private Equity": "Medium - Increasing scrutiny"
        }
        return risk_levels.get(alternative["type"], "Medium")
        
    def _assess_counterparty_risks(self, alternative: Dict) -> str:
        """Assess counterparty risks"""
        if alternative["type"] == "Cryptocurrency":
            return "Exchange/wallet risk"
        elif alternative["type"] == "REIT":
            return "Management quality risk"
        elif alternative["type"] in ["Digital Art", "Physical Art"]:
            return "Authentication/storage provider risk"
        else:
            return "Fund manager risk"
            
    def _assess_concentration_risk(self, alternative: Dict) -> str:
        """Assess concentration risk"""
        if alternative.get("min_investment", 0) > 100000:
            return "High - Large minimum investment"
        elif alternative["type"] == "Private Equity":
            return "Medium - Limited diversification"
        else:
            return "Low - Can diversify"
            
    def _assess_operational_risks(self, alternative: Dict) -> List[str]:
        """Assess operational risks"""
        risks = []
        
        if alternative.get("storage_cost", 0) > 0:
            risks.append("Storage and insurance costs")
        if alternative.get("maintenance_cost", 0) > 0:
            risks.append("Ongoing maintenance required")
        if alternative["type"] == "Cryptocurrency":
            risks.append("Custody and key management")
            
        return risks
        
    def _recommend_allocation(self, asset_type: str, score: float) -> float:
        """Recommend allocation percentage"""
        base_allocation = {
            "REIT": 10,
            "Cryptocurrency": 5,
            "Digital Art": 3,
            "Physical Art": 5,
            "Private Equity": 10,
            "Collectibles": 3
        }
        
        base = base_allocation.get(asset_type, 5)
        
        # Adjust based on score
        if score > 0.7:
            return min(self.risk_limits["concentration_limit"] * 100, base * 1.5)
        elif score > 0.55:
            return base
        else:
            return base * 0.5
            
    def _identify_key_factors(self, alt: Dict, opp: Dict, liq: Dict, risk: Dict) -> List[str]:
        """Identify key decision factors"""
        factors = []
        
        if float(opp["opportunity_score"].split("/")[0]) > 0.8:
            factors.append("High opportunity score")
        if alt["valuation"] == "Undervalued":
            factors.append("Attractive valuation")
        if float(risk["overall_risk_score"].split("/")[0]) < 5:
            factors.append("Acceptable risk level")
        if liq["liquidity_category"] in ["High", "Very High"]:
            factors.append("Good liquidity")
            
        return factors[:3]
        
    def _summarize_risks(self, risk: Dict) -> List[str]:
        """Summarize key risks"""
        risks = risk["specific_risks"].copy()
        
        if "High" in risk["regulatory_risks"]:
            risks.append("Regulatory uncertainty")
        if float(risk["overall_risk_score"].split("/")[0]) > 7:
            risks.append("High overall risk")
            
        return risks[:3]
        
    def _recommend_exit_strategy(self, liq: Dict) -> str:
        """Recommend exit strategy"""
        if liq["liquidity_category"] in ["Very High", "High"]:
            return "Market sale with trailing stop"
        elif "Auction house" in str(liq["exit_options"]):
            return "Planned auction after value appreciation"
        elif liq.get("lock_in_period", "None") != "None":
            return f"Hold until lock-in expires, then reassess"
        else:
            return "Gradual exit over 3-6 months"
            
    def _suggest_similar_alternatives(self, asset_type: str) -> List[str]:
        """Suggest similar alternative investments"""
        suggestions = {
            "REIT": ["InvIT funds", "Real estate mutual funds"],
            "Cryptocurrency": ["Crypto index funds", "DeFi protocols"],
            "Digital Art": ["NFT funds", "Metaverse assets"],
            "Physical Art": ["Art funds", "Wine investment"],
            "Private Equity": ["Venture debt", "Growth equity"]
        }
        return suggestions.get(asset_type, ["Diversified alternative fund"])[:2]
        
    def update_prices(self):
        """Update alternative investment prices"""
        for alt_id, performance in self.alternative_performance.items():
            alternative = self.alternatives[alt_id]
            
            # Base price movement based on volatility
            volatility = alternative.get("volatility", 0.3)
            daily_move = random.gauss(0, volatility / math.sqrt(252))
            
            # Type-specific adjustments
            if alternative["type"] == "Cryptocurrency":
                # Crypto more volatile on weekends
                if datetime.now().weekday() >= 5:
                    daily_move *= 1.5
            elif alternative["type"] == "REIT":
                # REITs influenced by interest rates
                if random.random() < 0.1:  # 10% chance of rate news
                    daily_move += random.uniform(-0.02, 0.02)
                    
            # Apply price change
            old_price = performance["current_price"]
            new_price = old_price * (1 + daily_move)
            
            performance["current_price"] = new_price
            performance["daily_change"] = new_price - old_price
            performance["daily_change_percent"] = daily_move * 100
            
            # Update returns
            performance["weekly_return"] = performance["weekly_return"] * 0.8 + daily_move * 100 * 2
            performance["monthly_return"] = performance["monthly_return"] * 0.95 + daily_move * 100
            performance["ytd_return"] = performance["ytd_return"] + daily_move * 100 * 0.1
            
    async def discover_opportunities(self, portfolio_profile: Dict) -> List[Dict[str, Any]]:
        """Discover new investment opportunities based on portfolio profile"""
        discovered = []
        
        # Check each emerging opportunity
        for opportunity in self.emerging_opportunities:
            score = self._score_opportunity(opportunity, portfolio_profile)
            
            if score > 0.6:
                discovered.append({
                    **opportunity,
                    "fit_score": score,
                    "recommendation": self._recommend_opportunity_action(opportunity, score),
                    "allocation_suggestion": self._suggest_opportunity_allocation(opportunity, portfolio_profile)
                })
                
        # Sort by fit score
        discovered.sort(key=lambda x: x["fit_score"], reverse=True)
        
        return discovered[:5]  # Top 5 opportunities
        
    def _score_opportunity(self, opportunity: Dict, profile: Dict) -> float:
        """Score opportunity based on portfolio profile"""
        score = 0.5  # Base score
        
        # Risk alignment
        risk_tolerance = profile.get("risk_tolerance", "medium")
        if risk_tolerance == "high" and opportunity["risk_level"] in ["High", "Very High"]:
            score += 0.2
        elif risk_tolerance == "low" and opportunity["risk_level"] == "Low":
            score += 0.2
            
        # Return expectations
        if opportunity["expected_return"] > profile.get("target_return", 0.10):
            score += 0.1
            
        # Liquidity needs
        if profile.get("liquidity_preference", "medium") == "high" and opportunity["liquidity"] in ["High", "Medium"]:
            score += 0.1
            
        # Time horizon match
        portfolio_horizon = profile.get("time_horizon", 5)
        opp_horizon = int(opportunity["time_horizon"].split("-")[0])
        if abs(portfolio_horizon - opp_horizon) < 2:
            score += 0.1
            
        return min(1.0, score)
        
    def _recommend_opportunity_action(self, opportunity: Dict, score: float) -> str:
        """Recommend action for opportunity"""
        if score > 0.8:
            return "High priority - allocate immediately"
        elif score > 0.6:
            return "Consider allocation"
        else:
            return "Monitor for improvements"
            
    def _suggest_opportunity_allocation(self, opportunity: Dict, profile: Dict) -> str:
        """Suggest allocation for opportunity"""
        portfolio_size = profile.get("portfolio_size", 10000000)
        min_investment = opportunity["min_investment"]
        
        # Calculate as percentage of alternatives allocation
        max_alternatives = portfolio_size * self.risk_limits["max_alternatives_allocation"]
        
        if opportunity["risk_level"] in ["High", "Very High"]:
            suggested = min(max_alternatives * 0.05, min_investment * 2)
        else:
            suggested = min(max_alternatives * 0.10, min_investment * 3)
            
        return f"₹{suggested:,.0f} ({(suggested/portfolio_size)*100:.1f}% of portfolio)"
        
    async def manage_liquidity(self, portfolio: Dict) -> Dict[str, Any]:
        """Manage liquidity across alternative investments"""
        positions = portfolio.get("alternative_positions", [])
        
        # Calculate current liquidity profile
        liquidity_profile = self._calculate_liquidity_profile(positions)
        
        # Check against target buckets
        rebalancing_needed = self._check_liquidity_rebalancing(liquidity_profile)
        
        # Generate rebalancing recommendations
        if rebalancing_needed:
            recommendations = self._generate_liquidity_recommendations(positions, liquidity_profile)
        else:
            recommendations = []
            
        return {
            "current_liquidity_profile": liquidity_profile,
            "target_buckets": self.liquidity_buckets,
            "rebalancing_needed": rebalancing_needed,
            "recommendations": recommendations,
            "liquidity_score": self._calculate_portfolio_liquidity_score(liquidity_profile),
            "stress_liquidity": self._calculate_stress_liquidity(positions)
        }
        
    def _calculate_liquidity_profile(self, positions: List[Dict]) -> Dict[str, float]:
        """Calculate current liquidity profile"""
        total_value = sum(p["current_value"] for p in positions)
        
        buckets = {
            "immediate": 0,
            "short_term": 0,
            "medium_term": 0,
            "long_term": 0
        }
        
        for position in positions:
            alternative = self.alternatives.get(position["alternative_id"])
            if not alternative:
                continue
                
            value = position["current_value"]
            liquidity = alternative.get("liquidity", "Unknown")
            
            if liquidity in ["Very High", "High"]:
                buckets["immediate"] += value
            elif liquidity == "Medium":
                buckets["short_term"] += value
            elif liquidity == "Low":
                buckets["medium_term"] += value
            else:
                buckets["long_term"] += value
                
        # Normalize to percentages
        if total_value > 0:
            for bucket in buckets:
                buckets[bucket] = buckets[bucket] / total_value
                
        return buckets
        
    def _check_liquidity_rebalancing(self, current_profile: Dict) -> bool:
        """Check if liquidity rebalancing is needed"""
        for bucket, target in self.liquidity_buckets.items():
            if abs(current_profile.get(bucket, 0) - target) > 0.1:  # 10% tolerance
                return True
        return False
        
    def _generate_liquidity_recommendations(self, positions: List[Dict], current_profile: Dict) -> List[Dict]:
        """Generate liquidity rebalancing recommendations"""
        recommendations = []
        
        # Identify over/under allocated buckets
        for bucket, target in self.liquidity_buckets.items():
            current = current_profile.get(bucket, 0)
            
            if current > target + 0.1:
                # Need to reduce this bucket
                recommendations.append({
                    "action": "Reduce",
                    "bucket": bucket,
                    "current": f"{current*100:.1f}%",
                    "target": f"{target*100:.1f}%",
                    "suggestion": f"Sell liquid assets in {bucket} category"
                })
            elif current < target - 0.1:
                # Need to increase this bucket
                recommendations.append({
                    "action": "Increase",
                    "bucket": bucket,
                    "current": f"{current*100:.1f}%",
                    "target": f"{target*100:.1f}%",
                    "suggestion": f"Add more liquid assets to {bucket} category"
                })
                
        return recommendations
        
    def _calculate_portfolio_liquidity_score(self, profile: Dict) -> float:
        """Calculate overall portfolio liquidity score"""
        # Weighted score based on ability to access funds quickly
        score = (
            profile.get("immediate", 0) * 10 +
            profile.get("short_term", 0) * 7 +
            profile.get("medium_term", 0) * 4 +
            profile.get("long_term", 0) * 1
        )
        return round(score, 1)
        
    def _calculate_stress_liquidity(self, positions: List[Dict]) -> Dict[str, Any]:
        """Calculate liquidity under stress conditions"""
        # Assume 50% haircut on illiquid assets
        stress_value = 0
        
        for position in positions:
            alternative = self.alternatives.get(position["alternative_id"])
            if not alternative:
                continue
                
            value = position["current_value"]
            liquidity = alternative.get("liquidity", "Unknown")
            
            if liquidity in ["Very High", "High"]:
                stress_value += value * 0.95
            elif liquidity == "Medium":
                stress_value += value * 0.80
            elif liquidity == "Low":
                stress_value += value * 0.60
            else:
                stress_value += value * 0.40
                
        total_value = sum(p["current_value"] for p in positions)
        
        return {
            "normal_value": total_value,
            "stress_value": stress_value,
            "haircut": total_value - stress_value,
            "stress_ratio": stress_value / total_value if total_value > 0 else 0
        } 