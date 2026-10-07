"""
AI Models for Advisory Engine - Simple implementations for MVP
"""
import numpy as np
from typing import Dict, List, Any, Tuple
import random
from datetime import datetime
import json

class SentimentAnalyzer:
    """
    Simple sentiment analyzer for financial news
    In production, this would use FinBERT or similar models
    """
    
    def __init__(self):
        # Sentiment keywords for simple analysis
        self.positive_keywords = [
            'growth', 'profit', 'gain', 'surge', 'rally', 'bullish', 
            'upgrade', 'beat', 'strong', 'record', 'boom', 'soar'
        ]
        self.negative_keywords = [
            'loss', 'decline', 'fall', 'crash', 'bearish', 'downgrade',
            'miss', 'weak', 'recession', 'slump', 'plunge', 'crisis'
        ]
        
    def analyze_text(self, text: str) -> Dict[str, float]:
        """
        Analyze sentiment of financial text
        Returns scores between -1 (negative) and 1 (positive)
        """
        text_lower = text.lower()
        
        # Count positive and negative words
        positive_count = sum(1 for word in self.positive_keywords if word in text_lower)
        negative_count = sum(1 for word in self.negative_keywords if word in text_lower)
        
        # Calculate sentiment score
        total_keywords = positive_count + negative_count
        if total_keywords == 0:
            sentiment_score = 0.0
        else:
            sentiment_score = (positive_count - negative_count) / total_keywords
        
        # Add some randomness for demo
        sentiment_score += random.uniform(-0.1, 0.1)
        sentiment_score = max(-1, min(1, sentiment_score))
        
        return {
            "sentiment_score": sentiment_score,
            "confidence": 0.75 + random.uniform(0, 0.2),
            "positive_signals": positive_count,
            "negative_signals": negative_count
        }
    
    def analyze_market_sentiment(self, news_items: List[str]) -> Dict[str, Any]:
        """Analyze overall market sentiment from multiple news items"""
        if not news_items:
            return {"overall_sentiment": 0, "trend": "neutral"}
        
        sentiments = [self.analyze_text(news)["sentiment_score"] for news in news_items]
        avg_sentiment = np.mean(sentiments)
        
        # Determine trend
        if avg_sentiment > 0.3:
            trend = "bullish"
        elif avg_sentiment < -0.3:
            trend = "bearish"
        else:
            trend = "neutral"
        
        return {
            "overall_sentiment": avg_sentiment,
            "trend": trend,
            "analyzed_items": len(news_items),
            "sentiment_distribution": {
                "positive": sum(1 for s in sentiments if s > 0.1),
                "neutral": sum(1 for s in sentiments if -0.1 <= s <= 0.1),
                "negative": sum(1 for s in sentiments if s < -0.1)
            }
        }


