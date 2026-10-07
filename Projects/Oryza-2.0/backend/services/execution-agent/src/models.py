"""
Data models for Execution Agent Service
"""
from pydantic import BaseModel, Field, validator
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from decimal import Decimal
from enum import Enum
import uuid


class OrderSide(str, Enum):
    BUY = "BUY"
    SELL = "SELL"


class OrderType(str, Enum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP = "STOP"
    STOP_LIMIT = "STOP_LIMIT"
    TRAILING_STOP = "TRAILING_STOP"


class OrderStatus(str, Enum):
    PENDING = "pending"
    SUBMITTED = "submitted"
    ACCEPTED = "accepted"
    PARTIALLY_FILLED = "partially_filled"
    FILLED = "filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"
    EXPIRED = "expired"
    FAILED = "failed"


class TimeInForce(str, Enum):
    DAY = "DAY"  # Valid for the day
    GTC = "GTC"  # Good Till Cancelled
    IOC = "IOC"  # Immediate or Cancel
    FOK = "FOK"  # Fill or Kill
    GTD = "GTD"  # Good Till Date
    MOC = "MOC"  # Market on Close
    MOO = "MOO"  # Market on Open


class ExecutionType(str, Enum):
    NEW = "NEW"
    PARTIAL_FILL = "PARTIAL_FILL"
    FILL = "FILL"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"
    REPLACED = "REPLACED"
    EXPIRED = "EXPIRED"


class SettlementStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class BrokerStatus(str, Enum):
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    RECONNECTING = "reconnecting"
    ERROR = "error"
    MAINTENANCE = "maintenance"


class OrderRequest(BaseModel):
    """Request to place an order"""
    symbol: str
    side: OrderSide
    order_type: OrderType
    quantity: Decimal = Field(gt=0)
    
    # Price fields
    price: Optional[Decimal] = Field(None, gt=0)
    stop_price: Optional[Decimal] = Field(None, gt=0)
    
    # Order parameters
    time_in_force: TimeInForce = TimeInForce.DAY
    expire_time: Optional[datetime] = None
    
    # Broker selection
    broker: Optional[str] = None  # If None, use smart routing
    
    # Additional parameters
    metadata: Optional[Dict[str, Any]] = None
    
    @validator('price')
    def validate_limit_price(cls, v, values):
        if values.get('order_type') in [OrderType.LIMIT, OrderType.STOP_LIMIT] and v is None:
            raise ValueError("Limit price required for limit orders")
        return v
        
    @validator('stop_price')
    def validate_stop_price(cls, v, values):
        if values.get('order_type') in [OrderType.STOP, OrderType.STOP_LIMIT] and v is None:
            raise ValueError("Stop price required for stop orders")
        return v


class Order(BaseModel):
    """Internal order representation"""
    order_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    
    # Order details
    symbol: str
    side: OrderSide
    order_type: OrderType
    quantity: Decimal
    filled_quantity: Decimal = Decimal("0")
    remaining_quantity: Decimal = Decimal("0")
    
    # Prices
    price: Optional[Decimal] = None
    stop_price: Optional[Decimal] = None
    avg_fill_price: Optional[Decimal] = None
    
    # Status
    status: OrderStatus = OrderStatus.PENDING
    
    # Time
    time_in_force: TimeInForce = TimeInForce.DAY
    expire_time: Optional[datetime] = None
    
    # Broker
    broker: Optional[str] = None
    broker_order_id: Optional[str] = None
    
    # Tracking
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    submitted_at: Optional[datetime] = None
    filled_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None
    
    # Metadata
    metadata: Optional[Dict[str, Any]] = None
    
    # Fees
    commission: Decimal = Decimal("0")
    fees: Decimal = Decimal("0")
    
    def update_fill(self, fill_quantity: Decimal, fill_price: Decimal):
        """Update order with partial or complete fill"""
        # Update quantities
        self.filled_quantity += fill_quantity
        self.remaining_quantity = self.quantity - self.filled_quantity
        
        # Update average price
        if self.avg_fill_price is None:
            self.avg_fill_price = fill_price
        else:
            total_value = (self.avg_fill_price * (self.filled_quantity - fill_quantity) + 
                          fill_price * fill_quantity)
            self.avg_fill_price = total_value / self.filled_quantity
            
        # Update status
        if self.remaining_quantity == 0:
            self.status = OrderStatus.FILLED
            self.filled_at = datetime.now()
        else:
            self.status = OrderStatus.PARTIALLY_FILLED
            
        self.updated_at = datetime.now()


class OrderResponse(BaseModel):
    """Response after placing an order"""
    order_id: str
    status: OrderStatus
    created_at: datetime
    
    # Echo request details
    symbol: str
    side: OrderSide
    order_type: OrderType
    quantity: Decimal
    price: Optional[Decimal] = None
    
    # Additional info
    message: Optional[str] = None


class ExecutionReport(BaseModel):
    """Trade execution report"""
    execution_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    order_id: str
    
    # Execution details
    exec_type: ExecutionType
    symbol: str
    side: OrderSide
    
    # Quantities
    last_quantity: Decimal = Decimal("0")  # This fill quantity
    cumulative_quantity: Decimal = Decimal("0")  # Total filled
    leaves_quantity: Decimal = Decimal("0")  # Remaining
    
    # Prices
    last_price: Optional[Decimal] = None  # This fill price
    avg_price: Optional[Decimal] = None  # Average fill price
    
    # Status
    order_status: OrderStatus
    
    # Broker info
    broker: str
    broker_exec_id: Optional[str] = None
    
    # Timestamps
    transact_time: datetime = Field(default_factory=datetime.now)
    
    # Additional
    text: Optional[str] = None  # Rejection reason or info
    commission: Decimal = Decimal("0")
    
    # Trade details (if filled)
    trade_id: Optional[str] = None
    liquidity_indicator: Optional[str] = None  # Added/Removed liquidity


class Position(BaseModel):
    """Current position in an asset"""
    position_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    
    # Asset
    symbol: str
    
    # Quantities
    quantity: Decimal
    available_quantity: Decimal  # Available to sell
    
    # Values
    avg_cost: Decimal
    market_price: Decimal
    market_value: Decimal
    
    # P&L
    unrealized_pnl: Decimal
    unrealized_pnl_percent: Decimal
    realized_pnl: Decimal = Decimal("0")
    
    # Broker
    broker: str
    account_id: str
    
    # Timestamps
    opened_at: datetime
    updated_at: datetime = Field(default_factory=datetime.now)
    
    @property
    def total_pnl(self) -> Decimal:
        return self.unrealized_pnl + self.realized_pnl


class PositionUpdate(BaseModel):
    """Position update event"""
    position_id: str
    symbol: str
    
    # Changes
    quantity_change: Decimal
    realized_pnl: Decimal = Decimal("0")
    
    # New values
    new_quantity: Decimal
    new_avg_cost: Decimal
    
    # Event info
    event_type: str  # "trade", "dividend", "split", etc.
    event_id: Optional[str] = None
    
    # Timestamp
    timestamp: datetime = Field(default_factory=datetime.now)


class MarketData(BaseModel):
    """Real-time market data"""
    symbol: str
    
    # Prices
    bid: Optional[Decimal] = None
    ask: Optional[Decimal] = None
    last: Optional[Decimal] = None
    open: Optional[Decimal] = None
    high: Optional[Decimal] = None
    low: Optional[Decimal] = None
    close: Optional[Decimal] = None
    prev_close: Optional[Decimal] = None
    
    # Volume
    volume: Optional[int] = None
    bid_size: Optional[int] = None
    ask_size: Optional[int] = None
    
    # Change
    change: Optional[Decimal] = None
    change_percent: Optional[Decimal] = None
    
    # Time
    timestamp: datetime = Field(default_factory=datetime.now)
    market_time: Optional[datetime] = None
    
    # Status
    halted: bool = False
    tradeable: bool = True


class OrderBook(BaseModel):
    """Order book depth"""
    symbol: str
    
    # Bids (buy orders)
    bids: List[Dict[str, Union[Decimal, int]]] = []  # [{"price": x, "size": y}]
    
    # Asks (sell orders)
    asks: List[Dict[str, Union[Decimal, int]]] = []  # [{"price": x, "size": y}]
    
    # Spread
    spread: Optional[Decimal] = None
    spread_percent: Optional[Decimal] = None
    
    # Timestamp
    timestamp: datetime = Field(default_factory=datetime.now)


class Trade(BaseModel):
    """Executed trade"""
    trade_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    order_id: str
    execution_id: str
    
    # Trade details
    symbol: str
    side: OrderSide
    quantity: Decimal
    price: Decimal
    
    # Fees
    commission: Decimal = Decimal("0")
    fees: Decimal = Decimal("0")
    net_amount: Decimal
    
    # Settlement
    settlement_date: datetime
    settlement_status: SettlementStatus = SettlementStatus.PENDING
    
    # Broker
    broker: str
    broker_trade_id: Optional[str] = None
    
    # Timestamps
    executed_at: datetime
    created_at: datetime = Field(default_factory=datetime.now)


class Settlement(BaseModel):
    """Trade settlement record"""
    settlement_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    trade_id: str
    user_id: str
    
    # Settlement details
    symbol: str
    side: OrderSide
    quantity: Decimal
    amount: Decimal
    
    # Status
    status: SettlementStatus = SettlementStatus.PENDING
    
    # Dates
    trade_date: datetime
    settlement_date: datetime
    completed_at: Optional[datetime] = None
    
    # Broker
    broker: str
    broker_reference: Optional[str] = None
    
    # Error handling
    error_message: Optional[str] = None
    retry_count: int = 0


class BrokerAccount(BaseModel):
    """Broker account connection"""
    account_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    
    # Broker info
    broker_id: str
    broker_account_id: str
    account_type: str  # "cash", "margin", etc.
    
    # Status
    status: BrokerStatus = BrokerStatus.DISCONNECTED
    is_active: bool = True
    
    # Capabilities
    can_trade_stocks: bool = True
    can_trade_options: bool = False
    can_trade_crypto: bool = False
    can_short: bool = False
    
    # Balances (cached)
    cash_balance: Optional[Decimal] = None
    buying_power: Optional[Decimal] = None
    
    # Timestamps
    connected_at: Optional[datetime] = None
    last_sync: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.now)
    
    # Encrypted credentials
    encrypted_credentials: Optional[str] = None


