"""
Rule Engine - Rule-based fraud detection
"""
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import logging
from decimal import Decimal

from .models import (
    Transaction, FraudRule, RuleType, RuleAction,
    TransactionType
)


class RuleEngine:
    """
    Evaluates transactions against fraud detection rules
    """
    
    def __init__(self):
        self.logger = logging.getLogger("rule_engine")
        self.rules = {}  # rule_id -> FraudRule
        
    async def initialize(self):
        """Initialize rule engine"""
        self.logger.info("Initializing Rule Engine")
        
        # Create default rules
        await self._create_default_rules()
        
    async def _create_default_rules(self):
        """Create default fraud detection rules"""
        default_rules = [
            # Amount-based rules
            FraudRule(
                name="High Amount Transaction",
                description="Flag transactions over $10,000",
                rule_type=RuleType.AMOUNT_LIMIT,
                conditions={
                    "max_amount": 10000
                },
                action=RuleAction.FLAG,
                risk_score_impact=30,
                priority=5
            ),
            FraudRule(
                name="Unusual Amount",
                description="Flag round amounts over $5,000",
                rule_type=RuleType.AMOUNT_LIMIT,
                conditions={
                    "min_amount": 5000,
                    "round_amount": True
                },
                action=RuleAction.FLAG,
                risk_score_impact=20,
                priority=7
            ),
            
            # Velocity rules
            FraudRule(
                name="High Transaction Velocity",
                description="More than 5 transactions in 10 minutes",
                rule_type=RuleType.VELOCITY,
                conditions={
                    "time_window": 600,  # seconds
                    "max_count": 5
                },
                action=RuleAction.REVIEW,
                risk_score_impact=40,
                priority=3
            ),
            FraudRule(
                name="Daily Amount Limit",
                description="More than $20,000 in daily transactions",
                rule_type=RuleType.VELOCITY,
                conditions={
                    "time_window": 86400,  # 24 hours
                    "max_amount": 20000
                },
                action=RuleAction.BLOCK,
                risk_score_impact=50,
                priority=2
            ),
            
            # Location rules
            FraudRule(
                name="High Risk Country",
                description="Transaction from high-risk country",
                rule_type=RuleType.LOCATION,
                conditions={
                    "blocked_countries": ["XX", "YY", "ZZ"],
                    "action": "block"
                },
                action=RuleAction.BLOCK,
                risk_score_impact=80,
                priority=1
            ),
            FraudRule(
                name="Impossible Travel",
                description="Transaction from distant location too quickly",
                rule_type=RuleType.LOCATION,
                conditions={
                    "max_distance_km": 500,
                    "time_window": 3600  # 1 hour
                },
                action=RuleAction.FLAG,
                risk_score_impact=60,
                priority=2
            ),
            
            # Merchant rules
            FraudRule(
                name="First Time Merchant",
                description="First transaction with this merchant",
                rule_type=RuleType.MERCHANT,
                conditions={
                    "new_merchant": True,
                    "min_amount": 1000
                },
                action=RuleAction.REVIEW,
                risk_score_impact=15,
                priority=8
            ),
            FraudRule(
                name="High Risk Merchant Category",
                description="Transaction with high-risk merchant category",
                rule_type=RuleType.MERCHANT,
                conditions={
                    "risky_categories": ["gambling", "crypto", "adult"]
                },
                action=RuleAction.FLAG,
                risk_score_impact=25,
                priority=6
            ),
            
            # Time-based rules
            FraudRule(
                name="Unusual Time",
                description="Transaction at unusual time (2-5 AM local)",
                rule_type=RuleType.TIME_BASED,
                conditions={
                    "blocked_hours": [2, 3, 4, 5]
                },
                action=RuleAction.FLAG,
                risk_score_impact=10,
                priority=9
            ),
            
            # Device rules
            FraudRule(
                name="New Device",
                description="Transaction from unrecognized device",
                rule_type=RuleType.DEVICE,
                conditions={
                    "new_device": True,
                    "min_amount": 500
                },
                action=RuleAction.CHALLENGE,
                risk_score_impact=20,
                priority=7
            )
        ]
        
        for rule in default_rules:
            self.rules[rule.rule_id] = rule
            
    async def evaluate_transaction(
        self,
        transaction: Transaction
    ) -> Dict[str, Any]:
        """Evaluate transaction against all active rules"""
        triggered_rules = []
        total_risk_score = 0
        actions_required = set()
        
        # Evaluate each active rule
        for rule in self.rules.values():
            if not rule.is_active:
                continue
                
            if await self._evaluate_rule(rule, transaction):
                triggered_rules.append(rule)
                total_risk_score += rule.risk_score_impact
                actions_required.add(rule.action)
                
                self.logger.info(f"Rule triggered: {rule.name} for transaction {transaction.transaction_id}")
                
        # Cap risk score at 100
        total_risk_score = min(100, total_risk_score)
        
        # Determine primary action
        if RuleAction.BLOCK in actions_required:
            primary_action = RuleAction.BLOCK
        elif RuleAction.CHALLENGE in actions_required:
            primary_action = RuleAction.CHALLENGE
        elif RuleAction.REVIEW in actions_required:
            primary_action = RuleAction.REVIEW
        elif RuleAction.FLAG in actions_required:
            primary_action = RuleAction.FLAG
        else:
            primary_action = RuleAction.NOTIFY
            
        return {
            "triggered_rules": triggered_rules,
            "risk_score": total_risk_score,
            "primary_action": primary_action,
            "all_actions": list(actions_required)
        }
        
    async def _evaluate_rule(
        self,
        rule: FraudRule,
        transaction: Transaction
    ) -> bool:
        """Evaluate a single rule against transaction"""
        try:
            if rule.rule_type == RuleType.AMOUNT_LIMIT:
                return await self._evaluate_amount_rule(rule, transaction)
            elif rule.rule_type == RuleType.VELOCITY:
                return await self._evaluate_velocity_rule(rule, transaction)
            elif rule.rule_type == RuleType.LOCATION:
                return await self._evaluate_location_rule(rule, transaction)
            elif rule.rule_type == RuleType.MERCHANT:
                return await self._evaluate_merchant_rule(rule, transaction)
            elif rule.rule_type == RuleType.TIME_BASED:
                return await self._evaluate_time_rule(rule, transaction)
            elif rule.rule_type == RuleType.DEVICE:
                return await self._evaluate_device_rule(rule, transaction)
            else:
                return False
                
        except Exception as e:
            self.logger.error(f"Error evaluating rule {rule.name}: {str(e)}")
            return False
            
    async def _evaluate_amount_rule(
        self,
        rule: FraudRule,
        transaction: Transaction
    ) -> bool:
        """Evaluate amount-based rule"""
        conditions = rule.conditions
        
        # Check maximum amount
        if "max_amount" in conditions:
            if transaction.amount > Decimal(str(conditions["max_amount"])):
                return True
                
        # Check minimum amount
        if "min_amount" in conditions:
            if transaction.amount < Decimal(str(conditions["min_amount"])):
                return False
                
        # Check for round amounts
        if conditions.get("round_amount"):
            # Check if amount ends in 00
            if transaction.amount % 100 == 0:
                return True
                
        return False
        
    async def _evaluate_velocity_rule(
        self,
        rule: FraudRule,
        transaction: Transaction
    ) -> bool:
        """Evaluate velocity-based rule"""
        conditions = rule.conditions
        time_window = conditions["time_window"]
        
        # In production, would query transaction history
        # For now, simulate with random chance
        import random
        
        if "max_count" in conditions:
            # Simulate: 10% chance of triggering velocity rule
            if random.random() < 0.1:
                return True
                
        if "max_amount" in conditions:
            # Simulate: 5% chance of exceeding daily limit
            if random.random() < 0.05:
                return True
                
        return False
        
    async def _evaluate_location_rule(
        self,
        rule: FraudRule,
        transaction: Transaction
    ) -> bool:
        """Evaluate location-based rule"""
        conditions = rule.conditions
        
        # Check blocked countries
        if "blocked_countries" in conditions:
            if transaction.country in conditions["blocked_countries"]:
                return True
                
        # Check impossible travel
        if "max_distance_km" in conditions:
            # In production, would calculate distance from last transaction
            # For now, simulate
            import random
            if random.random() < 0.05:  # 5% chance
                return True
                
        return False
        
    async def _evaluate_merchant_rule(
        self,
        rule: FraudRule,
        transaction: Transaction
    ) -> bool:
        """Evaluate merchant-based rule"""
        conditions = rule.conditions
        
        # Check new merchant
        if conditions.get("new_merchant"):
            # In production, would check transaction history
            # Simulate: 20% chance of new merchant
            import random
            if random.random() < 0.2:
                min_amount = conditions.get("min_amount", 0)
                if transaction.amount >= Decimal(str(min_amount)):
                    return True
                    
        # Check risky categories
        if "risky_categories" in conditions:
            if transaction.merchant_category:
                for category in conditions["risky_categories"]:
                    if category.lower() in transaction.merchant_category.lower():
                        return True
                        
        return False
        
    async def _evaluate_time_rule(
        self,
        rule: FraudRule,
        transaction: Transaction
    ) -> bool:
        """Evaluate time-based rule"""
        conditions = rule.conditions
        
        # Check blocked hours
        if "blocked_hours" in conditions:
            current_hour = transaction.initiated_at.hour
            if current_hour in conditions["blocked_hours"]:
                return True
                
        return False
        
    async def _evaluate_device_rule(
        self,
        rule: FraudRule,
        transaction: Transaction
    ) -> bool:
        """Evaluate device-based rule"""
        conditions = rule.conditions
        
        # Check new device
        if conditions.get("new_device"):
            # In production, would check device history
            # Simulate: 15% chance of new device
            import random
            if random.random() < 0.15:
                min_amount = conditions.get("min_amount", 0)
                if transaction.amount >= Decimal(str(min_amount)):
                    return True
                    
        return False
        
    async def get_rules(
        self,
        rule_type: Optional[RuleType] = None,
        active_only: bool = True
    ) -> List[FraudRule]:
        """Get fraud detection rules"""
        rules = list(self.rules.values())
        
        # Apply filters
        if rule_type:
            rules = [r for r in rules if r.rule_type == rule_type]
        if active_only:
            rules = [r for r in rules if r.is_active]
            
        # Sort by priority
        rules.sort(key=lambda r: r.priority)
        
        return rules
        
    async def create_rule(self, rule: FraudRule) -> FraudRule:
        """Create a new rule"""
        self.rules[rule.rule_id] = rule
        
        self.logger.info(f"Created rule: {rule.name}")
        
        return rule
        
    async def update_rule(
        self,
        rule_id: str,
        updates: Dict[str, Any]
    ) -> bool:
        """Update an existing rule"""
        rule = self.rules.get(rule_id)
        
        if not rule:
            return False
            
        # Update allowed fields
        allowed_fields = ["description", "conditions", "action", "risk_score_impact", "priority", "is_active"]
        
        for field, value in updates.items():
            if field in allowed_fields:
                setattr(rule, field, value)
                
        rule.updated_at = datetime.now()
        
        self.logger.info(f"Updated rule: {rule.name}")
        
        return True
        
    async def delete_rule(self, rule_id: str) -> bool:
        """Delete a rule"""
        if rule_id in self.rules:
            rule = self.rules[rule_id]
            self.logger.info(f"Deleted rule: {rule.name}")
            del self.rules[rule_id]
            return True
            
        return False
        
    async def get_active_rule_count(self) -> int:
        """Get count of active rules"""
        return sum(1 for r in self.rules.values() if r.is_active)
        
    async def evaluate_rule_effectiveness(self):
        """Evaluate effectiveness of rules"""
        # In production, this would:
        # - Track true/false positives for each rule
        # - Calculate precision and recall
        # - Adjust rule parameters
        # - Disable ineffective rules
        
        for rule in self.rules.values():
            total = rule.true_positive_count + rule.false_positive_count
            
            if total > 0:
                rule.effectiveness_score = rule.true_positive_count / total
            else:
                rule.effectiveness_score = 0.0
                
            # Disable rules with very low effectiveness
            if total > 100 and rule.effectiveness_score < 0.1:
                rule.is_active = False
                self.logger.warning(f"Disabled ineffective rule: {rule.name}")
                
    async def test_rule(
        self,
        rule: FraudRule,
        transaction: Transaction
    ) -> bool:
        """Test a rule against a transaction without side effects"""
        return await self._evaluate_rule(rule, transaction) 