"""
ESG Investment Analyzer
Ensures values alignment, monitors controversies, and maximizes impact through active selection
"""

import random
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import logging
import math

class ESGAnalyzer:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # ESG investment universe
        self.esg_investments = {
            # Green Energy
            "ICLN": {
                "name": "iShares Global Clean Energy ETF",
                "symbol": "ICLN",
                "type": "Clean Energy ETF",
                "category": "Environmental",
                "price": 18.75,
                "expense_ratio": 0.42,
                "holdings": 100,
                "aum": 5200000000,
                "esg_score": 8.5,
                "environmental_score": 9.2,
                "social_score": 7.8,
                "governance_score": 8.0,
                "carbon_intensity": 15.2,  # tCO2e/$M revenue
                "renewable_exposure": 95,
                "controversy_score": 0,
                "impact_metrics": {
                    "co2_avoided": 2500000,  # tons/year
                    "renewable_capacity": 50000,  # MW
                    "green_jobs": 150000
                }
            },
            "TAN": {
                "name": "Invesco Solar ETF",
                "symbol": "TAN",
                "type": "Solar Energy ETF",
                "category": "Environmental",
                "price": 65.40,
                "expense_ratio": 0.69,
                "holdings": 50,
                "aum": 2800000000,
                "esg_score": 8.8,
                "environmental_score": 9.5,
                "social_score": 8.0,
                "governance_score": 8.2,
                "carbon_intensity": 8.5,
                "renewable_exposure": 100,
                "controversy_score": 0,
                "impact_metrics": {
                    "co2_avoided": 1800000,
                    "solar_capacity": 30000,
                    "clean_energy_homes": 5000000
                }
            },
            
            # Sustainable Companies
            "DSI": {
                "name": "iShares MSCI KLD 400 Social ETF",
                "symbol": "DSI",
                "type": "ESG Leaders ETF",
                "category": "Broad ESG",
                "price": 132.50,
                "expense_ratio": 0.25,
                "holdings": 400,
                "aum": 3500000000,
                "esg_score": 7.8,
                "environmental_score": 7.5,
                "social_score": 8.2,
                "governance_score": 7.7,
                "carbon_intensity": 85.3,
                "renewable_exposure": 25,
                "controversy_score": 0.5,
                "impact_metrics": {
                    "diversity_score": 8.5,
                    "community_investment": 2500000000,
                    "sustainable_products": 45
                }
            },
            "ESGU": {
                "name": "iShares ESG Aware MSCI USA ETF",
                "symbol": "ESGU",
                "type": "ESG Integration ETF",
                "category": "Broad ESG",
                "price": 98.75,
                "expense_ratio": 0.15,
                "holdings": 300,
                "aum": 25000000000,
                "esg_score": 7.5,
                "environmental_score": 7.2,
                "social_score": 7.8,
                "governance_score": 7.5,
                "carbon_intensity": 95.5,
                "renewable_exposure": 20,
                "controversy_score": 0.8,
                "impact_metrics": {
                    "ghg_reduction": 15,  # % vs benchmark
                    "board_diversity": 35,  # % women
                    "ethics_training": 95  # % employees
                }
            },
            
            # Water & Environment
            "PHO": {
                "name": "Invesco Water Resources ETF",
                "symbol": "PHO",
                "type": "Water Resources ETF",
                "category": "Environmental",
                "price": 54.80,
                "expense_ratio": 0.60,
                "holdings": 36,
                "aum": 1800000000,
                "esg_score": 8.2,
                "environmental_score": 9.0,
                "social_score": 7.5,
                "governance_score": 7.8,
                "carbon_intensity": 45.2,
                "renewable_exposure": 15,
                "controversy_score": 0.2,
                "impact_metrics": {
                    "water_saved": 500000000,  # gallons/year
                    "water_access": 2000000,  # people
                    "infrastructure_investment": 5000000000
                }
            },
            
            # Social Impact
            "NACP": {
                "name": "Impact Shares NAACP Minority Empowerment ETF",
                "symbol": "NACP",
                "type": "Social Impact ETF",
                "category": "Social",
                "price": 28.90,
                "expense_ratio": 0.75,
                "holdings": 100,
                "aum": 120000000,
                "esg_score": 8.0,
                "environmental_score": 6.5,
                "social_score": 9.5,
                "governance_score": 8.0,
                "carbon_intensity": 110.5,
                "renewable_exposure": 10,
                "controversy_score": 0,
                "impact_metrics": {
                    "minority_employment": 45,  # %
                    "supplier_diversity": 30,  # %
                    "community_programs": 250
                }
            },
            "SHE": {
                "name": "SPDR Gender Diversity ETF",
                "symbol": "SHE",
                "type": "Gender Diversity ETF",
                "category": "Social",
                "price": 112.30,
                "expense_ratio": 0.20,
                "holdings": 185,
                "aum": 350000000,
                "esg_score": 7.7,
                "environmental_score": 7.0,
                "social_score": 8.8,
                "governance_score": 7.3,
                "carbon_intensity": 98.7,
                "renewable_exposure": 18,
                "controversy_score": 0.3,
                "impact_metrics": {
                    "women_leadership": 40,  # % exec positions
                    "gender_pay_gap": 5,  # %
                    "parental_leave": 16  # weeks avg
                }
            },
            
            # Green Bonds
            "GRNB": {
                "name": "VanEck Green Bond ETF",
                "symbol": "GRNB",
                "type": "Green Bond ETF",
                "category": "Environmental",
                "price": 25.15,
                "expense_ratio": 0.20,
                "holdings": 280,
                "aum": 150000000,
                "esg_score": 8.3,
                "environmental_score": 9.0,
                "social_score": 7.8,
                "governance_score": 7.5,
                "carbon_intensity": 5.2,
                "renewable_exposure": 80,
                "controversy_score": 0,
                "impact_metrics": {
                    "green_projects_funded": 500,
                    "renewable_capacity_funded": 25000,  # MW
                    "emissions_avoided": 3000000  # tons CO2
                }
            },
            
            # Sustainable Real Estate
            "ERTH": {
                "name": "Invesco MSCI Sustainable Future ETF",
                "symbol": "ERTH",
                "type": "Sustainable Future ETF",
                "category": "Broad ESG",
                "price": 62.45,
                "expense_ratio": 0.55,
                "holdings": 150,
                "aum": 280000000,
                "esg_score": 8.4,
                "environmental_score": 8.8,
                "social_score": 8.2,
                "governance_score": 8.0,
                "carbon_intensity": 25.5,
                "renewable_exposure": 60,
                "controversy_score": 0.1,
                "impact_metrics": {
                    "sustainable_buildings": 1500,
                    "energy_efficiency": 40,  # % improvement
                    "green_certifications": 85  # % of properties
                }
            },
            
            # Circular Economy
            "KROP": {
                "name": "Global X AgTech & Food Innovation ETF",
                "symbol": "KROP",
                "type": "Sustainable Agriculture ETF",
                "category": "Environmental",
                "price": 20.85,
                "expense_ratio": 0.50,
                "holdings": 40,
                "aum": 80000000,
                "esg_score": 7.9,
                "environmental_score": 8.5,
                "social_score": 7.5,
                "governance_score": 7.2,
                "carbon_intensity": 65.3,
                "renewable_exposure": 35,
                "controversy_score": 0.4,
                "impact_metrics": {
                    "food_waste_reduced": 2000000,  # tons
                    "sustainable_farming": 500000,  # acres
                    "water_efficiency": 30  # % improvement
                }
            }
        }
        
        # ESG themes and focus areas
        self.esg_themes = {
            "Climate Action": {
                "priority": 9.5,
                "investments": ["ICLN", "TAN", "GRNB"],
                "impact_focus": "co2_reduction",
                "exclusions": ["fossil_fuels", "coal_mining"]
            },
            "Social Justice": {
                "priority": 8.5,
                "investments": ["NACP", "SHE", "DSI"],
                "impact_focus": "equality",
                "exclusions": ["weapons", "tobacco"]
            },
            "Clean Water": {
                "priority": 9.0,
                "investments": ["PHO"],
                "impact_focus": "water_access",
                "exclusions": ["water_polluters"]
            },
            "Sustainable Living": {
                "priority": 8.0,
                "investments": ["ERTH", "KROP"],
                "impact_focus": "sustainability",
                "exclusions": ["deforestation"]
            }
        }
        
        # Controversy monitoring
        self.controversy_events = {
            "environmental_violation": -3.0,
            "labor_dispute": -2.0,
            "governance_scandal": -2.5,
            "data_breach": -1.5,
            "greenwashing": -4.0,
            "human_rights": -3.5,
            "tax_avoidance": -2.0,
            "product_safety": -2.5
        }
        
        # Values alignment profiles
        self.values_profiles = {
            "climate_first": {
                "environmental": 0.6,
                "social": 0.2,
                "governance": 0.2
            },
            "social_impact": {
                "environmental": 0.2,
                "social": 0.6,
                "governance": 0.2
            },
            "balanced_esg": {
                "environmental": 0.33,
                "social": 0.33,
                "governance": 0.34
            },
            "governance_focus": {
                "environmental": 0.2,
                "social": 0.2,
                "governance": 0.6
            }
        }
        
        # Impact measurement
        self.impact_categories = {
            "carbon_reduction": {"unit": "tCO2e", "weight": 0.3},
            "renewable_energy": {"unit": "MW", "weight": 0.25},
            "social_equality": {"unit": "score", "weight": 0.2},
            "water_conservation": {"unit": "gallons", "weight": 0.15},
            "circular_economy": {"unit": "tons", "weight": 0.1}
        }
        
        # Performance tracking
        self.investment_performance = {}
        self._initialize_performance()
        
        # Controversy tracking
        self.active_controversies = {}
        
        # Impact tracking
        self.portfolio_impact = {}
        
    def _initialize_performance(self):
        """Initialize ESG investment performance tracking"""
        for inv_id, inv_data in self.esg_investments.items():
            self.investment_performance[inv_id] = {
                "current_price": inv_data["price"],
                "daily_change": 0,
                "daily_change_percent": 0,
                "weekly_return": random.uniform(-2, 3),
                "monthly_return": random.uniform(-5, 8),
                "ytd_return": random.uniform(-10, 25),
                "esg_score_change": 0,
                "controversy_alert": False,
                "impact_score": self._calculate_initial_impact(inv_data)
            }
            
    def _calculate_initial_impact(self, investment: Dict) -> float:
        """Calculate initial impact score"""
        impact = investment["esg_score"] * 10
        
        # Environmental impact bonus
        if investment["carbon_intensity"] < 50:
            impact += 10
        elif investment["carbon_intensity"] < 100:
            impact += 5
            
        # Renewable exposure bonus
        impact += investment["renewable_exposure"] * 0.2
        
        # Controversy penalty
        impact -= investment["controversy_score"] * 20
        
        return min(100, max(0, impact))
        
    async def analyze_esg_investment_multi_agent(self, inv_id: str) -> Dict[str, Any]:
        """Multi-agent analysis of an ESG investment"""
        investment = self.esg_investments.get(inv_id)
        if not investment:
            return None
            
        performance = self.investment_performance[inv_id]
        
        # ESG Agent Analysis
        esg_analysis = await self._esg_agent_analysis(investment, performance)
        
        # Impact Agent Analysis
        impact_analysis = await self._impact_agent_analysis(investment, performance)
        
        # Risk Agent Analysis (Controversy)
        risk_analysis = await self._risk_agent_analysis(investment, performance)
        
        # Values Agent Analysis
        values_analysis = await self._values_agent_analysis(investment, performance)
        
        # Build consensus
        consensus = await self._build_esg_consensus(
            esg_analysis, impact_analysis, risk_analysis, values_analysis
        )
        
        return {
            "investment_id": inv_id,
            "investment_name": investment["name"],
            "current_price": performance["current_price"],
            "daily_change": performance["daily_change_percent"],
            "agents": {
                "esg": esg_analysis,
                "impact": impact_analysis,
                "risk": risk_analysis,
                "values": values_analysis
            },
            "consensus": consensus,
            "timestamp": datetime.now().isoformat()
        }
        
    async def _esg_agent_analysis(self, investment: Dict, performance: Dict) -> Dict[str, Any]:
        """Analyze ESG scores and trends"""
        # ESG score assessment
        esg_rating = self._rate_esg_score(investment["esg_score"])
        
        # Component analysis
        env_strength = "Strong" if investment["environmental_score"] > 8 else \
                      "Good" if investment["environmental_score"] > 7 else "Average"
        
        social_strength = "Strong" if investment["social_score"] > 8 else \
                         "Good" if investment["social_score"] > 7 else "Average"
        
        gov_strength = "Strong" if investment["governance_score"] > 8 else \
                      "Good" if investment["governance_score"] > 7 else "Average"
        
        # Carbon assessment
        carbon_rating = self._assess_carbon_intensity(investment["carbon_intensity"])
        
        # Trend analysis
        esg_trend = self._analyze_esg_trend(performance)
        
        return {
            "overall_score": f"{investment['esg_score']}/10",
            "rating": esg_rating,
            "environmental": {
                "score": f"{investment['environmental_score']}/10",
                "strength": env_strength,
                "carbon_intensity": f"{investment['carbon_intensity']} tCO2e/$M",
                "carbon_rating": carbon_rating,
                "renewable_exposure": f"{investment['renewable_exposure']}%"
            },
            "social": {
                "score": f"{investment['social_score']}/10",
                "strength": social_strength,
                "key_focus": self._identify_social_focus(investment)
            },
            "governance": {
                "score": f"{investment['governance_score']}/10",
                "strength": gov_strength
            },
            "trend": esg_trend,
            "recommendation": self._get_esg_recommendation(investment, esg_rating)
        }
        
    async def _impact_agent_analysis(self, investment: Dict, performance: Dict) -> Dict[str, Any]:
        """Analyze real-world impact"""
        impact_metrics = investment.get("impact_metrics", {})
        
        # Calculate impact scores
        environmental_impact = self._calculate_environmental_impact(investment, impact_metrics)
        social_impact = self._calculate_social_impact(investment, impact_metrics)
        
        # Impact efficiency
        impact_per_dollar = performance["impact_score"] / investment["price"]
        
        # Tangible outcomes
        tangible_outcomes = self._identify_tangible_outcomes(impact_metrics)
        
        # UN SDG alignment
        sdg_alignment = self._assess_sdg_alignment(investment)
        
        return {
            "impact_score": f"{performance['impact_score']:.1f}/100",
            "environmental_impact": environmental_impact,
            "social_impact": social_impact,
            "tangible_outcomes": tangible_outcomes,
            "impact_efficiency": f"{impact_per_dollar:.2f} impact/$",
            "sdg_alignment": sdg_alignment,
            "measurable_benefits": self._format_impact_metrics(impact_metrics),
            "impact_verification": self._assess_impact_verification(investment),
            "recommendation": self._get_impact_recommendation(performance["impact_score"])
        }
        
    async def _risk_agent_analysis(self, investment: Dict, performance: Dict) -> Dict[str, Any]:
        """Analyze ESG risks and controversies"""
        # Current controversy assessment
        controversy_level = self._assess_controversy_level(investment["controversy_score"])
        
        # Active controversies
        active_issues = self.active_controversies.get(investment["symbol"], [])
        
        # Risk factors
        risk_factors = self._identify_esg_risks(investment)
        
        # Greenwashing risk
        greenwashing_risk = self._assess_greenwashing_risk(investment)
        
        # Regulatory risk
        regulatory_risk = self._assess_regulatory_risk(investment)
        
        # Reputation risk
        reputation_risk = self._calculate_reputation_risk(
            investment["controversy_score"], 
            len(active_issues)
        )
        
        return {
            "controversy_score": f"{investment['controversy_score']}/10",
            "controversy_level": controversy_level,
            "active_controversies": len(active_issues),
            "recent_issues": [issue["type"] for issue in active_issues[-3:]],
            "risk_factors": risk_factors,
            "greenwashing_risk": greenwashing_risk,
            "regulatory_risk": regulatory_risk,
            "reputation_risk": reputation_risk,
            "exclusion_flags": self._check_exclusion_criteria(investment),
            "risk_mitigation": self._suggest_risk_mitigation(controversy_level, risk_factors),
            "divestment_trigger": performance.get("controversy_alert", False)
        }
        
    async def _values_agent_analysis(self, investment: Dict, performance: Dict) -> Dict[str, Any]:
        """Analyze values alignment"""
        # Theme alignment
        aligned_themes = self._find_aligned_themes(investment["symbol"])
        
        # Values match score
        values_match = self._calculate_values_match(investment, "balanced_esg")
        
        # Exclusion check
        exclusions = self._check_values_exclusions(investment)
        
        # Positive screening
        positive_factors = self._identify_positive_factors(investment)
        
        # Mission alignment
        mission_score = self._assess_mission_alignment(investment)
        
        return {
            "aligned_themes": aligned_themes,
            "values_match": f"{values_match:.0f}%",
            "positive_factors": positive_factors,
            "exclusions_passed": len(exclusions) == 0,
            "exclusion_details": exclusions,
            "mission_alignment": f"{mission_score}/10",
            "investment_thesis": self._generate_values_thesis(investment, aligned_themes),
            "stakeholder_benefit": self._assess_stakeholder_benefit(investment),
            "long_term_alignment": self._evaluate_long_term_alignment(investment)
        }
        
    async def _build_esg_consensus(self, esg: Dict, impact: Dict, risk: Dict, values: Dict) -> Dict[str, Any]:
        """Build multi-agent consensus for ESG investment"""
        scores = []
        
        # ESG score (normalized)
        esg_score = float(esg["overall_score"].split("/")[0]) / 10
        scores.append(esg_score)
        
        # Impact score (normalized)
        impact_score = float(impact["impact_score"].split("/")[0]) / 100
        scores.append(impact_score)
        
        # Risk score (inverse of controversy)
        risk_score = 1 - (float(risk["controversy_score"].split("/")[0]) / 10)
        if risk["divestment_trigger"]:
            risk_score = 0
        scores.append(risk_score)
        
        # Values score
        values_score = float(values["values_match"].strip("%")) / 100
        scores.append(values_score)
        
        # Weighted consensus
        weights = [1.2, 1.5, 1.0, 1.3]  # Impact and values weighted higher
        weighted_score = sum(s * w for s, w in zip(scores, weights)) / sum(weights)
        
        # Determine action
        if risk["divestment_trigger"]:
            action = "DIVEST"
            recommendation = "Immediate divestment due to controversy"
        elif weighted_score > 0.8:
            action = "STRONG BUY"
            recommendation = "Excellent ESG profile with high impact"
        elif weighted_score > 0.65:
            action = "BUY"
            recommendation = "Good ESG investment opportunity"
        elif weighted_score > 0.5:
            action = "HOLD"
            recommendation = "Acceptable ESG profile"
        else:
            action = "REDUCE"
            recommendation = "Consider alternatives with better ESG scores"
            
        # Key highlights
        highlights = self._identify_esg_highlights(esg, impact, risk, values)
        
        return {
            "action": action,
            "confidence": f"{weighted_score * 100:.0f}%",
            "recommendation": recommendation,
            "esg_rating": esg["rating"],
            "impact_effectiveness": self._rate_impact_effectiveness(impact_score),
            "values_alignment": "High" if values_score > 0.8 else "Good" if values_score > 0.6 else "Moderate",
            "key_strengths": highlights["strengths"],
            "key_concerns": highlights["concerns"],
            "investment_thesis": self._build_esg_thesis(esg, impact, values),
            "monitoring_points": self._identify_monitoring_points(risk, esg)
        }
        
    def _rate_esg_score(self, score: float) -> str:
        """Rate ESG score"""
        if score >= 8.5:
            return "Excellent"
        elif score >= 7.5:
            return "Good"
        elif score >= 6.5:
            return "Average"
        else:
            return "Below Average"
            
    def _assess_carbon_intensity(self, intensity: float) -> str:
        """Assess carbon intensity level"""
        if intensity < 20:
            return "Very Low"
        elif intensity < 50:
            return "Low"
        elif intensity < 100:
            return "Moderate"
        elif intensity < 150:
            return "High"
        else:
            return "Very High"
            
    def _analyze_esg_trend(self, performance: Dict) -> str:
        """Analyze ESG score trend"""
        # Simulated trend based on performance
        if performance.get("esg_score_change", 0) > 0.5:
            return "Improving"
        elif performance.get("esg_score_change", 0) < -0.5:
            return "Deteriorating"
        else:
            return "Stable"
            
    def _identify_social_focus(self, investment: Dict) -> str:
        """Identify primary social focus"""
        if "Gender" in investment["name"]:
            return "Gender equality"
        elif "Minority" in investment["name"] or "NAACP" in investment["name"]:
            return "Racial equity"
        elif "Social" in investment["name"]:
            return "Social responsibility"
        else:
            return "Community impact"
            
    def _get_esg_recommendation(self, investment: Dict, rating: str) -> str:
        """Get ESG-based recommendation"""
        if rating == "Excellent" and investment["controversy_score"] < 1:
            return "Top ESG performer with minimal controversies"
        elif rating == "Good":
            return "Solid ESG credentials suitable for most portfolios"
        elif investment["carbon_intensity"] < 30:
            return "Low carbon leader in its category"
        else:
            return "Consider for diversified ESG exposure"
            
    def _calculate_environmental_impact(self, investment: Dict, metrics: Dict) -> Dict[str, Any]:
        """Calculate environmental impact details"""
        impact = {
            "carbon_reduction": "Not measured",
            "renewable_contribution": "Not measured",
            "environmental_benefit": "Standard"
        }
        
        if "co2_avoided" in metrics:
            impact["carbon_reduction"] = f"{metrics['co2_avoided']:,} tons CO2/year"
            impact["environmental_benefit"] = "High" if metrics['co2_avoided'] > 1000000 else "Moderate"
            
        if "renewable_capacity" in metrics:
            impact["renewable_contribution"] = f"{metrics['renewable_capacity']:,} MW capacity"
            
        if "water_saved" in metrics:
            impact["water_conservation"] = f"{metrics['water_saved']:,} gallons/year"
            
        return impact
        
    def _calculate_social_impact(self, investment: Dict, metrics: Dict) -> Dict[str, Any]:
        """Calculate social impact details"""
        impact = {
            "social_benefit": "Standard",
            "beneficiaries": "Not specified"
        }
        
        if "diversity_score" in metrics:
            impact["diversity_impact"] = f"{metrics['diversity_score']}/10 diversity score"
            
        if "community_investment" in metrics:
            impact["community_benefit"] = f"${metrics['community_investment']:,} invested"
            
        if "minority_employment" in metrics:
            impact["employment_impact"] = f"{metrics['minority_employment']}% minority employment"
            
        if "water_access" in metrics:
            impact["beneficiaries"] = f"{metrics['water_access']:,} people with water access"
            
        return impact
        
    def _identify_tangible_outcomes(self, metrics: Dict) -> List[str]:
        """Identify tangible real-world outcomes"""
        outcomes = []
        
        if "co2_avoided" in metrics and metrics["co2_avoided"] > 0:
            outcomes.append(f"Avoids {metrics['co2_avoided']:,} tons of CO2 annually")
            
        if "green_jobs" in metrics:
            outcomes.append(f"Supports {metrics['green_jobs']:,} green jobs")
            
        if "clean_energy_homes" in metrics:
            outcomes.append(f"Powers {metrics['clean_energy_homes']:,} homes with clean energy")
            
        if "water_access" in metrics:
            outcomes.append(f"Provides water access to {metrics['water_access']:,} people")
            
        if "sustainable_farming" in metrics:
            outcomes.append(f"Converts {metrics['sustainable_farming']:,} acres to sustainable farming")
            
        return outcomes[:3]  # Top 3 outcomes
        
    def _assess_sdg_alignment(self, investment: Dict) -> List[str]:
        """Assess UN Sustainable Development Goals alignment"""
        sdg_alignment = []
        
        # Climate action (SDG 13)
        if investment["category"] == "Environmental" or investment["carbon_intensity"] < 50:
            sdg_alignment.append("SDG 13: Climate Action")
            
        # Clean energy (SDG 7)
        if investment["renewable_exposure"] > 50:
            sdg_alignment.append("SDG 7: Affordable Clean Energy")
            
        # Clean water (SDG 6)
        if "Water" in investment["name"]:
            sdg_alignment.append("SDG 6: Clean Water & Sanitation")
            
        # Gender equality (SDG 5)
        if "Gender" in investment["name"] or "SHE" in investment["symbol"]:
            sdg_alignment.append("SDG 5: Gender Equality")
            
        # Reduced inequalities (SDG 10)
        if "Social" in investment["type"] or "Minority" in investment["name"]:
            sdg_alignment.append("SDG 10: Reduced Inequalities")
            
        return sdg_alignment[:3]
        
    def _format_impact_metrics(self, metrics: Dict) -> Dict[str, str]:
        """Format impact metrics for display"""
        formatted = {}
        
        for key, value in metrics.items():
            if isinstance(value, int) and value > 1000:
                formatted[key.replace("_", " ").title()] = f"{value:,}"
            elif isinstance(value, (int, float)):
                formatted[key.replace("_", " ").title()] = str(value)
                
        return formatted
        
    def _assess_impact_verification(self, investment: Dict) -> str:
        """Assess how well impact is verified"""
        if investment["type"].endswith("ETF") and investment["aum"] > 1000000000:
            return "Third-party verified"
        elif investment["controversy_score"] < 0.5:
            return "Independently audited"
        else:
            return "Self-reported"
            
    def _get_impact_recommendation(self, impact_score: float) -> str:
        """Get impact-based recommendation"""
        if impact_score > 90:
            return "Exceptional impact profile - maximizes positive outcomes"
        elif impact_score > 75:
            return "Strong impact potential with measurable benefits"
        elif impact_score > 60:
            return "Good impact profile suitable for values-based investing"
        else:
            return "Moderate impact - consider higher impact alternatives"
            
    def _assess_controversy_level(self, score: float) -> str:
        """Assess controversy level"""
        if score == 0:
            return "None"
        elif score < 1:
            return "Minimal"
        elif score < 3:
            return "Low"
        elif score < 5:
            return "Moderate"
        else:
            return "High"
            
    def _identify_esg_risks(self, investment: Dict) -> List[str]:
        """Identify ESG-related risks"""
        risks = []
        
        if investment["carbon_intensity"] > 100:
            risks.append("High carbon intensity")
            
        if investment["controversy_score"] > 2:
            risks.append("Elevated controversy risk")
            
        if investment["governance_score"] < 7:
            risks.append("Governance concerns")
            
        if investment["renewable_exposure"] < 20 and investment["category"] == "Environmental":
            risks.append("Limited renewable exposure")
            
        if investment["expense_ratio"] > 0.5:
            risks.append("High expense ratio")
            
        return risks
        
    def _assess_greenwashing_risk(self, investment: Dict) -> str:
        """Assess greenwashing risk"""
        # High ESG score but high carbon intensity
        if investment["esg_score"] > 8 and investment["carbon_intensity"] > 150:
            return "High"
            
        # Environmental focus but low renewable exposure
        if investment["category"] == "Environmental" and investment["renewable_exposure"] < 30:
            return "Moderate"
            
        # Good verification and alignment
        if investment["controversy_score"] < 1 and investment["esg_score"] > 7.5:
            return "Low"
            
        return "Moderate"
        
    def _assess_regulatory_risk(self, investment: Dict) -> str:
        """Assess regulatory risk"""
        if investment["category"] == "Environmental":
            return "Low - regulatory tailwinds"
        elif investment["controversy_score"] > 3:
            return "High - potential scrutiny"
        else:
            return "Moderate - standard oversight"
            
    def _calculate_reputation_risk(self, controversy_score: float, active_issues: int) -> str:
        """Calculate reputation risk"""
        risk_score = controversy_score + (active_issues * 2)
        
        if risk_score > 8:
            return "High"
        elif risk_score > 5:
            return "Moderate"
        elif risk_score > 2:
            return "Low"
        else:
            return "Minimal"
            
    def _check_exclusion_criteria(self, investment: Dict) -> List[str]:
        """Check for exclusion criteria"""
        exclusions = []
        
        # Check carbon intensity
        if investment["carbon_intensity"] > 200:
            exclusions.append("Excessive carbon footprint")
            
        # Check controversy
        if investment["controversy_score"] > 5:
            exclusions.append("High controversy score")
            
        # Check category-specific exclusions
        if investment["renewable_exposure"] < 10 and investment["category"] == "Environmental":
            exclusions.append("Insufficient green exposure")
            
        return exclusions
        
    def _suggest_risk_mitigation(self, controversy_level: str, risks: List[str]) -> List[str]:
        """Suggest risk mitigation strategies"""
        suggestions = []
        
        if controversy_level in ["Moderate", "High"]:
            suggestions.append("Monitor news for emerging issues")
            suggestions.append("Set stop-loss at -10%")
            
        if "High carbon intensity" in risks:
            suggestions.append("Balance with low-carbon investments")
            
        if "Governance concerns" in risks:
            suggestions.append("Review proxy voting policies")
            
        return suggestions
        
    def _find_aligned_themes(self, symbol: str) -> List[str]:
        """Find aligned ESG themes"""
        aligned = []
        
        for theme, data in self.esg_themes.items():
            if symbol in data["investments"]:
                aligned.append(theme)
                
        return aligned
        
    def _calculate_values_match(self, investment: Dict, profile: str) -> float:
        """Calculate values match percentage"""
        weights = self.values_profiles[profile]
        
        match_score = (
            investment["environmental_score"] * weights["environmental"] +
            investment["social_score"] * weights["social"] +
            investment["governance_score"] * weights["governance"]
        ) * 10
        
        # Bonus for low controversy
        if investment["controversy_score"] < 1:
            match_score += 5
            
        return min(100, match_score)
        
    def _check_values_exclusions(self, investment: Dict) -> List[str]:
        """Check for values-based exclusions"""
        exclusions = []
        
        # Environmental exclusions
        if investment["carbon_intensity"] > 150:
            exclusions.append("High carbon emitter")
            
        # Social exclusions
        if investment["social_score"] < 6:
            exclusions.append("Poor social practices")
            
        # Controversy exclusions
        if investment["controversy_score"] > 3:
            exclusions.append("Significant controversies")
            
        return exclusions
        
    def _identify_positive_factors(self, investment: Dict) -> List[str]:
        """Identify positive ESG factors"""
        factors = []
        
        if investment["environmental_score"] > 8.5:
            factors.append("Environmental leader")
            
        if investment["renewable_exposure"] > 80:
            factors.append("High renewable exposure")
            
        if investment["social_score"] > 8.5:
            factors.append("Social impact champion")
            
        if investment["controversy_score"] == 0:
            factors.append("Controversy-free")
            
        if investment["carbon_intensity"] < 20:
            factors.append("Ultra-low carbon")
            
        return factors[:3]
        
    def _assess_mission_alignment(self, investment: Dict) -> float:
        """Assess mission alignment score"""
        score = 5.0  # Base score
        
        # Category alignment
        if investment["category"] in ["Environmental", "Social"]:
            score += 2
            
        # Impact metrics
        if "impact_metrics" in investment and len(investment["impact_metrics"]) > 3:
            score += 1.5
            
        # ESG leadership
        if investment["esg_score"] > 8:
            score += 1.5
            
        return min(10, score)
        
    def _generate_values_thesis(self, investment: Dict, themes: List[str]) -> str:
        """Generate values-based investment thesis"""
        if len(themes) > 0:
            return f"Aligns with {', '.join(themes)} priorities"
        elif investment["esg_score"] > 8:
            return "ESG leader across all dimensions"
        elif investment["category"] == "Environmental":
            return "Supports environmental sustainability"
        elif investment["category"] == "Social":
            return "Advances social equity and justice"
        else:
            return "Promotes responsible investing"
            
    def _assess_stakeholder_benefit(self, investment: Dict) -> str:
        """Assess stakeholder benefits"""
        if investment["type"] == "Clean Energy ETF":
            return "Benefits environment and future generations"
        elif investment["type"] == "Social Impact ETF":
            return "Benefits underserved communities"
        elif investment["type"] == "Gender Diversity ETF":
            return "Promotes workplace equality"
        else:
            return "Creates shared value for all stakeholders"
            
    def _evaluate_long_term_alignment(self, investment: Dict) -> str:
        """Evaluate long-term values alignment"""
        if investment["renewable_exposure"] > 80:
            return "Excellent - future-proof investment"
        elif investment["esg_score"] > 8 and investment["controversy_score"] < 1:
            return "Strong - sustained ESG leadership"
        elif investment["category"] in ["Environmental", "Social"]:
            return "Good - thematic alignment"
        else:
            return "Moderate - general ESG integration"
            
    def _rate_impact_effectiveness(self, score: float) -> str:
        """Rate impact effectiveness"""
        if score > 0.9:
            return "Exceptional"
        elif score > 0.75:
            return "High"
        elif score > 0.6:
            return "Good"
        else:
            return "Moderate"
            
    def _identify_esg_highlights(self, esg: Dict, impact: Dict, risk: Dict, values: Dict) -> Dict[str, List[str]]:
        """Identify key highlights and concerns"""
        strengths = []
        concerns = []
        
        # Strengths
        if float(esg["overall_score"].split("/")[0]) > 8:
            strengths.append("Excellent ESG ratings")
        if float(impact["impact_score"].split("/")[0]) > 80:
            strengths.append("High measurable impact")
        if values["exclusions_passed"]:
            strengths.append("Passes all values screens")
        if len(values["aligned_themes"]) > 0:
            strengths.append(f"Aligns with {len(values['aligned_themes'])} themes")
            
        # Concerns
        if risk["divestment_trigger"]:
            concerns.append("Active controversy requires divestment")
        if float(risk["controversy_score"].split("/")[0]) > 3:
            concerns.append("Elevated controversy risk")
        if risk["greenwashing_risk"] == "High":
            concerns.append("Potential greenwashing")
        if len(risk["risk_factors"]) > 2:
            concerns.append("Multiple risk factors")
            
        return {"strengths": strengths, "concerns": concerns}
        
    def _build_esg_thesis(self, esg: Dict, impact: Dict, values: Dict) -> str:
        """Build comprehensive ESG investment thesis"""
        if esg["rating"] == "Excellent" and float(impact["impact_score"].split("/")[0]) > 80:
            return "Best-in-class ESG leader with exceptional real-world impact"
        elif len(values["aligned_themes"]) > 1:
            return f"Strong thematic alignment with {', '.join(values['aligned_themes'])}"
        elif esg["environmental"]["carbon_rating"] in ["Very Low", "Low"]:
            return "Climate-positive investment supporting net-zero transition"
        else:
            return "Solid ESG investment for values-based portfolio"
            
    def _identify_monitoring_points(self, risk: Dict, esg: Dict) -> List[str]:
        """Identify key monitoring points"""
        points = []
        
        if float(risk["controversy_score"].split("/")[0]) > 2:
            points.append("Monitor for new controversies")
            
        if risk["greenwashing_risk"] in ["High", "Moderate"]:
            points.append("Verify impact claims quarterly")
            
        if esg["trend"] == "Deteriorating":
            points.append("Track ESG score changes")
            
        points.append("Review impact metrics annually")
        
        return points
        
    def check_controversy(self, symbol: str) -> Dict[str, Any]:
        """Check for new controversies"""
        # Simulate controversy detection
        if random.random() < 0.05:  # 5% chance of controversy
            controversy_type = random.choice(list(self.controversy_events.keys()))
            severity = abs(self.controversy_events[controversy_type])
            
            if symbol not in self.active_controversies:
                self.active_controversies[symbol] = []
                
            self.active_controversies[symbol].append({
                "type": controversy_type,
                "severity": severity,
                "date": datetime.now(),
                "impact": self.controversy_events[controversy_type]
            })
            
            # Update performance
            if symbol in self.investment_performance:
                self.investment_performance[symbol]["controversy_alert"] = True
                self.investment_performance[symbol]["esg_score_change"] = \
                    self.controversy_events[controversy_type] * 0.1
                    
            return {
                "controversy_detected": True,
                "type": controversy_type,
                "severity": "High" if severity > 3 else "Medium" if severity > 2 else "Low",
                "action_required": "DIVEST" if severity > 3 else "MONITOR",
                "impact": f"{self.controversy_events[controversy_type]}% price impact expected"
            }
            
        return {"controversy_detected": False}
        
    def update_prices(self):
        """Update ESG investment prices"""
        for inv_id, performance in self.investment_performance.items():
            investment = self.esg_investments[inv_id]
            
            # Base price movement
            volatility = 0.15  # ESG investments tend to be less volatile
            daily_move = random.gauss(0, volatility / math.sqrt(252))
            
            # ESG momentum
            if investment["esg_score"] > 8:
                daily_move += 0.0002  # Slight outperformance
                
            # Category trends
            if investment["category"] == "Environmental":
                daily_move += 0.0003  # Green premium
            elif investment["category"] == "Social":
                daily_move += 0.0001
                
            # Controversy impact
            if performance.get("controversy_alert", False):
                daily_move -= 0.01  # Sharp drop on controversy
                
            # Apply price change
            old_price = performance["current_price"]
            new_price = old_price * (1 + daily_move)
            
            performance["current_price"] = new_price
            performance["daily_change"] = new_price - old_price
            performance["daily_change_percent"] = daily_move * 100
            
            # Update returns
            performance["weekly_return"] = performance["weekly_return"] * 0.8 + daily_move * 100 * 5
            performance["monthly_return"] = performance["monthly_return"] * 0.95 + daily_move * 100 * 2
            
            # Update impact score (can improve with engagement)
            if random.random() < 0.1:  # 10% chance of impact change
                performance["impact_score"] = min(100, performance["impact_score"] + random.uniform(-2, 3))
                
    async def screen_portfolio_values(self, portfolio: List[Dict], values_profile: str = "balanced_esg") -> Dict[str, Any]:
        """Screen portfolio for values alignment"""
        aligned_investments = []
        exclusion_list = []
        improvement_opportunities = []
        
        for position in portfolio:
            investment = self.esg_investments.get(position["investment_id"])
            if not investment:
                continue
                
            # Values match
            match_score = self._calculate_values_match(investment, values_profile)
            
            # Exclusion check
            exclusions = self._check_values_exclusions(investment)
            
            if len(exclusions) == 0 and match_score > 60:
                aligned_investments.append({
                    "investment": investment["name"],
                    "match_score": match_score,
                    "strengths": self._identify_positive_factors(investment)
                })
            else:
                exclusion_list.append({
                    "investment": investment["name"],
                    "reasons": exclusions,
                    "action": "Divest" if len(exclusions) > 1 else "Review"
                })
                
            # Improvement opportunities
            if match_score > 50 and match_score < 80:
                improvements = self._suggest_improvements(investment)
                if improvements:
                    improvement_opportunities.append({
                        "investment": investment["name"],
                        "current_score": match_score,
                        "improvements": improvements
                    })
                    
        return {
            "values_profile": values_profile,
            "aligned_count": len(aligned_investments),
            "exclusion_count": len(exclusion_list),
            "portfolio_values_score": sum(inv["match_score"] for inv in aligned_investments) / len(aligned_investments) if aligned_investments else 0,
            "aligned_investments": aligned_investments,
            "exclusions": exclusion_list,
            "improvement_opportunities": improvement_opportunities,
            "recommendations": self._generate_portfolio_recommendations(aligned_investments, exclusion_list)
        }
        
    def _suggest_improvements(self, investment: Dict) -> List[str]:
        """Suggest improvements for borderline investments"""
        improvements = []
        
        if investment["carbon_intensity"] > 100:
            improvements.append("Engage on carbon reduction targets")
            
        if investment["social_score"] < 7:
            improvements.append("Advocate for better labor practices")
            
        if investment["governance_score"] < 7:
            improvements.append("Push for board diversity")
            
        return improvements
        
    def _generate_portfolio_recommendations(self, aligned: List[Dict], exclusions: List[Dict]) -> List[str]:
        """Generate portfolio-level recommendations"""
        recommendations = []
        
        if len(exclusions) > 0:
            recommendations.append(f"Divest from {len(exclusions)} investments failing values screen")
            
        avg_score = sum(inv["match_score"] for inv in aligned) / len(aligned) if aligned else 0
        if avg_score < 70:
            recommendations.append("Consider higher-impact ESG investments")
            
        if len(aligned) < 5:
            recommendations.append("Increase ESG allocation for better diversification")
            
        recommendations.append("Set up quarterly impact review process")
        
        return recommendations
        
    async def calculate_portfolio_impact(self, positions: List[Dict]) -> Dict[str, Any]:
        """Calculate total portfolio impact"""
        total_impact = {
            "co2_avoided": 0,
            "renewable_capacity": 0,
            "people_benefited": 0,
            "water_saved": 0,
            "green_jobs": 0
        }
        
        impact_investments = []
        
        for position in positions:
            investment = self.esg_investments.get(position["investment_id"])
            if not investment or "impact_metrics" not in investment:
                continue
                
            metrics = investment["impact_metrics"]
            weight = position["value"] / sum(p["value"] for p in positions)
            
            # Aggregate impacts
            if "co2_avoided" in metrics:
                total_impact["co2_avoided"] += metrics["co2_avoided"] * weight
            if "renewable_capacity" in metrics:
                total_impact["renewable_capacity"] += metrics["renewable_capacity"] * weight
            if "water_access" in metrics:
                total_impact["people_benefited"] += metrics["water_access"] * weight
            if "water_saved" in metrics:
                total_impact["water_saved"] += metrics["water_saved"] * weight
            if "green_jobs" in metrics:
                total_impact["green_jobs"] += int(metrics["green_jobs"] * weight)
                
            impact_investments.append({
                "investment": investment["name"],
                "category": investment["category"],
                "primary_impact": self._identify_primary_impact(metrics)
            })
            
        # Calculate impact score
        portfolio_impact_score = self._calculate_portfolio_impact_score(total_impact, len(positions))
        
        return {
            "total_impacts": {
                "CO2 Avoided": f"{int(total_impact['co2_avoided']):,} tons/year",
                "Renewable Capacity": f"{int(total_impact['renewable_capacity']):,} MW",
                "People Benefited": f"{int(total_impact['people_benefited']):,}",
                "Water Saved": f"{int(total_impact['water_saved']):,} gallons/year",
                "Green Jobs Supported": f"{int(total_impact['green_jobs']):,}"
            },
            "portfolio_impact_score": f"{portfolio_impact_score:.1f}/100",
            "impact_rating": self._rate_portfolio_impact(portfolio_impact_score),
            "sdg_contributions": self._calculate_sdg_contributions(impact_investments),
            "carbon_footprint": self._calculate_portfolio_carbon_footprint(positions),
            "recommendations": self._generate_impact_recommendations(portfolio_impact_score, total_impact)
        }
        
    def _identify_primary_impact(self, metrics: Dict) -> str:
        """Identify primary impact area"""
        if "co2_avoided" in metrics and metrics["co2_avoided"] > 1000000:
            return "Climate action"
        elif "water_access" in metrics:
            return "Water access"
        elif "minority_employment" in metrics:
            return "Social equity"
        elif "renewable_capacity" in metrics:
            return "Clean energy"
        else:
            return "Sustainable development"
            
    def _calculate_portfolio_impact_score(self, impacts: Dict, num_investments: int) -> float:
        """Calculate overall portfolio impact score"""
        score = 50  # Base score
        
        # Climate impact
        if impacts["co2_avoided"] > 1000000:
            score += 20
        elif impacts["co2_avoided"] > 500000:
            score += 10
            
        # Social impact
        if impacts["people_benefited"] > 1000000:
            score += 15
        elif impacts["people_benefited"] > 100000:
            score += 8
            
        # Renewable impact
        if impacts["renewable_capacity"] > 10000:
            score += 15
        elif impacts["renewable_capacity"] > 5000:
            score += 8
            
        # Diversification bonus
        if num_investments > 5:
            score += 5
            
        return min(100, score)
        
    def _rate_portfolio_impact(self, score: float) -> str:
        """Rate portfolio impact level"""
        if score > 85:
            return "Exceptional Impact"
        elif score > 70:
            return "High Impact"
        elif score > 55:
            return "Good Impact"
        else:
            return "Moderate Impact"
            
    def _calculate_sdg_contributions(self, investments: List[Dict]) -> List[str]:
        """Calculate SDG contributions"""
        sdg_count = {}
        
        for inv in investments:
            if inv["category"] == "Environmental":
                sdg_count["SDG 13: Climate Action"] = sdg_count.get("SDG 13: Climate Action", 0) + 1
                sdg_count["SDG 7: Clean Energy"] = sdg_count.get("SDG 7: Clean Energy", 0) + 1
            elif inv["category"] == "Social":
                sdg_count["SDG 10: Reduced Inequalities"] = sdg_count.get("SDG 10: Reduced Inequalities", 0) + 1
                sdg_count["SDG 5: Gender Equality"] = sdg_count.get("SDG 5: Gender Equality", 0) + 1
                
        # Return top 3 SDGs
        sorted_sdgs = sorted(sdg_count.items(), key=lambda x: x[1], reverse=True)
        return [sdg[0] for sdg in sorted_sdgs[:3]]
        
    def _calculate_portfolio_carbon_footprint(self, positions: List[Dict]) -> str:
        """Calculate weighted portfolio carbon footprint"""
        total_intensity = 0
        total_weight = 0
        
        for position in positions:
            investment = self.esg_investments.get(position["investment_id"])
            if investment:
                weight = position["value"]
                total_intensity += investment["carbon_intensity"] * weight
                total_weight += weight
                
        avg_intensity = total_intensity / total_weight if total_weight > 0 else 0
        
        return f"{avg_intensity:.1f} tCO2e/$M revenue"
        
    def _generate_impact_recommendations(self, score: float, impacts: Dict) -> List[str]:
        """Generate impact improvement recommendations"""
        recommendations = []
        
        if score < 70:
            recommendations.append("Increase allocation to high-impact investments")
            
        if impacts["co2_avoided"] < 500000:
            recommendations.append("Add more climate-focused investments")
            
        if impacts["people_benefited"] < 100000:
            recommendations.append("Consider social impact investments")
            
        recommendations.append("Track and report impact metrics quarterly")
        
        return recommendations 