class RiskCheck(BaseModel):
    """Risk validation check"""
    check_type: str  # "position_size", "buying_power", etc.
    passed: bool
    message: str
    
    # Details
    current_value: Optional[Decimal] = None
    limit_value: Optional[Decimal] = None
    
    # Severity
    severity: str = "info"  # "info", "warning", "error"


class RiskValidation(BaseModel):
    """Complete risk validation result"""
    order_id: Optional[str] = None
    user_id: str
    
    # Overall result
    passed: bool
    can_override: bool = False
    
    # Individual checks
    checks: List[RiskCheck] = []
    
    # Summary
    risk_score: float = Field(ge=0, le=100)
    reason: Optional[str] = None
    
    # Recommendations
    recommendations: List[str] = []
    
    # Timestamp
    validated_at: datetime = Field(default_factory=datetime.now)


class BrokerConfig(BaseModel):
    """Broker configuration"""
    broker_id: str
    name: str
    display_name: str
    
    # Capabilities
    supported_order_types: List[OrderType]
    supported_time_in_force: List[TimeInForce]
    supported_asset_classes: List[str]
    
    # Limits
    min_order_size: Decimal
    max_order_size: Optional[Decimal] = None
    
    # Features
    supports_fractional: bool = False
    supports_crypto: bool = False
    supports_options: bool = False
    supports_international: bool = False
    
    # API info
    api_type: str  # "REST", "FIX", "WebSocket"
    requires_oauth: bool = False
    
    # Status
    is_active: bool = True
    maintenance_mode: bool = False


class OrderRoutingDecision(BaseModel):
    """Smart order routing decision"""
    order_id: str
    
    # Decision
    selected_broker: str
    routing_reason: str
    
    # Scoring
    broker_scores: Dict[str, float] = {}
    
    # Factors considered
    factors: Dict[str, Any] = {
        "price_improvement": None,
        "execution_speed": None,
        "liquidity": None,
        "fees": None
    }
    
    # Timestamp
    decided_at: datetime = Field(default_factory=datetime.now)