class RiskScorer:
    """
    Simple risk scoring model for portfolios
    """
    
    def __init__(self):
        # Risk factors and weights
        self.risk_factors = {
            "concentration": 0.3,      # How concentrated the portfolio is
            "volatility": 0.25,        # Historical volatility
            "correlation": 0.2,        # Asset correlation
            "liquidity": 0.15,         # Liquidity risk
            "market_conditions": 0.1   # Current market risk
        }
        
    def calculate_portfolio_risk(self, portfolio_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate risk score for a portfolio
        Returns risk score 0-100 (0 = lowest risk, 100 = highest risk)
        """
        risk_scores = {}
        
        # Concentration risk (Herfindahl index)
        holdings = portfolio_data.get("holdings", [])
        if holdings:
            total_value = sum(h.get("value", 0) for h in holdings)
            if total_value > 0:
                concentration = sum((h.get("value", 0) / total_value) ** 2 for h in holdings)
                risk_scores["concentration"] = concentration * 100
            else:
                risk_scores["concentration"] = 50
        else:
            risk_scores["concentration"] = 50
        
        # Volatility risk (simulated)
        risk_scores["volatility"] = 20 + random.uniform(0, 40)
        
        # Correlation risk (simulated)
        risk_scores["correlation"] = 30 + random.uniform(0, 30)
        
        # Liquidity risk (based on asset types)
        risk_scores["liquidity"] = self._calculate_liquidity_risk(holdings)
        
        # Market conditions risk
        risk_scores["market_conditions"] = 40 + random.uniform(0, 20)
        
        # Calculate weighted average
        total_risk = sum(
            risk_scores[factor] * weight 
            for factor, weight in self.risk_factors.items()
        )
        
        # Determine risk level
        if total_risk < 30:
            risk_level = "low"
        elif total_risk < 50:
            risk_level = "moderate"
        elif total_risk < 70:
            risk_level = "high"
        else:
            risk_level = "very_high"
        
        return {
            "overall_risk_score": round(total_risk, 2),
            "risk_level": risk_level,
            "risk_breakdown": risk_scores,
            "recommendations": self._generate_risk_recommendations(risk_scores)
        }
    
    def _calculate_liquidity_risk(self, holdings: List[Dict]) -> float:
        """Calculate liquidity risk based on asset types"""
        if not holdings:
            return 50
        
        # Simple liquidity scoring by asset type
        liquidity_scores = {
            "stock": 20,
            "bond": 30,
            "mutual_fund": 25,
            "etf": 15,
            "commodity": 40,
            "crypto": 60,
            "real_estate": 80
        }
        
        total_value = sum(h.get("value", 0) for h in holdings)
        if total_value == 0:
            return 50
        
        weighted_liquidity = sum(
            h.get("value", 0) / total_value * 
            liquidity_scores.get(h.get("asset_type", "stock"), 50)
            for h in holdings
        )
        
        return weighted_liquidity
    
    def _generate_risk_recommendations(self, risk_scores: Dict[str, float]) -> List[str]:
        """Generate risk-based recommendations"""
        recommendations = []
        
        if risk_scores.get("concentration", 0) > 60:
            recommendations.append("Portfolio is highly concentrated. Consider diversifying across more assets.")
        
        if risk_scores.get("volatility", 0) > 60:
            recommendations.append("High volatility detected. Consider adding defensive assets.")
        
        if risk_scores.get("liquidity", 0) > 50:
            recommendations.append("Liquidity risk is elevated. Ensure you have sufficient liquid assets.")
        
        if not recommendations:
            recommendations.append("Portfolio risk is well-managed. Continue monitoring market conditions.")
        
        return recommendations


class PortfolioOptimizer:
    """
    Simple portfolio optimization using Modern Portfolio Theory concepts
    """
    
    def __init__(self):
        self.risk_free_rate = 0.04  # 4% risk-free rate
        
    def optimize_allocation(
        self, 
        current_portfolio: Dict[str, Any],
        risk_tolerance: str,
        investment_goals: List[str]
    ) -> Dict[str, Any]:
        """
        Generate optimized portfolio allocation
        """
        # Define target allocations based on risk tolerance
        allocation_templates = {
            "conservative": {
                "stocks": 0.30,
                "bonds": 0.50,
                "commodities": 0.10,
                "cash": 0.10
            },
            "moderate": {
                "stocks": 0.50,
                "bonds": 0.30,
                "commodities": 0.10,
                "alternatives": 0.05,
                "cash": 0.05
            },
            "aggressive": {
                "stocks": 0.70,
                "bonds": 0.15,
                "commodities": 0.05,
                "alternatives": 0.08,
                "cash": 0.02
            }
        }
        
        # Get base allocation
        base_allocation = allocation_templates.get(risk_tolerance, allocation_templates["moderate"])
        
        # Adjust for investment goals
        if "growth" in investment_goals:
            base_allocation["stocks"] = min(base_allocation.get("stocks", 0) + 0.1, 0.8)
            base_allocation["bonds"] = max(base_allocation.get("bonds", 0) - 0.1, 0.1)
        
        if "income" in investment_goals:
            base_allocation["bonds"] = min(base_allocation.get("bonds", 0) + 0.1, 0.6)
            base_allocation["stocks"] = max(base_allocation.get("stocks", 0) - 0.1, 0.2)
        
        # Calculate expected returns (simplified)
        expected_returns = {
            "stocks": 0.10 + random.uniform(-0.02, 0.02),
            "bonds": 0.05 + random.uniform(-0.01, 0.01),
            "commodities": 0.06 + random.uniform(-0.03, 0.03),
            "alternatives": 0.08 + random.uniform(-0.02, 0.02),
            "cash": 0.02
        }
        
        # Calculate portfolio expected return
        portfolio_return = sum(
            base_allocation.get(asset, 0) * expected_returns.get(asset, 0.05)
            for asset in base_allocation
        )
        
        # Generate rebalancing suggestions
        rebalancing_needed = self._check_rebalancing_needed(current_portfolio, base_allocation)
        
        return {
            "target_allocation": base_allocation,
            "expected_return": round(portfolio_return, 4),
            "sharpe_ratio": round((portfolio_return - self.risk_free_rate) / 0.15, 2),
            "rebalancing_needed": rebalancing_needed,
            "optimization_timestamp": datetime.now().isoformat()
        }
    
    def _check_rebalancing_needed(
        self, 
        current: Dict[str, Any], 
        target: Dict[str, float]
    ) -> Dict[str, Any]:
        """Check if rebalancing is needed"""
        # Simplified rebalancing check
        threshold = 0.05  # 5% threshold
        
        actions = []
        for asset_class, target_weight in target.items():
            current_weight = current.get("allocation", {}).get(asset_class, 0)
            diff = target_weight - current_weight
            
            if abs(diff) > threshold:
                action = "increase" if diff > 0 else "decrease"
                actions.append({
                    "asset_class": asset_class,
                    "action": action,
                    "amount": abs(diff),
                    "current": current_weight,
                    "target": target_weight
                })
        
        return {
            "needed": len(actions) > 0,
            "actions": actions
        } 