"""
ESG Scorer - Simple ESG scoring implementation for MVP
"""
import numpy as np
from typing import Dict, List, Any, Tuple
from datetime import datetime
import random

class ESGScorer:
    """
    Simple ESG scoring system for demonstration
    In production, this would connect to real ESG data providers
    """
    
    def __init__(self):
        # ESG criteria weights
        self.weights = {
            "environmental": 0.33,
            "social": 0.33,
            "governance": 0.34
        }
        
        # Company ESG data (mock data for demo)
        self.company_esg_data = {
            "RELIANCE": {
                "environmental": {"carbon_footprint": 0.6, "renewable_energy": 0.4, "waste_management": 0.5},
                "social": {"employee_satisfaction": 0.7, "community_impact": 0.6, "diversity": 0.5},
                "governance": {"board_independence": 0.8, "transparency": 0.7, "ethics": 0.8}
            },
            "TCS": {
                "environmental": {"carbon_footprint": 0.8, "renewable_energy": 0.7, "waste_management": 0.8},
                "social": {"employee_satisfaction": 0.9, "community_impact": 0.8, "diversity": 0.8},
                "governance": {"board_independence": 0.9, "transparency": 0.9, "ethics": 0.9}
            },
            "HDFC": {
                "environmental": {"carbon_footprint": 0.7, "renewable_energy": 0.6, "waste_management": 0.7},
                "social": {"employee_satisfaction": 0.8, "community_impact": 0.7, "diversity": 0.7},
                "governance": {"board_independence": 0.8, "transparency": 0.8, "ethics": 0.8}
            },
            "INFY": {
                "environmental": {"carbon_footprint": 0.9, "renewable_energy": 0.8, "waste_management": 0.8},
                "social": {"employee_satisfaction": 0.8, "community_impact": 0.8, "diversity": 0.9},
                "governance": {"board_independence": 0.8, "transparency": 0.9, "ethics": 0.9}
            }
        }
    
    def calculate_esg_score(self, company: str) -> Dict[str, Any]:
        """
        Calculate ESG score for a company
        Returns score from 0-100
        """
        if company not in self.company_esg_data:
            # Generate random scores for unknown companies
            return self._generate_random_esg_score(company)
        
        data = self.company_esg_data[company]
        
        # Calculate sub-scores
        env_score = np.mean(list(data["environmental"].values())) * 100
        social_score = np.mean(list(data["social"].values())) * 100
        gov_score = np.mean(list(data["governance"].values())) * 100
        
        # Calculate overall score
        overall_score = (
            env_score * self.weights["environmental"] +
            social_score * self.weights["social"] +
            gov_score * self.weights["governance"]
        )
        
        # Determine rating
        rating = self._get_esg_rating(overall_score)
        
        return {
            "company": company,
            "overall_score": round(overall_score, 2),
            "rating": rating,
            "breakdown": {
                "environmental": round(env_score, 2),
                "social": round(social_score, 2),
                "governance": round(gov_score, 2)
            },
            "strengths": self._identify_strengths(data),
            "weaknesses": self._identify_weaknesses(data),
            "timestamp": datetime.now().isoformat()
        }
    
    def _generate_random_esg_score(self, company: str) -> Dict[str, Any]:
        """Generate random ESG scores for demo purposes"""
        env_score = 40 + random.uniform(0, 40)
        social_score = 40 + random.uniform(0, 40)
        gov_score = 40 + random.uniform(0, 40)
        
        overall_score = (
            env_score * self.weights["environmental"] +
            social_score * self.weights["social"] +
            gov_score * self.weights["governance"]
        )
        
        return {
            "company": company,
            "overall_score": round(overall_score, 2),
            "rating": self._get_esg_rating(overall_score),
            "breakdown": {
                "environmental": round(env_score, 2),
                "social": round(social_score, 2),
                "governance": round(gov_score, 2)
            },
            "strengths": ["Data transparency", "Market position"],
            "weaknesses": ["Limited ESG disclosure"],
            "timestamp": datetime.now().isoformat()
        }
    
    def _get_esg_rating(self, score: float) -> str:
        """Convert numeric score to rating"""
        if score >= 80:
            return "AAA"
        elif score >= 70:
            return "AA"
        elif score >= 60:
            return "A"
        elif score >= 50:
            return "BBB"
        elif score >= 40:
            return "BB"
        elif score >= 30:
            return "B"
        else:
            return "CCC"
    
    def _identify_strengths(self, data: Dict) -> List[str]:
        """Identify ESG strengths"""
        strengths = []
        
        # Check environmental strengths
        if np.mean(list(data["environmental"].values())) > 0.7:
            strengths.append("Strong environmental practices")
        
        # Check social strengths
        if data["social"]["employee_satisfaction"] > 0.8:
            strengths.append("High employee satisfaction")
        if data["social"]["diversity"] > 0.7:
            strengths.append("Good diversity metrics")
        
        # Check governance strengths
        if data["governance"]["transparency"] > 0.8:
            strengths.append("Excellent transparency")
        
        return strengths if strengths else ["Maintaining industry standards"]
    
    def _identify_weaknesses(self, data: Dict) -> List[str]:
        """Identify ESG weaknesses"""
        weaknesses = []
        
        # Check environmental weaknesses
        if data["environmental"]["carbon_footprint"] < 0.5:
            weaknesses.append("High carbon footprint")
        
        # Check social weaknesses
        if data["social"]["community_impact"] < 0.5:
            weaknesses.append("Limited community engagement")
        
        # Check governance weaknesses
        if data["governance"]["board_independence"] < 0.6:
            weaknesses.append("Board independence concerns")
        
        return weaknesses if weaknesses else ["Room for improvement in sustainability"]
    
    def analyze_portfolio_esg(self, holdings: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze ESG performance of entire portfolio
        """
        if not holdings:
            return {"error": "No holdings provided"}
        
        total_value = sum(h.get("value", 0) for h in holdings)
        if total_value == 0:
            return {"error": "Portfolio has zero value"}
        
        weighted_scores = {"environmental": 0, "social": 0, "governance": 0}
        overall_weighted = 0
        
        company_scores = []
        
        for holding in holdings:
            company = holding.get("symbol", "")
            value = holding.get("value", 0)
            weight = value / total_value
            
            # Get ESG score for company
            score = self.calculate_esg_score(company)
            company_scores.append(score)
            
            # Add to weighted scores
            for dimension in ["environmental", "social", "governance"]:
                weighted_scores[dimension] += score["breakdown"][dimension] * weight
            
            overall_weighted += score["overall_score"] * weight
        
        # Determine portfolio ESG rating
        portfolio_rating = self._get_esg_rating(overall_weighted)
        
        # Identify improvement opportunities
        improvements = self._suggest_improvements(company_scores, holdings)
        
        return {
            "portfolio_esg_score": round(overall_weighted, 2),
            "portfolio_rating": portfolio_rating,
            "dimension_scores": {k: round(v, 2) for k, v in weighted_scores.items()},
            "company_scores": company_scores,
            "improvement_suggestions": improvements,
            "esg_leaders": [s["company"] for s in company_scores if s["overall_score"] > 70],
            "esg_laggards": [s["company"] for s in company_scores if s["overall_score"] < 50],
            "analysis_timestamp": datetime.now().isoformat()
        }
    
    def _suggest_improvements(self, scores: List[Dict], holdings: List[Dict]) -> List[str]:
        """Suggest portfolio ESG improvements"""
        suggestions = []
        
        # Find lowest scoring companies
        low_scorers = [s for s in scores if s["overall_score"] < 50]
        if low_scorers:
            suggestions.append(f"Consider replacing {low_scorers[0]['company']} with higher ESG-rated alternatives")
        
        # Check dimension balance
        avg_env = np.mean([s["breakdown"]["environmental"] for s in scores])
        avg_social = np.mean([s["breakdown"]["social"] for s in scores])
        avg_gov = np.mean([s["breakdown"]["governance"] for s in scores])
        
        if avg_env < 60:
            suggestions.append("Increase allocation to companies with strong environmental practices")
        if avg_social < 60:
            suggestions.append("Consider companies with better social impact metrics")
        if avg_gov < 60:
            suggestions.append("Focus on companies with stronger governance structures")
        
        if not suggestions:
            suggestions.append("Portfolio has good ESG balance. Continue monitoring for improvements.")
        
        return suggestions
    
    def get_sustainable_alternatives(self, company: str, sector: str = None) -> List[Dict[str, Any]]:
        """
        Get sustainable alternatives to a given company
        """
        # In production, this would search real ESG databases
        # For demo, return mock alternatives
        
        alternatives = {
            "technology": [
                {"symbol": "MSFT", "name": "Microsoft", "esg_score": 82, "reason": "Carbon negative commitment"},
                {"symbol": "AAPL", "name": "Apple", "esg_score": 78, "reason": "100% renewable energy"},
            ],
            "finance": [
                {"symbol": "HDFC", "name": "HDFC Bank", "esg_score": 75, "reason": "Strong governance practices"},
                {"symbol": "ICICI", "name": "ICICI Bank", "esg_score": 72, "reason": "Social inclusion initiatives"},
            ],
            "energy": [
                {"symbol": "TATAPOWER", "name": "Tata Power", "esg_score": 80, "reason": "Renewable energy focus"},
                {"symbol": "ADANIGREEN", "name": "Adani Green", "esg_score": 77, "reason": "Clean energy portfolio"},
            ]
        }
        
        # Return sector-specific alternatives or general ones
        if sector and sector.lower() in alternatives:
            return alternatives[sector.lower()]
        else:
            # Return top ESG companies across sectors
            return [
                {"symbol": "INFY", "name": "Infosys", "esg_score": 85, "reason": "Carbon neutral operations"},
                {"symbol": "TCS", "name": "TCS", "esg_score": 83, "reason": "Sustainability leadership"},
                {"symbol": "WIPRO", "name": "Wipro", "esg_score": 80, "reason": "Water positive commitment"}
            ] 