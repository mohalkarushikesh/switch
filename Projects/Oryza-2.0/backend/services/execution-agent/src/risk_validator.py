"""
Risk Validator - Validates orders against risk rules
"""
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import logging
from decimal import Decimal

from .models import (
    Order, OrderSide, RiskCheck, RiskValidation
)


class RiskValidator:
    """
    Validates orders against various risk rules
    """
    
    def __init__(self):
        self.logger = logging.getLogger("risk_validator")
        self.risk_rules = self._initialize_rules()
        self.user_limits = {}  # user_id -> limits
        self.daily_volumes = {}  # user_id -> {symbol -> volume}
        
    async def initialize(self):
        """Initialize risk validator"""
        self.logger.info("Initializing Risk Validator")
        # In production, load risk rules from database
        
    def _initialize_rules(self) -> Dict[str, Any]:
        """Initialize default risk rules"""
        return {
            "max_order_value": Decimal("50000"),  # Max single order value
            "max_position_concentration": Decimal("0.25"),  # Max 25% in one position
            "max_daily_trades": 50,  # Max trades per day
            "max_daily_volume": Decimal("500000"),  # Max daily trading volume
            "min_account_equity": Decimal("2000"),  # Min account value
            "restricted_symbols": ["BRK.A"],  # Restricted symbols
            "pattern_day_trader_min": Decimal("25000"),  # PDT rule
            "max_loss_per_day": Decimal("0.05"),  # Max 5% daily loss
            "max_leverage": Decimal("2.0"),  # Max 2x leverage
        }
        
    async def validate_order(self, order: Order, user: Any) -> RiskValidation:
        """Validate an order against risk rules"""
        checks = []
        passed = True
        risk_score = 0.0
        
        # Run all checks
        checks.extend(await self._check_order_size(order, user))
        checks.extend(await self._check_buying_power(order, user))
        checks.extend(await self._check_position_concentration(order, user))
        checks.extend(await self._check_daily_limits(order, user))
        checks.extend(await self._check_restricted_symbols(order))
        checks.extend(await self._check_pattern_day_trader(order, user))
        checks.extend(await self._check_market_conditions(order))
        
        # Calculate overall result
        failed_checks = [c for c in checks if not c.passed]
        warning_checks = [c for c in checks if c.severity == "warning"]
        
        if any(c.severity == "error" for c in failed_checks):
            passed = False
            
        # Calculate risk score (0-100)
        if checks:
            passed_weight = sum(1 for c in checks if c.passed) / len(checks)
            warning_penalty = len(warning_checks) * 0.1
            risk_score = max(0, min(100, (1 - passed_weight + warning_penalty) * 100))
            
        # Generate reason if failed
        reason = None
        if not passed:
            error_messages = [c.message for c in failed_checks if c.severity == "error"]
            reason = "; ".join(error_messages[:2])  # Top 2 errors
            
        # Generate recommendations
        recommendations = self._generate_recommendations(checks, order)
        
        return RiskValidation(
            order_id=order.order_id,
            user_id=order.user_id,
            passed=passed,
            can_override=all(c.severity != "error" for c in failed_checks),
            checks=checks,
            risk_score=risk_score,
            reason=reason,
            recommendations=recommendations
        )
        
    async def _check_order_size(self, order: Order, user: Any) -> List[RiskCheck]:
        """Check order size limits"""
        checks = []
        
        # Calculate order value
        if order.price:
            order_value = order.quantity * order.price
        else:
            # For market orders, estimate using current price
            order_value = order.quantity * Decimal("100")  # Mock price
            
        # Check max order value
        max_value = self.risk_rules["max_order_value"]
        
        checks.append(RiskCheck(
            check_type="max_order_value",
            passed=order_value <= max_value,
            message=f"Order value ${order_value:.2f} exceeds maximum ${max_value:.2f}" 
                   if order_value > max_value else "Order size within limits",
            current_value=order_value,
            limit_value=max_value,
            severity="error" if order_value > max_value else "info"
        ))
        
        # Check minimum order size
        min_value = Decimal("1")  # $1 minimum
        
        if order_value < min_value:
            checks.append(RiskCheck(
                check_type="min_order_value",
                passed=False,
                message=f"Order value ${order_value:.2f} below minimum ${min_value:.2f}",
                current_value=order_value,
                limit_value=min_value,
                severity="error"
            ))
            
        return checks
        
    async def _check_buying_power(self, order: Order, user: Any) -> List[RiskCheck]:
        """Check if user has sufficient buying power"""
        checks = []
        
        # Get user's buying power (mock)
        buying_power = Decimal("10000")  # In production, fetch from broker
        
        # Calculate required buying power
        if order.price:
            required = order.quantity * order.price
        else:
            required = order.quantity * Decimal("100")  # Mock price
            
        if order.side == OrderSide.BUY:
            checks.append(RiskCheck(
                check_type="buying_power",
                passed=required <= buying_power,
                message=f"Insufficient buying power: need ${required:.2f}, have ${buying_power:.2f}"
                       if required > buying_power else "Sufficient buying power",
                current_value=buying_power,
                limit_value=required,
                severity="error" if required > buying_power else "info"
            ))
            
        return checks
        
    async def _check_position_concentration(self, order: Order, user: Any) -> List[RiskCheck]:
        """Check position concentration limits"""
        checks = []
        
        if order.side == OrderSide.BUY:
            # Get current positions (mock)
            total_portfolio_value = Decimal("50000")
            current_position_value = Decimal("5000")  # Current position in symbol
            
            # Calculate new position value
            if order.price:
                order_value = order.quantity * order.price
            else:
                order_value = order.quantity * Decimal("100")
                
            new_position_value = current_position_value + order_value
            concentration = new_position_value / total_portfolio_value
            
            max_concentration = self.risk_rules["max_position_concentration"]
            
            checks.append(RiskCheck(
                check_type="position_concentration",
                passed=concentration <= max_concentration,
                message=f"Position would be {concentration:.1%} of portfolio, exceeds {max_concentration:.1%} limit"
                       if concentration > max_concentration else "Position concentration within limits",
                current_value=concentration,
                limit_value=max_concentration,
                severity="warning" if concentration > max_concentration * 0.8 else "info"
            ))
            
        return checks
        
    async def _check_daily_limits(self, order: Order, user: Any) -> List[RiskCheck]:
        """Check daily trading limits"""
        checks = []
        
        user_id = order.user_id
        today = datetime.now().date()
        
        # Initialize daily tracking if needed
        if user_id not in self.daily_volumes:
            self.daily_volumes[user_id] = {}
            
        # Get today's trades (mock)
        daily_trade_count = 10  # In production, query database
        max_trades = self.risk_rules["max_daily_trades"]
        
        checks.append(RiskCheck(
            check_type="daily_trade_count",
            passed=daily_trade_count < max_trades,
            message=f"Daily trade limit reached: {daily_trade_count}/{max_trades}"
                   if daily_trade_count >= max_trades else f"Daily trades: {daily_trade_count}/{max_trades}",
            current_value=Decimal(daily_trade_count),
            limit_value=Decimal(max_trades),
            severity="error" if daily_trade_count >= max_trades else "info"
        ))
        
        # Check daily volume
        if order.price:
            order_value = order.quantity * order.price
        else:
            order_value = order.quantity * Decimal("100")
            
        daily_volume = Decimal("100000")  # Mock current daily volume
        new_daily_volume = daily_volume + order_value
        max_volume = self.risk_rules["max_daily_volume"]
        
        checks.append(RiskCheck(
            check_type="daily_volume",
            passed=new_daily_volume <= max_volume,
            message=f"Daily volume would exceed limit: ${new_daily_volume:.2f} > ${max_volume:.2f}"
                   if new_daily_volume > max_volume else "Daily volume within limits",
            current_value=new_daily_volume,
            limit_value=max_volume,
            severity="warning" if new_daily_volume > max_volume * 0.8 else "info"
        ))
        
        return checks
        
    async def _check_restricted_symbols(self, order: Order) -> List[RiskCheck]:
        """Check if symbol is restricted"""
        checks = []
        
        restricted = self.risk_rules["restricted_symbols"]
        
        if order.symbol in restricted:
            checks.append(RiskCheck(
                check_type="restricted_symbol",
                passed=False,
                message=f"Symbol {order.symbol} is restricted for trading",
                severity="error"
            ))
        else:
            checks.append(RiskCheck(
                check_type="restricted_symbol",
                passed=True,
                message="Symbol is allowed for trading",
                severity="info"
            ))
            
        return checks
        
    async def _check_pattern_day_trader(self, order: Order, user: Any) -> List[RiskCheck]:
        """Check pattern day trader rules"""
        checks = []
        
        # Check if user is flagged as PDT (mock)
        is_pdt = False  # In production, check user flags
        account_value = Decimal("30000")  # Mock account value
        
        if is_pdt:
            min_equity = self.risk_rules["pattern_day_trader_min"]
            
            checks.append(RiskCheck(
                check_type="pattern_day_trader",
                passed=account_value >= min_equity,
                message=f"PDT account requires ${min_equity:.2f} minimum equity, current: ${account_value:.2f}"
                       if account_value < min_equity else "PDT requirements met",
                current_value=account_value,
                limit_value=min_equity,
                severity="error" if account_value < min_equity else "info"
            ))
            
        # Check day trade count
        day_trade_count = 2  # Mock day trades in 5 days
        
        if day_trade_count >= 4 and account_value < self.risk_rules["pattern_day_trader_min"]:
            checks.append(RiskCheck(
                check_type="day_trade_warning",
                passed=True,  # Warning only
                message=f"Warning: {day_trade_count} day trades in 5 days. One more will trigger PDT rules.",
                current_value=Decimal(day_trade_count),
                limit_value=Decimal(4),
                severity="warning"
            ))
            
        return checks
        
    async def _check_market_conditions(self, order: Order) -> List[RiskCheck]:
        """Check market conditions"""
        checks = []
        
        # Check if market is halted (mock)
        is_halted = False  # In production, check with market data
        
        if is_halted:
            checks.append(RiskCheck(
                check_type="market_halted",
                passed=False,
                message=f"Trading halted for {order.symbol}",
                severity="error"
            ))
            
        # Check volatility (mock)
        volatility = Decimal("0.02")  # 2% volatility
        high_volatility_threshold = Decimal("0.05")  # 5%
        
        if volatility > high_volatility_threshold:
            checks.append(RiskCheck(
                check_type="high_volatility",
                passed=True,  # Warning only
                message=f"High volatility detected: {volatility:.1%}",
                current_value=volatility,
                limit_value=high_volatility_threshold,
                severity="warning"
            ))
            
        return checks
        
    def _generate_recommendations(
        self,
        checks: List[RiskCheck],
        order: Order
    ) -> List[str]:
        """Generate recommendations based on risk checks"""
        recommendations = []
        
        # Check for concentration warning
        concentration_check = next(
            (c for c in checks if c.check_type == "position_concentration" and not c.passed),
            None
        )
        if concentration_check:
            recommendations.append(
                "Consider diversifying your portfolio to reduce concentration risk"
            )
            
        # Check for PDT warning
        pdt_warning = next(
            (c for c in checks if c.check_type == "day_trade_warning"),
            None
        )
        if pdt_warning:
            recommendations.append(
                "Consider holding positions overnight to avoid PDT classification"
            )
            
        # Check for high volatility
        volatility_check = next(
            (c for c in checks if c.check_type == "high_volatility"),
            None
        )
        if volatility_check:
            recommendations.append(
                "Consider using limit orders instead of market orders in volatile conditions"
            )
            
        # Check buying power
        buying_power_check = next(
            (c for c in checks if c.check_type == "buying_power" and not c.passed),
            None
        )
        if buying_power_check:
            recommendations.append(
                "Reduce order size or deposit additional funds"
            )
            
        return recommendations
        
    async def update_user_limits(self, user_id: str, limits: Dict[str, Any]):
        """Update user-specific risk limits"""
        self.user_limits[user_id] = limits
        self.logger.info(f"Updated risk limits for user {user_id}")
        
    async def get_user_risk_profile(self, user_id: str) -> Dict[str, Any]:
        """Get user's current risk profile"""
        # In production, aggregate from database
        
        return {
            "risk_score": 25.0,
            "daily_trades_used": 10,
            "daily_volume_used": Decimal("100000"),
            "largest_position_concentration": Decimal("0.15"),
            "current_leverage": Decimal("1.0"),
            "pdt_flag": False,
            "restrictions": [],
            "warnings": [
                "Approaching daily trade limit"
            ]
        } 