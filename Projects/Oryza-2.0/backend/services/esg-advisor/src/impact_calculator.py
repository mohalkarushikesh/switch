"""
Impact Calculator - Calculates real-world impact of investments
"""
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import numpy as np
import logging

from .models import ImpactMetric, ImpactStory


class ImpactCalculator:
    """
    Calculates and measures real-world impact of sustainable investments
    """
    
    def __init__(self):
        self.logger = logging.getLogger("impact_calculator")
        self.sdg_goals = {
            1: "No Poverty",
            2: "Zero Hunger", 
            3: "Good Health and Well-being",
            4: "Quality Education",
            5: "Gender Equality",
            6: "Clean Water and Sanitation",
            7: "Affordable and Clean Energy",
            8: "Decent Work and Economic Growth",
            9: "Industry, Innovation and Infrastructure",
            10: "Reduced Inequalities",
            11: "Sustainable Cities and Communities",
            12: "Responsible Consumption and Production",
            13: "Climate Action",
            14: "Life Below Water",
            15: "Life on Land",
            16: "Peace, Justice and Strong Institutions",
            17: "Partnerships for the Goals"
        }
        
    async def initialize(self):
        """Initialize the impact calculator"""
        self.logger.info("Initializing Impact Calculator")
        # In production, connect to impact databases
        await asyncio.sleep(0.1)  # Simulate initialization
        
    async def calculate_carbon_footprint(
        self,
        portfolio_id: str,
        asset_analyses: List[Dict[str, Any]]
    ) -> Dict[str, float]:
        """
        Calculate portfolio carbon footprint
        """
        total_value = sum(a["asset"].allocation * 100000 for a in asset_analyses)  # Assume 100k portfolio
        
        total_emissions = 0
        for analysis in asset_analyses:
            # In production, use real emissions data
            # Mock calculation based on sector
            sector_emissions = self._get_sector_emissions(analysis["asset"].asset_class)
            asset_value = analysis["asset"].allocation * 100000
            
            # Emissions in tons CO2e per $1M revenue
            emissions_intensity = sector_emissions * (asset_value / 1000000)
            total_emissions += emissions_intensity
        
        # Calculate various carbon metrics
        return {
            "total_emissions": total_emissions,
            "intensity": total_emissions / (total_value / 1000000),  # per $M invested
            "avoided_emissions": self._calculate_avoided_emissions(asset_analyses),
            "offset_equivalent": total_emissions * 25,  # Trees needed to offset
            "comparison": {
                "vs_market": -15.5,  # % less than market average
                "vs_peers": -8.2     # % less than peer group
            }
        }
    
    def _get_sector_emissions(self, asset_class: str) -> float:
        """Get average emissions by sector"""
        # Tons CO2e per $1M revenue
        sector_emissions = {
            "equity": 150,
            "fixed_income": 100,
            "real_estate": 200,
            "commodities": 300,
            "alternatives": 120
        }
        return sector_emissions.get(asset_class, 150)
    
    def _calculate_avoided_emissions(
        self,
        asset_analyses: List[Dict[str, Any]]
    ) -> float:
        """Calculate emissions avoided through green investments"""
        avoided = 0
        
        for analysis in asset_analyses:
            # Check if it's a green investment
            esg_score = analysis["analysis"]["scores"]["environmental"].score
            if esg_score > 75:
                # High ESG score indicates potential emissions avoidance
                allocation_value = analysis["asset"].allocation * 100000
                # Rough estimate: 50 tons CO2e avoided per $1M in green investments
                avoided += (allocation_value / 1000000) * 50
        
        return avoided
    
    async def assess_sdg_alignment(
        self,
        asset_analyses: List[Dict[str, Any]]
    ) -> Dict[int, float]:
        """
        Assess portfolio alignment with UN Sustainable Development Goals
        """
        sdg_alignment = {i: 0.0 for i in range(1, 18)}
        total_weight = sum(a["weight"] for a in asset_analyses)
        
        for analysis in asset_analyses:
            weight = analysis["weight"] / total_weight
            
            # In production, use real SDG mapping
            # Mock mapping based on asset characteristics
            asset_sdgs = self._map_asset_to_sdgs(analysis)
            
            for sdg, alignment in asset_sdgs.items():
                sdg_alignment[sdg] += alignment * weight
        
        # Filter out SDGs with minimal alignment
        return {k: v for k, v in sdg_alignment.items() if v > 0.05}
    
    def _map_asset_to_sdgs(self, analysis: Dict[str, Any]) -> Dict[int, float]:
        """Map asset to relevant SDGs"""
        # In production, use sophisticated SDG mapping
        # Simple mock based on ESG scores
        mapping = {}
        
        env_score = analysis["analysis"]["scores"]["environmental"].score
        soc_score = analysis["analysis"]["scores"]["social"].score
        gov_score = analysis["analysis"]["scores"]["governance"].score
        
        # Environmental focus
        if env_score > 70:
            mapping[7] = 0.3   # Clean Energy
            mapping[13] = 0.4  # Climate Action
            mapping[6] = 0.2   # Clean Water
        
        # Social focus
        if soc_score > 70:
            mapping[3] = 0.3   # Good Health
            mapping[4] = 0.2   # Quality Education
            mapping[5] = 0.2   # Gender Equality
            mapping[8] = 0.3   # Decent Work
        
        # Governance focus
        if gov_score > 70:
            mapping[16] = 0.4  # Peace & Justice
            mapping[17] = 0.2  # Partnerships
        
        return mapping
    
    async def calculate_impact(
        self,
        portfolio_id: str,
        time_period: str = "1Y"
    ) -> Dict[str, Any]:
        """
        Calculate comprehensive impact metrics
        """
        # In production, aggregate real impact data
        # Mock calculations
        
        portfolio_value = 100000  # Example portfolio value
        
        # Environmental impact
        carbon_avoided = 15.5  # tons CO2e
        renewable_energy = carbon_avoided * 2000  # kWh equivalent
        water_saved = 50000  # gallons
        waste_diverted = 2.5  # tons
        
        # Social impact
        jobs_supported = int(portfolio_value / 50000)  # 1 job per $50k
        communities = 5
        people_helped = {
            "healthcare_access": 150,
            "education_access": 75,
            "clean_water_access": 200
        }
        
        # SDG contributions
        sdg_contributions = {
            3: {"impact": "Provided healthcare to 150 people", "value": 150},
            4: {"impact": "Funded education for 75 students", "value": 75},
            6: {"impact": "Clean water access for 200 people", "value": 200},
            7: {"impact": f"Generated {renewable_energy} kWh clean energy", "value": renewable_energy},
            8: {"impact": f"Supported {jobs_supported} jobs", "value": jobs_supported},
            13: {"impact": f"Avoided {carbon_avoided} tons CO2e", "value": carbon_avoided}
        }
        
        return {
            "carbon_avoided": carbon_avoided,
            "renewable_energy": renewable_energy,
            "water_saved": water_saved,
            "waste_diverted": waste_diverted,
            "jobs_supported": jobs_supported,
            "communities": communities,
            "people_helped": people_helped,
            "sdg_contributions": sdg_contributions
        }
    
    async def generate_impact_stories(
        self,
        impact_metrics: Dict[str, Any]
    ) -> List[ImpactStory]:
        """
        Generate human-readable impact stories
        """
        stories = []
        
        # Carbon impact story
        if impact_metrics["carbon_avoided"] > 10:
            stories.append(ImpactStory(
                title="Fighting Climate Change",
                description=f"Your investments helped avoid {impact_metrics['carbon_avoided']} tons of CO2 emissions - equivalent to taking {int(impact_metrics['carbon_avoided'] / 4.6)} cars off the road for a year.",
                metrics=[
                    ImpactMetric(
                        metric_name="CO2 Avoided",
                        value=impact_metrics["carbon_avoided"],
                        unit="tons",
                        description="Carbon dioxide emissions prevented",
                        calculation_method="Scope 1 & 2 emissions analysis",
                        confidence_level=0.85
                    )
                ],
                beneficiaries="Global climate",
                location="Worldwide"
            ))
        
        # Jobs impact story
        if impact_metrics["jobs_supported"] > 0:
            stories.append(ImpactStory(
                title="Creating Economic Opportunities",
                description=f"Your portfolio supports {impact_metrics['jobs_supported']} jobs across sustainable industries, contributing to economic growth and community development.",
                metrics=[
                    ImpactMetric(
                        metric_name="Jobs Supported",
                        value=impact_metrics["jobs_supported"],
                        unit="FTE jobs",
                        description="Full-time equivalent jobs supported",
                        calculation_method="Input-output economic modeling",
                        confidence_level=0.75
                    )
                ],
                beneficiaries=f"{impact_metrics['jobs_supported']} workers and their families",
                location="Various communities"
            ))
        
        # Clean energy story
        if impact_metrics["renewable_energy"] > 1000:
            stories.append(ImpactStory(
                title="Powering a Clean Future",
                description=f"Your investments in renewable energy generated {impact_metrics['renewable_energy']:,.0f} kWh of clean electricity - enough to power {int(impact_metrics['renewable_energy'] / 10500)} homes for a year.",
                metrics=[
                    ImpactMetric(
                        metric_name="Clean Energy Generated",
                        value=impact_metrics["renewable_energy"],
                        unit="kWh",
                        description="Renewable electricity generated",
                        calculation_method="Direct project output measurement",
                        confidence_level=0.90
                    )
                ],
                beneficiaries="Local communities using clean energy",
                location="Renewable energy project sites"
            ))
        
        return stories
    
    async def create_visualizations(
        self,
        impact_metrics: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create data for impact visualizations
        """
        return {
            "carbon_gauge": {
                "type": "gauge",
                "value": impact_metrics["carbon_avoided"],
                "max": 50,
                "units": "tons CO2e",
                "color_scale": ["#ff4444", "#ffaa00", "#00aa00"]
            },
            "sdg_radar": {
                "type": "radar",
                "labels": [self.sdg_goals[k] for k in impact_metrics["sdg_contributions"].keys()],
                "values": [v["value"] for v in impact_metrics["sdg_contributions"].values()],
                "max_values": [200, 100, 250, 50000, 10, 20]
            },
            "impact_timeline": {
                "type": "line",
                "labels": ["Q1", "Q2", "Q3", "Q4"],
                "datasets": [
                    {
                        "label": "Carbon Avoided",
                        "data": [3.2, 6.8, 10.5, 15.5],
                        "color": "#00aa00"
                    },
                    {
                        "label": "Jobs Supported",
                        "data": [1, 1, 2, 2],
                        "color": "#0066cc"
                    }
                ]
            },
            "impact_map": {
                "type": "map",
                "locations": [
                    {"lat": 37.7749, "lng": -122.4194, "impact": "Solar farm: 5MW capacity"},
                    {"lat": 40.7128, "lng": -74.0060, "impact": "Green building: 200 jobs"},
                    {"lat": 51.5074, "lng": -0.1278, "impact": "Wind farm: 10MW capacity"}
                ]
            }
        }
    
    async def generate_report_pdf(
        self,
        impact_metrics: Dict[str, Any],
        impact_stories: List[ImpactStory]
    ) -> str:
        """
        Generate PDF impact report
        """
        # In production, generate actual PDF
        # Return mock URL
        report_id = f"impact_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        return f"https://reports.oryza.ai/{report_id}.pdf"
    
    async def project_future_impact(
        self,
        current_metrics: Dict[str, Any],
        time_horizon: str = "5Y"
    ) -> Dict[str, Any]:
        """
        Project future impact based on current trajectory
        """
        years = int(time_horizon[0])
        
        # Simple linear projection (in production, use sophisticated models)
        return {
            "carbon_avoided": current_metrics["carbon_avoided"] * years * 1.1,  # 10% annual growth
            "renewable_energy": current_metrics["renewable_energy"] * years * 1.15,
            "jobs_supported": int(current_metrics["jobs_supported"] * years * 1.05),
            "communities": current_metrics["communities"] * years,
            "confidence_interval": {
                "lower": 0.8,  # 80% of projected
                "upper": 1.3   # 130% of projected
            }
        } 