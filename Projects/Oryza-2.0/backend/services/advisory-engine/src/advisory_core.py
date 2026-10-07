"""
Advisory Core - Central advisory logic and orchestration
"""
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import numpy as np
import logging

from .models import (
    PortfolioAnalysis, RiskAssessment, ActionItem, ActionPriority,
    RiskLevel, MarketCondition, MarketInsight, GoalProgress
)
from .ai_models import SentimentAnalyzer, RiskScorer, PortfolioOptimizer


class AdvisoryCore:
    """
    Core advisory engine that coordinates analysis and recommendations
    """
    
    def __init__(self):
        self.logger = logging.getLogger("advisory_core")
        self.market_data_cache = {}
        self.is_initialized = False
        # Initialize AI models
        self.sentiment_analyzer = SentimentAnalyzer()
        self.risk_scorer = RiskScorer()
        self.portfolio_optimizer = PortfolioOptimizer()
        
    async def initialize(self):
        """Initialize the advisory core"""
        self.logger.info("Initializing Advisory Core with AI models")
        # In production, connect to market data feeds
        await asyncio.sleep(0.1)  # Simulate initialization
        self.is_initialized = True
        self.logger.info("AI models loaded: Sentiment, Risk, and Portfolio Optimizer")
        
    async def get_market_conditions(self) -> Dict[str, Any]:
        """Get current market conditions"""
        # In production, fetch real market data
        return {
            "indices": {
                "SP500": {"value": 4500, "change": 0.5, "trend": "bullish"},
                "NASDAQ": {"value": 14000, "change": 0.8, "trend": "bullish"},
                "DJI": {"value": 35000, "change": 0.3, "trend": "neutral"},
            },
            "volatility": {"VIX": 18.5, "level": "medium"},
            "sentiment": "cautiously_optimistic",
            "key_factors": [
                "Fed policy uncertainty",
                "Corporate earnings growth",
                "Geopolitical tensions"
            ]
        }
        
    async def assess_risks(
        self,
        portfolio: Any,
        market_conditions: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Assess portfolio risks using AI Risk Scorer"""
        # Prepare portfolio data for AI risk scorer
        portfolio_data = {
            "holdings": [
                {"symbol": "RELIANCE", "value": 125000, "asset_type": "stock"},
                {"symbol": "TCS", "value": 87000, "asset_type": "stock"},
                {"symbol": "HDFC_BOND", "value": 50000, "asset_type": "bond"},
                {"symbol": "GOLD_ETF", "value": 38000, "asset_type": "commodity"}
            ],
            "total_value": 300000
        }
        
        # Use AI risk scorer
        ai_risk_assessment = self.risk_scorer.calculate_portfolio_risk(portfolio_data)
        
        # Calculate various risk metrics
        risk_metrics = []
        
        # Volatility risk from AI
        volatility = ai_risk_assessment["risk_breakdown"]["volatility"]
        risk_metrics.append({
            "metric_name": "Portfolio Volatility",
            "current_value": volatility,
            "benchmark_value": 15.0,
            "status": "good" if volatility < 30 else "warning" if volatility < 50 else "critical",
            "description": f"AI-assessed portfolio volatility at {volatility:.1f}%"
        })
        
        # Concentration risk from AI
        concentration = ai_risk_assessment["risk_breakdown"]["concentration"]
        risk_metrics.append({
            "metric_name": "Concentration Risk",
            "current_value": concentration,
            "benchmark_value": 30.0,
            "status": "good" if concentration < 40 else "warning" if concentration < 60 else "critical",
            "description": f"AI-detected concentration risk score: {concentration:.1f}"
        })
        
        # Liquidity risk from AI
        liquidity = ai_risk_assessment["risk_breakdown"]["liquidity"]
        risk_metrics.append({
            "metric_name": "Liquidity Risk",
            "current_value": liquidity,
            "benchmark_value": 30.0,
            "status": "good" if liquidity < 40 else "warning" if liquidity < 60 else "critical",
            "description": f"AI-calculated liquidity risk: {liquidity:.1f}"
        })
        
        # Overall risk assessment
        risk_score = ai_risk_assessment["overall_risk_score"]
        risk_level = ai_risk_assessment["risk_level"]
        
        # Identify specific risks
        concentration_risks = ["High exposure to equity markets"] if concentration > 50 else []
        market_risks = self._identify_market_risks(market_conditions)
        specific_risks = ["Consider diversification across asset classes"]
        
        # Use AI recommendations
        mitigation_suggestions = ai_risk_assessment["recommendations"]
        
        return {
            "overall_risk_level": risk_level,
            "risk_score": risk_score,
            "risk_metrics": risk_metrics,
            "concentration_risks": concentration_risks,
            "market_risks": market_risks,
            "specific_risks": specific_risks,
            "risk_mitigation_suggestions": mitigation_suggestions,
            "ai_powered": True,
            "ai_confidence": 0.85
        }
        
    def _calculate_portfolio_volatility(self, portfolio: Any) -> float:
        """Calculate portfolio volatility"""
        # In production, use historical data and covariance matrices
        # Mock calculation
        return np.random.uniform(12, 22)
        
    def _calculate_concentration_risk(self, portfolio: Any) -> float:
        """Calculate concentration risk"""
        # In production, analyze actual positions
        # Mock: return largest position percentage
        return np.random.uniform(5, 30)
        
    def _calculate_market_correlation(self, portfolio: Any) -> float:
        """Calculate correlation with market"""
        # In production, calculate actual correlation
        return np.random.uniform(0.6, 0.9)
        
    def _calculate_overall_risk_score(
        self,
        risk_metrics: List[Dict[str, Any]],
        market_conditions: Dict[str, Any]
    ) -> float:
        """Calculate overall risk score (0-100)"""
        base_score = 50
        
        # Adjust based on metrics
        for metric in risk_metrics:
            if metric["status"] == "warning":
                base_score += 10
            elif metric["status"] == "critical":
                base_score += 20
                
        # Adjust based on market conditions
        if market_conditions["volatility"]["level"] == "high":
            base_score += 15
        elif market_conditions["volatility"]["level"] == "medium":
            base_score += 5
            
        return min(base_score, 100)
        
    def _determine_risk_level(self, risk_score: float) -> str:
        """Determine risk level from score"""
        if risk_score < 20:
            return RiskLevel.VERY_LOW
        elif risk_score < 40:
            return RiskLevel.LOW
        elif risk_score < 60:
            return RiskLevel.MEDIUM
        elif risk_score < 80:
            return RiskLevel.HIGH
        else:
            return RiskLevel.VERY_HIGH
            
    def _identify_concentration_risks(self, portfolio: Any) -> List[Dict[str, Any]]:
        """Identify concentration risks"""
        risks = []
        
        # Check sector concentration
        # In production, analyze actual sector distribution
        risks.append({
            "type": "sector_concentration",
            "description": "Technology sector represents 45% of portfolio",
            "severity": "medium",
            "impact": "Vulnerable to tech sector downturns"
        })
        
        return risks
        
    def _identify_market_risks(self, market_conditions: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify market-related risks"""
        risks = []
        
        for factor in market_conditions.get("key_factors", []):
            risks.append({
                "type": "market_factor",
                "description": factor,
                "severity": "medium",
                "impact": "Could affect overall portfolio performance"
            })
            
        return risks
        
    def _identify_specific_risks(self, portfolio: Any) -> List[Dict[str, Any]]:
        """Identify portfolio-specific risks"""
        # In production, analyze actual holdings
        return [
            {
                "type": "currency_risk",
                "description": "15% exposure to foreign currency fluctuations",
                "severity": "low",
                "impact": "Potential impact on international holdings"
            }
        ]
        
    def _generate_risk_mitigation_suggestions(
        self,
        risk_level: str,
        concentration_risks: List[Dict[str, Any]],
        market_risks: List[Dict[str, Any]],
        specific_risks: List[Dict[str, Any]]
    ) -> List[str]:
        """Generate risk mitigation suggestions"""
        suggestions = []
        
        if risk_level in [RiskLevel.HIGH, RiskLevel.VERY_HIGH]:
            suggestions.append("Consider reducing overall portfolio risk through diversification")
            suggestions.append("Review and potentially reduce leverage if applicable")
            
        if concentration_risks:
            suggestions.append("Diversify holdings to reduce concentration in specific sectors")
            
        if len(market_risks) > 2:
            suggestions.append("Consider hedging strategies for market volatility")
            
        suggestions.append("Maintain adequate cash reserves for market opportunities")
        
        return suggestions
        
    async def generate_action_items(
        self,
        portfolio_analysis: Dict[str, Any],
        recommendations: List[Dict[str, Any]],
        risk_assessment: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate prioritized action items"""
        action_items = []
        
        # High priority items
        if risk_assessment["overall_risk_level"] in [RiskLevel.HIGH, RiskLevel.VERY_HIGH]:
            action_items.append({
                "id": "action_001",
                "title": "Reduce Portfolio Risk",
                "description": "Your portfolio risk is elevated. Consider rebalancing to reduce exposure.",
                "priority": ActionPriority.HIGH,
                "category": "risk",
                "impact": "Reduce potential losses by 10-15%",
                "steps": [
                    "Review current allocations",
                    "Identify high-risk positions",
                    "Gradually reduce exposure",
                    "Increase defensive assets"
                ],
                "automated_available": True
            })
            
        # Rebalancing opportunities
        if self._needs_rebalancing(portfolio_analysis):
            action_items.append({
                "id": "action_002",
                "title": "Rebalance Portfolio",
                "description": "Your portfolio has drifted from target allocations",
                "priority": ActionPriority.MEDIUM,
                "category": "rebalancing",
                "deadline": datetime.now() + timedelta(days=30),
                "impact": "Restore optimal risk-return profile",
                "steps": [
                    "Review target allocations",
                    "Calculate required trades",
                    "Execute rebalancing trades",
                    "Update portfolio targets"
                ],
                "automated_available": True
            })
            
        # Tax optimization
        if datetime.now().month in [11, 12]:  # Year-end
            action_items.append({
                "id": "action_003",
                "title": "Year-End Tax Loss Harvesting",
                "description": "Identify opportunities to reduce tax liability",
                "priority": ActionPriority.MEDIUM,
                "category": "tax",
                "deadline": datetime(datetime.now().year, 12, 31),
                "impact": "Potential tax savings of $500-2000",
                "steps": [
                    "Identify positions with losses",
                    "Review wash sale rules",
                    "Execute tax loss harvesting",
                    "Reinvest proceeds strategically"
                ],
                "automated_available": True
            })
            
        # Investment opportunities
        for rec in recommendations[:2]:  # Top 2 recommendations
            action_items.append({
                "id": f"action_{len(action_items)+1:03d}",
                "title": f"Investment Opportunity: {rec.get('asset_name', 'Asset')}",
                "description": rec.get('rationale', 'Strong investment opportunity identified'),
                "priority": ActionPriority.LOW,
                "category": "opportunity",
                "impact": rec.get('expected_impact', {}).get('return', 'Positive expected return'),
                "steps": [
                    "Review recommendation details",
                    "Assess fit with portfolio",
                    "Determine position size",
                    "Place investment order"
                ],
                "automated_available": False
            })
            
        return action_items
        
    def _needs_rebalancing(self, portfolio_analysis: Dict[str, Any]) -> bool:
        """Check if portfolio needs rebalancing"""
        # In production, check actual deviation from targets
        return np.random.random() > 0.5  # 50% chance for demo
        
    def calculate_next_review_date(
        self,
        portfolio_analysis: Dict[str, Any],
        review_frequency: str
    ) -> datetime:
        """Calculate next portfolio review date"""
        frequencies = {
            "monthly": timedelta(days=30),
            "quarterly": timedelta(days=90),
            "annually": timedelta(days=365)
        }
        
        delta = frequencies.get(review_frequency, timedelta(days=90))
        return datetime.now() + delta
        
    async def get_market_overview(self) -> Dict[str, Any]:
        """Get comprehensive market overview"""
        conditions = []
        
        # Major indices
        indices = {
            "S&P 500": {"value": 4500, "change": 12.5, "change_pct": 0.28},
            "NASDAQ": {"value": 14000, "change": 45.2, "change_pct": 0.32},
            "Dow Jones": {"value": 35000, "change": 85.0, "change_pct": 0.24},
            "Russell 2000": {"value": 2200, "change": -5.5, "change_pct": -0.25}
        }
        
        for index, data in indices.items():
            trend = "bullish" if data["change_pct"] > 0.1 else "bearish" if data["change_pct"] < -0.1 else "neutral"
            conditions.append(MarketCondition(
                index=index,
                value=data["value"],
                change=data["change"],
                change_percentage=data["change_pct"],
                trend=trend,
                volatility="medium"
            ))
            
        # Market insights
        insights = [
            MarketInsight(
                title="Fed Policy Impact",
                description="Federal Reserve signals potential rate pause, supporting equity valuations",
                impact="positive",
                affected_sectors=["Technology", "Real Estate", "Consumer Discretionary"],
                recommended_actions=["Consider growth stocks", "Review bond duration"],
                confidence=75
            ),
            MarketInsight(
                title="Earnings Season Strong",
                description="Q3 earnings beating expectations for 78% of S&P 500 companies",
                impact="positive",
                affected_sectors=["Technology", "Healthcare", "Financials"],
                recommended_actions=["Focus on quality earnings", "Look for guidance upgrades"],
                confidence=85
            )
        ]
        
        # Sector performance
        sector_performance = {
            "Technology": 2.5,
            "Healthcare": 1.8,
            "Financials": 0.5,
            "Energy": -1.2,
            "Real Estate": 1.2,
            "Consumer Discretionary": 1.5,
            "Industrials": 0.8,
            "Materials": -0.5,
            "Utilities": 0.2,
            "Consumer Staples": 0.3
        }
        
        return {
            "timestamp": datetime.now(),
            "conditions": conditions,
            "insights": insights,
            "sentiment": "cautiously_optimistic",
            "volatility_index": 18.5,
            "fear_greed_index": 65,  # 0-100, 65 = Greed
            "sector_performance": sector_performance,
            "global_factors": [
                "China economic recovery",
                "European energy situation",
                "US-China trade relations",
                "Global inflation trends"
            ]
        }
        
    async def get_trending_insights(self) -> List[Dict[str, Any]]:
        """Get trending market insights"""
        return [
            {
                "id": "insight_001",
                "category": "technology",
                "title": "AI Revolution Continues",
                "summary": "AI-related stocks showing strong momentum",
                "details": "Companies with strong AI exposure outperforming by 15%",
                "action": "Consider AI-focused ETFs or leading AI companies",
                "relevance_score": 0.9,
                "timestamp": datetime.now()
            },
            {
                "id": "insight_002",
                "category": "macro",
                "title": "Inflation Moderating",
                "summary": "Core inflation showing signs of cooling",
                "details": "CPI data suggests Fed may pause rate hikes",
                "action": "Review fixed income duration and equity growth exposure",
                "relevance_score": 0.85,
                "timestamp": datetime.now()
            },
            {
                "id": "insight_003",
                "category": "sector",
                "title": "Healthcare Innovation",
                "summary": "Biotech sector seeing increased M&A activity",
                "details": "Large pharma companies acquiring innovative biotechs",
                "action": "Consider biotech ETFs for diversified exposure",
                "relevance_score": 0.75,
                "timestamp": datetime.now()
            }
        ]
        
    async def calculate_goal_progress(
        self,
        portfolio: Any,
        goals: List[Any]
    ) -> List[Dict[str, Any]]:
        """Calculate progress towards financial goals"""
        progress_list = []
        
        for goal in goals:
            # In production, calculate actual progress
            current_value = portfolio.total_value * 0.3  # Mock: 30% allocated to this goal
            progress_pct = (current_value / goal.target_amount) * 100
            
            # Project completion date
            monthly_contribution = 1000  # Mock value
            months_to_goal = max(0, (goal.target_amount - current_value) / monthly_contribution)
            projected_date = datetime.now() + timedelta(days=months_to_goal * 30)
            
            progress_list.append({
                "goal_id": goal.id,
                "goal_type": goal.goal_type,
                "goal_name": goal.name,
                "target_amount": goal.target_amount,
                "current_amount": current_value,
                "progress_percentage": min(progress_pct, 100),
                "projected_completion_date": projected_date,
                "on_track": progress_pct >= (goal.progress_expected or 50),
                "monthly_contribution_needed": monthly_contribution,
                "recommendations": [
                    f"Increase monthly contribution to ${monthly_contribution * 1.2:.0f} to reach goal faster",
                    "Consider automating contributions",
                    "Review asset allocation for this goal"
                ]
            })
            
        return progress_list
        
    async def get_educational_content(
        self,
        user_level: str,
        topic: Optional[str],
        user_interests: List[str]
    ) -> List[Dict[str, Any]]:
        """Get personalized educational content"""
        # In production, use ML to personalize content
        content = [
            {
                "id": "edu_001",
                "title": "Understanding Portfolio Diversification",
                "category": "investing_basics",
                "level": "beginner",
                "content_type": "article",
                "summary": "Learn how diversification can reduce risk while maintaining returns",
                "url": "/education/diversification-guide",
                "duration_minutes": 10,
                "topics": ["diversification", "risk_management", "asset_allocation"],
                "personalized_relevance": 0.9
            },
            {
                "id": "edu_002",
                "title": "Tax-Efficient Investing Strategies",
                "category": "tax_planning",
                "level": user_level,
                "content_type": "video",
                "summary": "Maximize after-tax returns with smart tax strategies",
                "url": "/education/tax-efficiency-video",
                "duration_minutes": 15,
                "topics": ["taxes", "tax_loss_harvesting", "asset_location"],
                "personalized_relevance": 0.85
            },
            {
                "id": "edu_003",
                "title": "Introduction to ESG Investing",
                "category": "sustainable_investing",
                "level": user_level,
                "content_type": "interactive",
                "summary": "Explore how to align your investments with your values",
                "url": "/education/esg-interactive",
                "duration_minutes": 20,
                "topics": ["ESG", "sustainable_investing", "impact_investing"],
                "personalized_relevance": 0.8
            }
        ]
        
        # Filter by topic if specified
        if topic:
            content = [c for c in content if topic in c["topics"]]
            
        # Sort by relevance
        content.sort(key=lambda x: x["personalized_relevance"], reverse=True)
        
        return content 