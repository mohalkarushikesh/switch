"""
Fixed Income Analyzer
Tracks yield curves, manages bond ladders, handles credit events, and adjusts duration
"""

import random
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import logging
import math

class FixedIncomeAnalyzer:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Bond universe
        self.bonds = {
            # Government Securities
            "GOI_2Y": {
                "name": "Government of India 2Y Bond",
                "type": "Government",
                "maturity": datetime.now() + timedelta(days=730),
                "coupon": 6.5,
                "yield": 6.8,
                "price": 98.50,
                "face_value": 100,
                "rating": "AAA",
                "duration": 1.85,
                "convexity": 4.2,
                "liquidity": "High",
                "min_investment": 10000
            },
            "GOI_5Y": {
                "name": "Government of India 5Y Bond",
                "type": "Government",
                "maturity": datetime.now() + timedelta(days=1825),
                "coupon": 7.2,
                "yield": 7.5,
                "price": 97.80,
                "face_value": 100,
                "rating": "AAA",
                "duration": 4.35,
                "convexity": 22.5,
                "liquidity": "High",
                "min_investment": 10000
            },
            "GOI_10Y": {
                "name": "Government of India 10Y Bond",
                "type": "Government",
                "maturity": datetime.now() + timedelta(days=3650),
                "coupon": 7.8,
                "yield": 8.1,
                "price": 96.50,
                "face_value": 100,
                "rating": "AAA",
                "duration": 7.85,
                "convexity": 75.3,
                "liquidity": "High",
                "min_investment": 10000
            },
            
            # State Development Loans
            "MH_SDL_5Y": {
                "name": "Maharashtra SDL 5Y",
                "type": "SDL",
                "maturity": datetime.now() + timedelta(days=1825),
                "coupon": 7.5,
                "yield": 7.9,
                "price": 97.20,
                "face_value": 100,
                "rating": "AA+",
                "duration": 4.25,
                "convexity": 21.8,
                "liquidity": "Medium",
                "min_investment": 25000
            },
            
            # Corporate Bonds
            "HDFC_3Y": {
                "name": "HDFC Ltd 3Y Bond",
                "type": "Corporate",
                "maturity": datetime.now() + timedelta(days=1095),
                "coupon": 8.2,
                "yield": 8.6,
                "price": 98.80,
                "face_value": 100,
                "rating": "AAA",
                "duration": 2.75,
                "convexity": 9.5,
                "liquidity": "Medium",
                "min_investment": 50000
            },
            "ICICI_5Y": {
                "name": "ICICI Bank 5Y Bond",
                "type": "Corporate",
                "maturity": datetime.now() + timedelta(days=1825),
                "coupon": 8.5,
                "yield": 8.9,
                "price": 97.60,
                "face_value": 100,
                "rating": "AAA",
                "duration": 4.15,
                "convexity": 20.8,
                "liquidity": "Medium",
                "min_investment": 50000
            },
            "TATA_7Y": {
                "name": "Tata Steel 7Y Bond",
                "type": "Corporate",
                "maturity": datetime.now() + timedelta(days=2555),
                "coupon": 9.2,
                "yield": 9.8,
                "price": 95.50,
                "face_value": 100,
                "rating": "AA",
                "duration": 5.85,
                "convexity": 40.2,
                "liquidity": "Low",
                "min_investment": 100000
            },
            
            # Tax-Free Bonds
            "NHAI_15Y": {
                "name": "NHAI Tax-Free Bond 15Y",
                "type": "Tax-Free",
                "maturity": datetime.now() + timedelta(days=5475),
                "coupon": 7.0,
                "yield": 7.3,
                "price": 97.00,
                "face_value": 100,
                "rating": "AAA",
                "duration": 10.25,
                "convexity": 135.6,
                "liquidity": "Low",
                "min_investment": 10000,
                "tax_free": True
            },
            
            # Perpetual Bonds
            "SBI_PERP": {
                "name": "SBI Perpetual Bond",
                "type": "Perpetual",
                "maturity": None,  # No maturity
                "coupon": 9.5,
                "yield": 10.2,
                "price": 93.10,
                "face_value": 100,
                "rating": "AA+",
                "duration": 9.8,
                "convexity": 120.5,
                "liquidity": "Low",
                "min_investment": 100000,
                "call_date": datetime.now() + timedelta(days=1825)
            }
        }
        
        # Yield curve data
        self.yield_curve = {
            "1M": 5.5,
            "3M": 6.0,
            "6M": 6.3,
            "1Y": 6.7,
            "2Y": 6.8,
            "3Y": 7.1,
            "5Y": 7.5,
            "7Y": 7.8,
            "10Y": 8.1,
            "15Y": 8.3,
            "20Y": 8.4,
            "30Y": 8.5
        }
        
        # Market conditions
        self.market_conditions = {
            "rate_environment": "rising",  # rising, falling, stable
            "credit_spreads": "widening",  # widening, tightening, stable
            "liquidity": "normal",  # abundant, normal, tight
            "inflation_expectation": 5.5,
            "repo_rate": 6.5,
            "reverse_repo": 6.0
        }
        
        # Bond performance tracking
        self.bond_performance = {}
        self._initialize_performance()
        
        # Ladder configurations
        self.ladder_strategies = {
            "conservative": {
                "rungs": 5,
                "max_maturity": 5,  # years
                "spacing": "equal",  # equal, barbell, bullet
                "credit_quality": ["AAA", "AA+"]
            },
            "moderate": {
                "rungs": 7,
                "max_maturity": 10,
                "spacing": "equal",
                "credit_quality": ["AAA", "AA+", "AA"]
            },
            "aggressive": {
                "rungs": 10,
                "max_maturity": 15,
                "spacing": "barbell",
                "credit_quality": ["AAA", "AA+", "AA", "AA-"]
            }
        }
        
        # Credit events tracking
        self.credit_events = []
        
    def _initialize_performance(self):
        """Initialize bond performance tracking"""
        for bond_id, bond_data in self.bonds.items():
            self.bond_performance[bond_id] = {
                "current_price": bond_data["price"],
                "current_yield": bond_data["yield"],
                "ytd_return": random.uniform(-2, 5),
                "modified_duration": bond_data["duration"] / (1 + bond_data["yield"]/100),
                "spread_to_govt": self._calculate_spread(bond_data),
                "accrued_interest": 0,
                "days_to_maturity": (bond_data["maturity"] - datetime.now()).days if bond_data["maturity"] else 999999
            }
            
    def _calculate_spread(self, bond: Dict) -> float:
        """Calculate spread over government securities"""
        if bond["type"] == "Government":
            return 0
        
        # Find comparable government bond
        govt_yield = self.yield_curve.get("10Y", 8.1)
        return bond["yield"] - govt_yield
        
    async def analyze_bond_multi_agent(self, bond_id: str) -> Dict[str, Any]:
        """Multi-agent analysis of a bond"""
        bond = self.bonds.get(bond_id)
        if not bond:
            return None
            
        performance = self.bond_performance[bond_id]
        
        # Fixed Income Agent Analysis
        fi_analysis = await self._fixed_income_agent_analysis(bond, performance)
        
        # Credit Agent Analysis
        credit_analysis = await self._credit_agent_analysis(bond, performance)
        
        # Duration Agent Analysis
        duration_analysis = await self._duration_agent_analysis(bond, performance)
        
        # Yield Agent Analysis
        yield_analysis = await self._yield_agent_analysis(bond, performance)
        
        # Build consensus
        consensus = await self._build_bond_consensus(
            fi_analysis, credit_analysis, duration_analysis, yield_analysis
        )
        
        return {
            "bond_id": bond_id,
            "bond_name": bond["name"],
            "current_price": performance["current_price"],
            "current_yield": performance["current_yield"],
            "agents": {
                "fixed_income": fi_analysis,
                "credit": credit_analysis,
                "duration": duration_analysis,
                "yield": yield_analysis
            },
            "consensus": consensus,
            "timestamp": datetime.now().isoformat()
        }
        
    async def _fixed_income_agent_analysis(self, bond: Dict, performance: Dict) -> Dict[str, Any]:
        """Analyze overall fixed income characteristics"""
        # Calculate metrics
        ytm = self._calculate_ytm(bond, performance["current_price"])
        total_return = self._calculate_total_return(bond, performance)
        
        # Analyze relative value
        fair_value = self._calculate_fair_value(bond)
        value_assessment = "Undervalued" if performance["current_price"] < fair_value * 0.98 else \
                          "Overvalued" if performance["current_price"] > fair_value * 1.02 else "Fair"
        
        return {
            "yield_to_maturity": f"{ytm:.2f}%",
            "current_yield": f"{(bond['coupon'] / performance['current_price']) * 100:.2f}%",
            "total_return_ytd": f"{total_return:.2f}%",
            "accrued_interest": f"₹{performance['accrued_interest']:.2f}",
            "days_to_maturity": performance["days_to_maturity"],
            "value_assessment": value_assessment,
            "fair_value": f"₹{fair_value:.2f}",
            "liquidity_score": self._get_liquidity_score(bond["liquidity"]),
            "recommendation": "Buy" if value_assessment == "Undervalued" else \
                            "Sell" if value_assessment == "Overvalued" else "Hold"
        }
        
    async def _credit_agent_analysis(self, bond: Dict, performance: Dict) -> Dict[str, Any]:
        """Analyze credit risk and events"""
        # Check for credit events
        recent_events = [
            event for event in self.credit_events 
            if event["bond_id"] == bond.get("bond_id") and 
            (datetime.now() - event["timestamp"]).days < 90
        ]
        
        # Credit metrics
        spread_trend = "Widening" if self.market_conditions["credit_spreads"] == "widening" else \
                      "Tightening" if self.market_conditions["credit_spreads"] == "tightening" else "Stable"
        
        # Default probability (simplified)
        default_prob = self._calculate_default_probability(bond["rating"])
        
        return {
            "credit_rating": bond["rating"],
            "rating_outlook": random.choice(["Stable", "Positive", "Negative"]),
            "spread_to_govt": f"{performance['spread_to_govt']:.2f}%",
            "spread_trend": spread_trend,
            "default_probability": f"{default_prob:.2f}%",
            "recovery_rate": f"{self._get_recovery_rate(bond['type'])}%",
            "credit_events": len(recent_events),
            "issuer_health": self._assess_issuer_health(bond),
            "downgrade_risk": "Low" if bond["rating"].startswith("AAA") else \
                            "Medium" if bond["rating"].startswith("AA") else "High"
        }
        
    async def _duration_agent_analysis(self, bond: Dict, performance: Dict) -> Dict[str, Any]:
        """Analyze duration and interest rate risk"""
        # Rate sensitivity
        rate_change_impact = self._calculate_rate_impact(
            performance["modified_duration"], 
            bond["convexity"],
            0.25  # 25 bps change
        )
        
        # Duration positioning
        target_duration = self._get_target_duration()
        duration_stance = "Reduce" if bond["duration"] > target_duration + 1 else \
                         "Increase" if bond["duration"] < target_duration - 1 else "Maintain"
        
        return {
            "macaulay_duration": f"{bond['duration']:.2f} years",
            "modified_duration": f"{performance['modified_duration']:.2f}",
            "convexity": f"{bond['convexity']:.1f}",
            "dv01": f"₹{performance['modified_duration'] * performance['current_price'] / 10000:.2f}",
            "rate_sensitivity": f"{rate_change_impact:.2f}% per 25bps",
            "rate_environment": self.market_conditions["rate_environment"],
            "target_duration": f"{target_duration:.1f} years",
            "duration_positioning": duration_stance,
            "hedge_recommendation": "Consider IRS" if bond["duration"] > 7 else "No hedge needed"
        }
        
    async def _yield_agent_analysis(self, bond: Dict, performance: Dict) -> Dict[str, Any]:
        """Analyze yield curve positioning and opportunities"""
        # Yield curve analysis
        curve_position = self._analyze_curve_position(bond)
        carry_roll = self._calculate_carry_and_roll(bond, performance)
        
        # Find yield opportunities
        better_yields = self._find_better_yields(bond)
        
        return {
            "yield_curve_position": curve_position,
            "curve_shape": self._get_curve_shape(),
            "carry": f"{carry_roll['carry']:.2f}%",
            "roll_down": f"{carry_roll['roll']:.2f}%",
            "total_return_potential": f"{carry_roll['total']:.2f}%",
            "reinvestment_risk": "High" if performance["days_to_maturity"] < 365 else \
                               "Medium" if performance["days_to_maturity"] < 730 else "Low",
            "yield_pickup_available": f"{better_yields['best_pickup']:.2f}%" if better_yields else "0%",
            "curve_strategy": self._recommend_curve_strategy(),
            "real_yield": f"{performance['current_yield'] - self.market_conditions['inflation_expectation']:.2f}%"
        }
        
    async def _build_bond_consensus(self, fi: Dict, credit: Dict, duration: Dict, yield_: Dict) -> Dict[str, Any]:
        """Build multi-agent consensus for bond action"""
        scores = []
        
        # Fixed income score
        fi_score = 0.8 if fi["value_assessment"] == "Undervalued" else \
                  0.6 if fi["value_assessment"] == "Fair" else 0.4
        scores.append(fi_score)
        
        # Credit score
        credit_score = 0.9 if credit["credit_rating"].startswith("AAA") else \
                      0.7 if credit["credit_rating"].startswith("AA") else 0.5
        if credit["downgrade_risk"] == "High":
            credit_score *= 0.8
        scores.append(credit_score)
        
        # Duration score
        duration_score = 0.8 if duration["duration_positioning"] == "Maintain" else 0.6
        if self.market_conditions["rate_environment"] == "rising" and float(duration["modified_duration"]) > 5:
            duration_score *= 0.7
        scores.append(duration_score)
        
        # Yield score
        yield_score = 0.7
        if float(yield_["total_return_potential"].replace("%", "")) > 8:
            yield_score = 0.9
        scores.append(yield_score)
        
        consensus_score = sum(scores) / len(scores)
        
        # Determine action
        if consensus_score > 0.75:
            action = "BUY"
            recommendation = "Attractive risk-reward with strong credit and yield"
        elif consensus_score > 0.6:
            action = "HOLD"
            recommendation = "Maintain position, monitor credit and rates"
        else:
            action = "SELL"
            recommendation = "Consider switching to better opportunities"
            
        return {
            "action": action,
            "confidence": f"{consensus_score * 100:.0f}%",
            "recommendation": recommendation,
            "key_risks": self._identify_key_risks(fi, credit, duration, yield_),
            "alternatives": await self._find_alternatives(action) if action == "SELL" else []
        }
        
    def _calculate_ytm(self, bond: Dict, current_price: float) -> float:
        """Calculate yield to maturity"""
        if not bond.get("maturity"):
            return bond["yield"]  # For perpetual bonds
            
        # Simplified YTM calculation
        years_to_maturity = (bond["maturity"] - datetime.now()).days / 365
        if years_to_maturity <= 0:
            return 0
            
        # Approximate YTM
        annual_coupon = bond["coupon"]
        ytm = (annual_coupon + (bond["face_value"] - current_price) / years_to_maturity) / \
              ((bond["face_value"] + current_price) / 2) * 100
        
        return ytm
        
    def _calculate_total_return(self, bond: Dict, performance: Dict) -> float:
        """Calculate total return including price change and coupon"""
        price_return = (performance["current_price"] - bond["price"]) / bond["price"] * 100
        coupon_return = bond["coupon"] * 0.5  # Assuming 6 months
        return price_return + coupon_return
        
    def _calculate_fair_value(self, bond: Dict) -> float:
        """Calculate theoretical fair value"""
        # Simplified DCF
        if not bond.get("maturity"):
            return bond["coupon"] / (bond["yield"] / 100)
            
        years_to_maturity = (bond["maturity"] - datetime.now()).days / 365
        fair_value = 0
        
        # Present value of coupons
        for year in range(1, int(years_to_maturity) + 1):
            fair_value += bond["coupon"] / ((1 + bond["yield"]/100) ** year)
            
        # Present value of principal
        fair_value += bond["face_value"] / ((1 + bond["yield"]/100) ** years_to_maturity)
        
        return fair_value
        
    def _get_liquidity_score(self, liquidity: str) -> int:
        """Convert liquidity to score"""
        return {"High": 9, "Medium": 6, "Low": 3}.get(liquidity, 5)
        
    def _calculate_default_probability(self, rating: str) -> float:
        """Estimate default probability based on rating"""
        default_probs = {
            "AAA": 0.01,
            "AA+": 0.03,
            "AA": 0.05,
            "AA-": 0.10,
            "A+": 0.20,
            "A": 0.35,
            "A-": 0.50
        }
        return default_probs.get(rating, 1.0)
        
    def _get_recovery_rate(self, bond_type: str) -> int:
        """Get expected recovery rate by bond type"""
        recovery_rates = {
            "Government": 100,
            "SDL": 95,
            "Corporate": 40,
            "Tax-Free": 60,
            "Perpetual": 35
        }
        return recovery_rates.get(bond_type, 40)
        
    def _assess_issuer_health(self, bond: Dict) -> str:
        """Assess issuer financial health"""
        if bond["type"] == "Government":
            return "Sovereign"
        elif bond["rating"].startswith("AAA"):
            return "Excellent"
        elif bond["rating"].startswith("AA"):
            return "Good"
        else:
            return "Fair"
            
    def _calculate_rate_impact(self, duration: float, convexity: float, rate_change: float) -> float:
        """Calculate price impact from rate change"""
        # Price change = -Duration * Rate Change + 0.5 * Convexity * (Rate Change)^2
        linear_impact = -duration * rate_change
        convexity_impact = 0.5 * convexity * (rate_change ** 2)
        return linear_impact + convexity_impact
        
    def _get_target_duration(self) -> float:
        """Get target duration based on rate environment"""
        if self.market_conditions["rate_environment"] == "rising":
            return 3.0
        elif self.market_conditions["rate_environment"] == "falling":
            return 7.0
        else:
            return 5.0
            
    def _analyze_curve_position(self, bond: Dict) -> str:
        """Analyze bond's position on yield curve"""
        if bond["duration"] < 2:
            return "Short end"
        elif bond["duration"] < 5:
            return "Belly"
        elif bond["duration"] < 10:
            return "Long end"
        else:
            return "Ultra-long"
            
    def _calculate_carry_and_roll(self, bond: Dict, performance: Dict) -> Dict[str, float]:
        """Calculate carry and roll-down return"""
        # Carry = Coupon - Funding Cost
        carry = bond["coupon"] - self.market_conditions["repo_rate"]
        
        # Roll-down = Price appreciation as bond rolls down the curve
        if performance["days_to_maturity"] > 365:
            roll = (100 - performance["current_price"]) / (performance["days_to_maturity"] / 365) * 0.5
        else:
            roll = 0
            
        return {
            "carry": carry,
            "roll": roll,
            "total": carry + roll
        }
        
    def _find_better_yields(self, bond: Dict) -> Dict[str, Any]:
        """Find bonds with better yields in similar credit/duration"""
        better_bonds = []
        
        for bond_id, other_bond in self.bonds.items():
            if (other_bond["rating"] == bond["rating"] and 
                abs(other_bond["duration"] - bond["duration"]) < 1 and
                other_bond["yield"] > bond["yield"]):
                better_bonds.append({
                    "bond_id": bond_id,
                    "yield_pickup": other_bond["yield"] - bond["yield"]
                })
                
        if better_bonds:
            best = max(better_bonds, key=lambda x: x["yield_pickup"])
            return {"best_pickup": best["yield_pickup"], "bond_id": best["bond_id"]}
        return None
        
    def _get_curve_shape(self) -> str:
        """Determine yield curve shape"""
        short_rate = self.yield_curve["1Y"]
        medium_rate = self.yield_curve["5Y"]
        long_rate = self.yield_curve["10Y"]
        
        if long_rate > medium_rate > short_rate:
            return "Normal"
        elif short_rate > medium_rate > long_rate:
            return "Inverted"
        else:
            return "Flat"
            
    def _recommend_curve_strategy(self) -> str:
        """Recommend yield curve strategy"""
        shape = self._get_curve_shape()
        
        if shape == "Normal":
            return "Ride the curve"
        elif shape == "Inverted":
            return "Stay short"
        else:
            return "Barbell strategy"
            
    def _identify_key_risks(self, fi: Dict, credit: Dict, duration: Dict, yield_: Dict) -> List[str]:
        """Identify main risks for the bond"""
        risks = []
        
        if self.market_conditions["rate_environment"] == "rising" and float(duration["modified_duration"]) > 5:
            risks.append("High duration risk")
            
        if credit["downgrade_risk"] != "Low":
            risks.append(f"{credit['downgrade_risk']} downgrade risk")
            
        if yield_["reinvestment_risk"] == "High":
            risks.append("High reinvestment risk")
            
        if fi["liquidity_score"] < 5:
            risks.append("Low liquidity")
            
        return risks
        
    async def _find_alternatives(self, action: str) -> List[Dict[str, Any]]:
        """Find alternative bonds"""
        alternatives = []
        
        for bond_id, bond in self.bonds.items():
            if bond["rating"].startswith("AA"):
                alternatives.append({
                    "bond_id": bond_id,
                    "name": bond["name"],
                    "yield": bond["yield"],
                    "rating": bond["rating"],
                    "duration": bond["duration"]
                })
                
        # Sort by yield
        alternatives.sort(key=lambda x: x["yield"], reverse=True)
        return alternatives[:3]
        
    async def construct_ladder(self, amount: float, strategy: str = "moderate") -> Dict[str, Any]:
        """Construct a bond ladder"""
        config = self.ladder_strategies[strategy]
        
        # Calculate allocation per rung
        allocation_per_rung = amount / config["rungs"]
        
        # Select bonds for ladder
        ladder_bonds = []
        target_maturities = []
        
        # Generate target maturities
        for i in range(config["rungs"]):
            if config["spacing"] == "equal":
                years = (i + 1) * config["max_maturity"] / config["rungs"]
            elif config["spacing"] == "barbell":
                # Concentrate on short and long ends
                if i < config["rungs"] // 2:
                    years = (i + 1) * 2
                else:
                    years = config["max_maturity"] - (config["rungs"] - i - 1) * 2
            else:  # bullet
                # Concentrate around middle
                years = config["max_maturity"] / 2 + (i - config["rungs"] // 2) * 0.5
                
            target_maturities.append(years)
            
        # Find bonds matching target maturities
        for target_years in target_maturities:
            best_match = None
            best_diff = float('inf')
            
            for bond_id, bond in self.bonds.items():
                if bond["rating"] in config["credit_quality"]:
                    if bond.get("maturity"):
                        years_to_maturity = (bond["maturity"] - datetime.now()).days / 365
                        diff = abs(years_to_maturity - target_years)
                        
                        if diff < best_diff:
                            best_diff = diff
                            best_match = {
                                "bond_id": bond_id,
                                "bond": bond,
                                "allocation": allocation_per_rung,
                                "units": int(allocation_per_rung / (bond["price"] * bond["min_investment"] / 100))
                            }
                            
            if best_match:
                ladder_bonds.append(best_match)
                
        # Calculate ladder metrics
        avg_yield = sum(b["bond"]["yield"] for b in ladder_bonds) / len(ladder_bonds)
        avg_duration = sum(b["bond"]["duration"] for b in ladder_bonds) / len(ladder_bonds)
        
        return {
            "strategy": strategy,
            "total_investment": amount,
            "rungs": len(ladder_bonds),
            "bonds": ladder_bonds,
            "average_yield": avg_yield,
            "average_duration": avg_duration,
            "annual_income": sum(b["allocation"] * b["bond"]["coupon"] / 100 for b in ladder_bonds),
            "maturity_schedule": self._generate_maturity_schedule(ladder_bonds)
        }
        
    def _generate_maturity_schedule(self, ladder_bonds: List[Dict]) -> List[Dict]:
        """Generate maturity schedule for ladder"""
        schedule = []
        
        for bond_data in ladder_bonds:
            bond = bond_data["bond"]
            if bond.get("maturity"):
                schedule.append({
                    "date": bond["maturity"].strftime("%Y-%m-%d"),
                    "bond_name": bond["name"],
                    "amount": bond_data["allocation"],
                    "reinvestment_needed": True
                })
                
        schedule.sort(key=lambda x: x["date"])
        return schedule
        
    async def manage_rollover(self, maturing_bond_id: str, amount: float) -> Dict[str, Any]:
        """Manage bond rollover"""
        maturing_bond = self.bonds.get(maturing_bond_id)
        if not maturing_bond:
            return None
            
        # Find replacement bond
        target_duration = maturing_bond["duration"]
        target_rating = maturing_bond["rating"]
        
        candidates = []
        for bond_id, bond in self.bonds.items():
            if (bond["rating"] == target_rating and 
                abs(bond["duration"] - target_duration) < 2 and
                bond_id != maturing_bond_id):
                candidates.append({
                    "bond_id": bond_id,
                    "bond": bond,
                    "yield_diff": bond["yield"] - maturing_bond["yield"]
                })
                
        if not candidates:
            return {"status": "No suitable replacement found"}
            
        # Select best replacement (highest yield)
        best_replacement = max(candidates, key=lambda x: x["bond"]["yield"])
        
        return {
            "status": "Rollover recommended",
            "maturing_bond": {
                "bond_id": maturing_bond_id,
                "name": maturing_bond["name"],
                "yield": maturing_bond["yield"]
            },
            "replacement_bond": {
                "bond_id": best_replacement["bond_id"],
                "name": best_replacement["bond"]["name"],
                "yield": best_replacement["bond"]["yield"],
                "yield_pickup": best_replacement["yield_diff"]
            },
            "action": "Execute rollover to maintain ladder structure"
        }
        
    def update_bond_prices(self):
        """Update bond prices based on yield movements"""
        # Simulate yield curve shifts
        curve_shift = random.uniform(-0.1, 0.1)  # ±10 bps
        
        for tenor, yield_val in self.yield_curve.items():
            self.yield_curve[tenor] = max(0, yield_val + curve_shift)
            
        # Update bond prices based on duration
        for bond_id, performance in self.bond_performance.items():
            bond = self.bonds[bond_id]
            
            # Price change from yield change
            yield_change = curve_shift
            price_change = -performance["modified_duration"] * yield_change
            
            # Add convexity adjustment
            price_change += 0.5 * bond["convexity"] * (yield_change ** 2)
            
            # Update price
            performance["current_price"] = max(50, min(120, performance["current_price"] * (1 + price_change / 100)))
            
            # Update yield
            performance["current_yield"] = bond["yield"] + yield_change
            
            # Update spread
            performance["spread_to_govt"] = self._calculate_spread(bond)
            
            # Accrue interest
            performance["accrued_interest"] += bond["coupon"] / 365
            
    def simulate_credit_event(self, bond_id: str, event_type: str):
        """Simulate a credit event"""
        event = {
            "bond_id": bond_id,
            "event_type": event_type,  # downgrade, default, upgrade
            "timestamp": datetime.now(),
            "impact": {
                "price_change": -5 if event_type == "downgrade" else -20 if event_type == "default" else 2,
                "spread_change": 50 if event_type == "downgrade" else 500 if event_type == "default" else -25
            }
        }
        
        self.credit_events.append(event)
        
        # Apply impact
        if bond_id in self.bond_performance:
            performance = self.bond_performance[bond_id]
            performance["current_price"] *= (1 + event["impact"]["price_change"] / 100)
            performance["current_yield"] += event["impact"]["spread_change"] / 100 