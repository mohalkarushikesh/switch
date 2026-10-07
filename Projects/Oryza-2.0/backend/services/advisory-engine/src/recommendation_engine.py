"""
Recommendation Engine - Generates personalized investment recommendations
"""
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime
import numpy as np
import logging
import uuid

from .models import Recommendation, RecommendationType


class RecommendationEngine:
    """
    Generates personalized investment recommendations using ML and analytics
    """
    
    def __init__(self):
        self.logger = logging.getLogger("recommendation_engine")
        self.recommendation_models = {}
        self.is_initialized = False
        
    async def initialize(self):
        """Initialize the recommendation engine"""
        self.logger.info("Initializing Recommendation Engine")
        # In production, load ML models
        await asyncio.sleep(0.1)  # Simulate initialization
        self.is_initialized = True
        
    async def generate_recommendations(
        self,
        portfolio_analysis: Dict[str, Any],
        market_conditions: Dict[str, Any],
        user_profile: Any
    ) -> List[Dict[str, Any]]:
        """Generate recommendations based on analysis and market conditions"""
        recommendations = []
        
        # Rebalancing recommendations
        rebalancing_recs = await self._generate_rebalancing_recommendations(
            portfolio_analysis
        )
        recommendations.extend(rebalancing_recs)
        
        # New opportunity recommendations
        opportunity_recs = await self._generate_opportunity_recommendations(
            market_conditions, user_profile
        )
        recommendations.extend(opportunity_recs)
        
        # Risk mitigation recommendations
        if portfolio_analysis.get("risk_score", 0) > 60:
            risk_recs = await self._generate_risk_recommendations(
                portfolio_analysis
            )
            recommendations.extend(risk_recs)
        
        # Sort by confidence score
        recommendations.sort(key=lambda x: x["confidence_score"], reverse=True)
        
        return recommendations[:10]  # Top 10 recommendations
        
    async def get_recommendations(
        self,
        user_id: str,
        recommendation_type: Optional[str] = None,
        filters: Dict[str, Any] = {},
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get filtered recommendations for user"""
        # In production, fetch from recommendation database
        all_recommendations = await self._fetch_user_recommendations(user_id)
        
        # Filter by type if specified
        if recommendation_type:
            all_recommendations = [
                r for r in all_recommendations 
                if r["type"] == recommendation_type
            ]
        
        # Apply additional filters
        for key, value in filters.items():
            if key == "asset_class":
                all_recommendations = [
                    r for r in all_recommendations
                    if r.get("asset_class") == value
                ]
            elif key == "min_confidence":
                all_recommendations = [
                    r for r in all_recommendations
                    if r.get("confidence_score", 0) >= value
                ]
        
        return all_recommendations[:limit]
        
    async def _generate_rebalancing_recommendations(
        self,
        portfolio_analysis: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate rebalancing recommendations"""
        recommendations = []
        
        for allocation in portfolio_analysis.get("asset_allocation", []):
            if abs(allocation["deviation"]) > 5:  # 5% deviation threshold
                if allocation["deviation"] > 0:
                    # Overweight - recommend selling
                    recommendations.append(self._create_recommendation(
                        type=RecommendationType.SELL,
                        symbol=f"{allocation['asset_class']}_ETF",
                        asset_name=f"{allocation['asset_class']} ETF",
                        asset_class=allocation["asset_class"],
                        action=f"Reduce {allocation['asset_class']} allocation by {allocation['deviation']:.1f}%",
                        rationale=f"{allocation['asset_class']} is overweight by {allocation['deviation']:.1f}%",
                        confidence_score=85,
                        expected_impact={
                            "risk_reduction": "Medium",
                            "return_impact": "Neutral"
                        }
                    ))
                else:
                    # Underweight - recommend buying
                    recommendations.append(self._create_recommendation(
                        type=RecommendationType.BUY,
                        symbol=f"{allocation['asset_class']}_ETF",
                        asset_name=f"{allocation['asset_class']} ETF",
                        asset_class=allocation["asset_class"],
                        action=f"Increase {allocation['asset_class']} allocation by {abs(allocation['deviation']):.1f}%",
                        rationale=f"{allocation['asset_class']} is underweight by {abs(allocation['deviation']):.1f}%",
                        confidence_score=85,
                        expected_impact={
                            "diversification": "Improved",
                            "return_impact": "Positive"
                        }
                    ))
        
        return recommendations
        
    async def _generate_opportunity_recommendations(
        self,
        market_conditions: Dict[str, Any],
        user_profile: Any
    ) -> List[Dict[str, Any]]:
        """Generate new opportunity recommendations"""
        recommendations = []
        
        # Mock opportunities based on market conditions
        opportunities = [
            {
                "symbol": "NVDA",
                "name": "NVIDIA Corporation",
                "class": "equity",
                "sector": "Technology",
                "thesis": "AI leadership position with strong growth",
                "target_return": 25
            },
            {
                "symbol": "ICLN",
                "name": "iShares Global Clean Energy ETF",
                "class": "etf",
                "sector": "Clean Energy",
                "thesis": "Clean energy transition accelerating globally",
                "target_return": 20
            },
            {
                "symbol": "SCHD",
                "name": "Schwab US Dividend Equity ETF",
                "class": "etf",
                "sector": "Dividend",
                "thesis": "Quality dividend stocks for income generation",
                "target_return": 12
            }
        ]
        
        # Filter based on user risk tolerance
        risk_map = {
            "conservative": 10,
            "moderate": 15,
            "aggressive": 25,
            "very_aggressive": 35
        }
        
        max_return = risk_map.get(user_profile.risk_tolerance, 15)
        
        for opp in opportunities:
            if opp["target_return"] <= max_return:
                recommendations.append(self._create_recommendation(
                    type=RecommendationType.NEW_OPPORTUNITY,
                    symbol=opp["symbol"],
                    asset_name=opp["name"],
                    asset_class=opp["class"],
                    action=f"Consider adding {opp['symbol']} to portfolio",
                    rationale=opp["thesis"],
                    confidence_score=75 + np.random.uniform(-10, 10),
                    expected_impact={
                        "expected_return": f"{opp['target_return']}%",
                        "sector_exposure": opp["sector"],
                        "diversification": "Positive"
                    },
                    current_price=100 * (1 + np.random.uniform(-0.1, 0.1))
                ))
        
        return recommendations
        
    async def _generate_risk_recommendations(
        self,
        portfolio_analysis: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate risk mitigation recommendations"""
        recommendations = []
        
        # Hedging recommendation
        recommendations.append(self._create_recommendation(
            type=RecommendationType.RISK_MITIGATION,
            symbol="SPY_PUT",
            asset_name="S&P 500 Put Options",
            asset_class="derivatives",
            action="Consider portfolio hedging with put options",
            rationale="Portfolio risk is elevated; protective puts can limit downside",
            confidence_score=70,
            expected_impact={
                "max_loss_reduction": "15%",
                "cost": "1-2% annually",
                "protection_level": "High"
            }
        ))
        
        # Defensive asset recommendation
        recommendations.append(self._create_recommendation(
            type=RecommendationType.BUY,
            symbol="AGG",
            asset_name="iShares Core US Aggregate Bond ETF",
            asset_class="fixed_income",
            action="Increase defensive allocation with bonds",
            rationale="Add stability to portfolio during volatile markets",
            confidence_score=80,
            expected_impact={
                "volatility_reduction": "20%",
                "expected_return": "3-4%",
                "correlation": "Low with equities"
            }
        ))
        
        return recommendations
        
    def _create_recommendation(
        self,
        type: RecommendationType,
        symbol: str,
        asset_name: str,
        asset_class: str,
        action: str,
        rationale: str,
        confidence_score: float,
        expected_impact: Dict[str, Any],
        current_price: float = 100,
        quantity: Optional[float] = None,
        target_price: Optional[float] = None
    ) -> Dict[str, Any]:
        """Create a recommendation object"""
        return {
            "id": str(uuid.uuid4()),
            "type": type,
            "symbol": symbol,
            "asset_name": asset_name,
            "asset_class": asset_class,
            "action": action,
            "rationale": rationale,
            "confidence_score": confidence_score,
            "expected_impact": expected_impact,
            "current_price": current_price,
            "quantity": quantity,
            "target_price": target_price or current_price * 1.1,
            "time_horizon": "3-6 months",
            "risks": self._identify_recommendation_risks(type, asset_class),
            "created_at": datetime.now()
        }
        
    def _identify_recommendation_risks(
        self,
        rec_type: RecommendationType,
        asset_class: str
    ) -> List[str]:
        """Identify risks for recommendation"""
        risks = []
        
        # General risks
        risks.append("Market conditions may change")
        
        # Type-specific risks
        if rec_type == RecommendationType.NEW_OPPORTUNITY:
            risks.append("New position may increase portfolio risk")
            
        if asset_class == "equity":
            risks.append("Subject to market volatility")
            risks.append("Company-specific risks apply")
        elif asset_class == "fixed_income":
            risks.append("Interest rate risk")
            risks.append("Credit risk")
        elif asset_class == "derivatives":
            risks.append("Time decay risk")
            risks.append("Leverage risk")
            
        return risks
        
    async def _fetch_user_recommendations(self, user_id: str) -> List[Dict[str, Any]]:
        """Fetch recommendations for user from database"""
        # In production, query recommendation database
        # Mock data for now
        recommendations = []
        
        # Generate some mock recommendations
        for i in range(20):
            rec_type = np.random.choice(list(RecommendationType))
            recommendations.append(self._create_recommendation(
                type=rec_type,
                symbol=f"SYMBOL{i}",
                asset_name=f"Asset {i}",
                asset_class=np.random.choice(["equity", "fixed_income", "etf"]),
                action=f"Action for asset {i}",
                rationale=f"Rationale for recommendation {i}",
                confidence_score=np.random.uniform(60, 95),
                expected_impact={"return": f"{np.random.uniform(5, 20):.1f}%"}
            ))
            
        return recommendations 